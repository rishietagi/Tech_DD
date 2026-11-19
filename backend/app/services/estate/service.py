"""Persistence and assembly for the four estate assessments.

Applications, data & infrastructure (`data_tech`), team & governance and strategy &
projects share one lifecycle, the business-process assessment's: answers are working notes
(one current set, not versioned); scores are versioned; consultant edits to gaps are an
overlay applied at read time so a re-score never discards them.

Every assessment has one questionnaire answered once per engagement — the subject
`estate` — and optionally one set of questions per inventory item.
"""

import logging
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.estate import EstateAnswer, EstateAssessment, EstateGapNote, InventoryItem
from app.schemas.estate import (
    ESTATE_SUBJECT,
    SCORE_SCHEMA_VERSION,
    AnswerOption,
    ApplicationsScorePayload,
    DataTechScorePayload,
    EstateAnswerRead,
    EstateAnswerWrite,
    EstateDomain,
    EstateQuestion,
    EstateRead,
    EstateScoreRead,
    EstateSubject,
    Gap,
    GapNoteWrite,
    StrategyProjectsScorePayload,
    TeamGovernanceScorePayload,
)
from app.services.assess.service import find_latest_score
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.estate import applications as app_rules
from app.services.estate import data_tech as dt_rules
from app.services.estate import judgement
from app.services.estate import strategy_projects as sp_rules
from app.services.estate import team_governance as tg_rules
from app.services.estate.gaps import count, overlay
from app.services.estate.inventory import items_of, process_refs
from app.services.estate.library import (
    get_applications_config,
    get_data_tech_config,
    get_strategy_projects_config,
    get_team_governance_config,
)
from app.services.estate.llm import EstateSummariser, rules_summary
from app.services.intelligence.mode import use_llm

logger = logging.getLogger(__name__)

DOMAINS: tuple[EstateDomain, ...] = ("applications", "data_tech", "team_governance", "strategy_projects")
DOMAIN_NAMES = {
    "applications": "applications",
    "data_tech": "data & infrastructure",
    "team_governance": "team & governance",
    "strategy_projects": "strategy & projects",
}
SUBJECT_KINDS: dict[str, tuple[str, ...]] = {
    "applications": ("application",),
    "data_tech": ("data_domain", "platform"),
    "team_governance": (),
    "strategy_projects": ("it_project",),
}
QUESTIONNAIRE = {
    "applications": ("Portfolio questions", "The application landscape as a whole"),
    "data_tech": ("Estate checks", "Resilience, engineering practice, cyber security"),
    "team_governance": ("Team & governance", "Leadership, governance, capacity and people risk"),
    "strategy_projects": ("Strategy & portfolio", "IT strategy, portfolio governance and AI"),
}
CHECK_LABELS = {
    "pass": "Pass — in place and evidenced",
    "partial": "Partial — partly in place",
    "fail": "Fail — not in place",
    "unknown": "Unknown — not yet established",
}
AI_MATERIAL = {"Embedded in the product", "Core to the value proposition"}


def _domain(domain: str) -> EstateDomain:
    if domain not in DOMAINS:
        raise AppError(
            code="unknown_domain",
            message=f"{domain!r} is not an estate assessment. Use one of: {', '.join(DOMAINS)}.",
            status_code=404,
        )
    return domain  # type: ignore[return-value]


# ------------------------------------------------------------------ context


def assess_context(db: Session, engagement_id: str) -> judgement.AssessContext:
    """Which variant of the questionnaires this deal sees.

    The DD type is the scope's classification once a scope exists, else the intake's
    declared preference; AI is material when the intake says it is embedded in or core to
    the product — the condition of scope rule A11.
    """
    from app.services.scope import service as scope_service  # local: scope imports widely

    engagement = get_engagement(db, engagement_id)
    intake = assemble_intake_full(engagement)
    dd_type = ""
    try:
        scope = scope_service.get_latest_scope(db, engagement_id)
        dd_type = str((scope.payload_json.get("classification") or {}).get("dd_type") or "")
    except AppError:
        dd_type = ""
    if dd_type not in ("enterprise", "product", "blended"):
        preference = getattr(intake.objectives, "dd_type_preference", None)
        value = str(getattr(preference, "value", preference) or "").lower()
        dd_type = next((t for t in ("enterprise", "product", "blended") if t in value), "enterprise")
    ai = getattr(intake.technology, "ai_ml_dependence", None)
    ai_value = str(getattr(ai, "value", ai) or "")
    return judgement.AssessContext(dd_type=dd_type, ai_material=ai_value in AI_MATERIAL)


# ------------------------------------------------------------------ questions


def _scale_options(levels: dict[int, str]) -> list[AnswerOption]:
    return [AnswerOption(value=str(level), label=f"{level} — {text}") for level, text in sorted(levels.items())]


def question_sets(domain: EstateDomain, context: judgement.AssessContext) -> dict[str, list[EstateQuestion]]:
    if domain == "applications":
        config = get_applications_config()
        return {
            "application": [
                EstateQuestion(id=q.id, text=q.text, help=q.help, group=q.group, options=_scale_options(q.levels))
                for q in config.questions
            ],
            "estate": judgement.as_estate_questions(config.portfolio_questions, config.portfolio_sections, context),
        }
    if domain == "team_governance":
        tg = get_team_governance_config()
        return {"estate": judgement.as_estate_questions(tg.questions, tg.sections, context)}
    if domain == "strategy_projects":
        sp = get_strategy_projects_config()
        return {
            "it_project": [
                EstateQuestion(
                    id=q.id,
                    text=q.text,
                    help=q.help,
                    group="projects",
                    source=q.source,
                    options=[AnswerOption(value=o.label, label=o.label) for o in q.options],
                )
                for q in sp.project_questions
            ],
            "estate": judgement.as_estate_questions(sp.questions, sp.sections, context),
        }
    dt = get_data_tech_config()

    def options(q: Any) -> list[AnswerOption]:
        return [AnswerOption(value=o.label, label=o.label) for o in q.options]

    return {
        "data_domain": [
            EstateQuestion(id=q.id, text=q.text, help=q.help, group="data", options=options(q))
            for q in dt.domain_questions
        ],
        "platform": [
            EstateQuestion(id=q.id, text=q.text, help=q.help, group="platform", options=options(q))
            for q in dt.platform_questions
        ],
        "estate": [
            EstateQuestion(
                id=c.id,
                text=c.text,
                help=c.source,
                group=s.key,
                group_label=s.label,
                options=[AnswerOption(value=k, label=v) for k, v in CHECK_LABELS.items()],
            )
            for s in dt.check_sections
            for c in s.checks
        ],
    }


# ------------------------------------------------------------------ answers


def load_answers(db: Session, engagement_id: str, domain: EstateDomain) -> dict[str, dict[str, EstateAnswer]]:
    rows = db.scalars(
        select(EstateAnswer).where(EstateAnswer.engagement_id == engagement_id, EstateAnswer.domain == domain)
    )
    out: dict[str, dict[str, EstateAnswer]] = {}
    for row in rows:
        out.setdefault(row.subject_id, {})[row.question_id] = row
    return out


def _values(rows: dict[str, EstateAnswer]) -> dict[str, str]:
    return {qid: row.value for qid, row in rows.items() if row.value.strip()}


def _remark_map(rows: dict[str, EstateAnswer]) -> dict[str, str]:
    return {qid: row.remarks for qid, row in rows.items() if row.remarks.strip()}


def _subtitle(item: InventoryItem) -> str:
    fields = item.fields or {}
    keys = {
        "application": ("category", "vendor"),
        "data_domain": ("sensitivity",),
        "platform": ("category", "lifecycle"),
        "it_project": ("status", "vendor"),
    }.get(item.kind, ())
    return " · ".join(str(fields[k]) for k in keys if fields.get(k))


def _subjects(db: Session, engagement_id: str, kind: str) -> list[dt_rules.Subject]:
    return [
        dt_rules.Subject(item_id=i.id, ref=i.ref, fields=dict(i.fields or {}))
        for i in items_of(db, engagement_id, kind)  # type: ignore[arg-type]
    ]


def _apps(db: Session, engagement_id: str) -> list[app_rules.AppInput]:
    """Applications with the analyst's answers — other assessments read their criticality."""
    answers = load_answers(db, engagement_id, "applications")
    return [
        app_rules.AppInput(item_id=i.id, ref=i.ref, fields=dict(i.fields or {}), answers=_values(answers.get(i.id, {})))
        for i in items_of(db, engagement_id, "application")
    ]


def _evidence(db: Session, engagement_id: str, domain: EstateDomain) -> dict[str, list[str]]:
    """What the target's inventories say beside a question. Never an answer by itself."""
    if domain == "data_tech":
        found = dt_rules.tool_evidence(_subjects(db, engagement_id, "cyber_tool"), get_data_tech_config())
        return {check: [line for line, _ in lines] for check, lines in found.items()}
    if domain == "team_governance":
        roles = _subjects(db, engagement_id, "it_role")
        if not roles:
            return {}
        out: dict[str, list[str]] = {}
        leaders = [r.text("designation") or r.name for r in roles if r.text("function") == "IT leadership"]
        out["TG1"] = [
            f"IT team inventory: {', '.join(leaders)}" if leaders else "IT team inventory: no IT leadership role"
        ]
        sole = [r.text("designation") or r.name for r in roles if r.text("sole_holder") == "Yes"]
        if sole:
            out["TG12"] = [f"Only one person can do: {', '.join(sole)}"]
        external = [r for r in roles if r.text("engagement") in tg_rules.EXTERNAL]
        out["TG8"] = [f"{len(external)} of {len(roles)} roles outsourced, contracted or parent-provided"]
        out["TG9"] = [f"{len(roles)} roles in the IT team inventory"]
        return out
    return {}


def get_estate(db: Session, engagement_id: str, domain: str) -> EstateRead:
    get_engagement(db, engagement_id)
    dom = _domain(domain)
    context = assess_context(db, engagement_id)
    sets = question_sets(dom, context)
    answers = load_answers(db, engagement_id, dom)

    subjects: list[EstateSubject] = []
    for kind in SUBJECT_KINDS[dom]:
        ids = {q.id for q in sets[kind]}
        for item in items_of(db, engagement_id, kind):  # type: ignore[arg-type]
            given = _values(answers.get(item.id, {}))
            subjects.append(
                EstateSubject(
                    id=item.id,
                    kind=kind,
                    ref=item.ref,
                    name=str((item.fields or {}).get("name") or item.ref),
                    subtitle=_subtitle(item),
                    answered=sum(1 for q in given if q in ids),
                    question_count=len(ids),
                )
            )
    estate_ids = {q.id for q in sets["estate"]}
    given = _values(answers.get(ESTATE_SUBJECT, {}))
    name, subtitle = QUESTIONNAIRE[dom]
    subjects.append(
        EstateSubject(
            id=ESTATE_SUBJECT,
            kind="estate",
            ref="Q",
            name=name,
            subtitle=subtitle,
            answered=sum(1 for q in given if q in estate_ids),
            question_count=len(estate_ids),
        )
    )

    latest = find_latest(db, engagement_id, dom)
    return EstateRead(
        engagement_id=engagement_id,
        domain=dom,
        subjects=subjects,
        questions=sets,
        answers={
            subject: {qid: EstateAnswerRead(value=row.value, remarks=row.remarks) for qid, row in rows.items()}
            for subject, rows in answers.items()
        },
        evidence=_evidence(db, engagement_id, dom),
        dd_type=context.dd_type,
        ai_material=context.ai_material,
        latest_score_version=latest.version if latest is not None and _current(latest) else None,
    )


def save_answer(db: Session, engagement_id: str, domain: str, write: EstateAnswerWrite) -> EstateRead:
    """Upsert one answer. Rejects an unknown subject, question or option outright —
    an orphan row never renders and never scores, so it would be invisible."""
    get_engagement(db, engagement_id)
    dom = _domain(domain)
    sets = question_sets(dom, assess_context(db, engagement_id))

    if write.subject_id == ESTATE_SUBJECT:
        kind = "estate"
    else:
        item = db.get(InventoryItem, write.subject_id)
        if item is None or item.engagement_id != engagement_id or item.kind not in SUBJECT_KINDS[dom]:
            raise AppError(code="unknown_subject", message="That item is not in this assessment.", status_code=404)
        kind = item.kind

    question = next((q for q in sets[kind] if q.id == write.question_id), None)
    if question is None:
        raise AppError(
            code="unknown_question",
            message=f"{write.question_id!r} is not a question for this item.",
            status_code=404,
        )
    if write.value and write.value not in {o.value for o in question.options}:
        raise AppError(
            code="validation_error",
            message=f"{write.value!r} is not an option for {question.text}.",
            status_code=422,
            field_errors=[{"field": "value", "message": "Not one of the options."}],
        )

    row = db.scalar(
        select(EstateAnswer).where(
            EstateAnswer.engagement_id == engagement_id,
            EstateAnswer.domain == dom,
            EstateAnswer.subject_id == write.subject_id,
            EstateAnswer.question_id == write.question_id,
        )
    )
    if row is None:
        row = EstateAnswer(
            engagement_id=engagement_id,
            domain=dom,
            subject_id=write.subject_id,
            question_id=write.question_id,
        )
        db.add(row)
    if write.value is not None:
        row.value = write.value
    if write.remarks is not None:
        row.remarks = write.remarks
    db.commit()
    return get_estate(db, engagement_id, dom)


# ------------------------------------------------------------------ scoring


def find_latest(db: Session, engagement_id: str, domain: EstateDomain) -> EstateAssessment | None:
    return db.scalar(
        select(EstateAssessment)
        .where(EstateAssessment.engagement_id == engagement_id, EstateAssessment.domain == domain)
        .order_by(EstateAssessment.version.desc())
        .limit(1)
    )


def _current(row: EstateAssessment) -> bool:
    """A payload from before the theme registers cannot be read as one: re-score it."""
    return int((row.payload_json or {}).get("schema_version", 1)) >= SCORE_SCHEMA_VERSION


def find_current(db: Session, engagement_id: str, domain: EstateDomain) -> EstateAssessment | None:
    row = find_latest(db, engagement_id, domain)
    return row if row is not None and _current(row) else None


def _process_scores(db: Session, engagement_id: str) -> dict[str, app_rules.ProcessScore]:
    scores: dict[str, app_rules.ProcessScore] = {}
    for process in process_refs():
        latest = find_latest_score(db, engagement_id, process.key)
        if latest is not None:
            scores[process.key] = app_rules.ProcessScore(
                key=process.key, name=process.name, index=latest.index_value, band=latest.band
            )
    return scores


def _remarks(db: Session, engagement_id: str, domain: EstateDomain) -> list[dict[str, str]]:
    names = {i.id: f"{i.ref} {(i.fields or {}).get('name', '')}".strip() for i in items_of(db, engagement_id)}
    out: list[dict[str, str]] = []
    for subject, rows in load_answers(db, engagement_id, domain).items():
        for qid, row in rows.items():
            if row.remarks.strip():
                out.append(
                    {
                        "subject": names.get(subject, QUESTIONNAIRE[domain][0]),
                        "question": qid,
                        "answer": row.value,
                        "remarks": row.remarks.strip(),
                    }
                )
    return out


def _with_answers(subjects: list[dt_rules.Subject], answers: dict[str, dict[str, EstateAnswer]]) -> list[Any]:
    for subject in subjects:
        subject.answers = _values(answers.get(subject.item_id, {}))
    return subjects


def _budget_inputs(db: Session, engagement_id: str) -> Any:
    from app.services.estate import budget as budget_service  # local: budget imports library

    read = budget_service.get_budget(db, engagement_id)
    return read.inputs if read.saved else None


def compute_payload(
    db: Session, engagement_id: str, dom: EstateDomain, today: date | None = None
) -> tuple[dict[str, Any], list[Gap]]:
    """The deterministic score for one assessment, as a payload dict and its gaps."""
    answers = load_answers(db, engagement_id, dom)
    estate_answers = _values(answers.get(ESTATE_SUBJECT, {}))
    estate_remarks = _remark_map(answers.get(ESTATE_SUBJECT, {}))
    now = datetime.now(UTC)
    day = today or now.date()

    if dom == "applications":
        result = app_rules.score_applications(
            _apps(db, engagement_id),
            get_applications_config(),
            process_refs(),
            _process_scores(db, engagement_id),
            day,
            estate_answers,
            estate_remarks,
        )
        payload = ApplicationsScorePayload(
            generator="rules",
            generated_at=now,
            index=result.index,
            ai_index=result.ai_index,
            counts=result.counts,
            applications=result.applications,
            portfolio=result.portfolio,
            gaps=result.gaps,
            gap_counts=count(result.gaps),
            coverage_note=result.coverage_note,
            **app_rules.band_fields(result.index),
        ).model_dump(mode="json")
        return payload, result.gaps

    if dom == "data_tech":
        app_names = {
            i.ref: str((i.fields or {}).get("name") or i.ref) for i in items_of(db, engagement_id, "application")
        }
        dt = dt_rules.score_data_tech(
            _with_answers(_subjects(db, engagement_id, "data_domain"), answers),
            _with_answers(_subjects(db, engagement_id, "platform"), answers),
            estate_answers,
            app_names,
            get_data_tech_config(),
            estate_remarks,
            _apps(db, engagement_id),
            _subjects(db, engagement_id, "cyber_tool"),
        )
        payload = DataTechScorePayload(
            generator="rules",
            generated_at=now,
            index=dt.index,
            sections=dt.sections,
            domains=dt.domains,
            platforms=dt.platforms,
            checks=dt.checks,
            gaps=dt.gaps,
            gap_counts=count(dt.gaps),
            coverage_note=dt.coverage_note,
            **app_rules.band_fields(dt.index, "maturity"),
        ).model_dump(mode="json")
        return payload, dt.gaps

    context = assess_context(db, engagement_id)
    if dom == "team_governance":
        tg = tg_rules.score_team_governance(
            _subjects(db, engagement_id, "it_role"),
            _apps(db, engagement_id),
            _subjects(db, engagement_id, "it_contract"),
            estate_answers,
            estate_remarks,
            get_team_governance_config(),
            context,
            day,
        )
        payload = TeamGovernanceScorePayload(
            generator="rules",
            generated_at=now,
            index=tg.index,
            sections=tg.sections,
            people=tg.people,
            answered=tg.answered,
            question_count=tg.question_count,
            gaps=tg.gaps,
            gap_counts=count(tg.gaps),
            coverage_note=tg.coverage_note,
            **app_rules.band_fields(tg.index, "maturity"),
        ).model_dump(mode="json")
        return payload, tg.gaps

    sp = sp_rules.score_strategy_projects(
        _with_answers(_subjects(db, engagement_id, "it_project"), answers),
        _apps(db, engagement_id),
        estate_answers,
        estate_remarks,
        _budget_inputs(db, engagement_id),
        get_strategy_projects_config(),
        context,
        day,
    )
    payload = StrategyProjectsScorePayload(
        generator="rules",
        generated_at=now,
        index=sp.index,
        sections=sp.sections,
        projects=sp.projects,
        portfolio=sp.portfolio,
        answered=sp.answered,
        question_count=sp.question_count,
        gaps=sp.gaps,
        gap_counts=count(sp.gaps),
        coverage_note=sp.coverage_note,
        **app_rules.band_fields(sp.index, "maturity"),
    ).model_dump(mode="json")
    return payload, sp.gaps


def generate_score(
    db: Session,
    engagement_id: str,
    domain: str,
    generator_name: str | None = None,
    summariser: EstateSummariser | None = None,
    today: date | None = None,
) -> EstateAssessment:
    get_engagement(db, engagement_id)
    dom = _domain(domain)
    payload, gaps = compute_payload(db, engagement_id, dom, today)

    summary, pointers = rules_summary(dom, payload, gaps)
    payload["executive_summary"], payload["pointers"] = summary, pointers
    if use_llm("estate-summary", generator_name):
        written = (summariser or EstateSummariser()).summarise(dom, payload, _remarks(db, engagement_id, dom))
        if written is not None:
            payload["executive_summary"] = written.executive_summary.strip()
            payload["pointers"] = written.pointers
            payload["generator"] = "llm"

    latest = find_latest(db, engagement_id, dom)
    row = EstateAssessment(
        engagement_id=engagement_id,
        domain=dom,
        version=(latest.version + 1) if latest is not None else 1,
        generator=payload["generator"],
        index_value=payload.get("index"),
        band=payload.get("band"),
        gap_count=len(gaps),
        payload_json=payload,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ------------------------------------------------------------------ reads with overlay


def _notes(db: Session, engagement_id: str, domain: EstateDomain) -> dict[str, EstateGapNote]:
    return {
        n.gap_key: n
        for n in db.scalars(
            select(EstateGapNote).where(EstateGapNote.engagement_id == engagement_id, EstateGapNote.domain == domain)
        )
    }


def to_read(db: Session, row: EstateAssessment) -> EstateScoreRead:
    payload = dict(row.payload_json)
    gaps = overlay(
        [Gap.model_validate(g) for g in payload.get("gaps", [])],
        _notes(db, row.engagement_id, row.domain),  # type: ignore[arg-type]
    )
    payload["gaps"] = [g.model_dump(mode="json") for g in gaps]
    payload["gap_counts"] = count(gaps).model_dump()
    return EstateScoreRead(
        id=row.id,
        engagement_id=row.engagement_id,
        domain=row.domain,
        version=row.version,
        generator=row.generator,
        payload=payload,
        created_at=row.created_at,
    )


def get_latest_score(db: Session, engagement_id: str, domain: str) -> EstateScoreRead:
    get_engagement(db, engagement_id)
    dom = _domain(domain)
    row = find_latest(db, engagement_id, dom)
    if row is None:
        raise AppError(code="no_score", message="This assessment has not been scored yet.", status_code=404)
    if not _current(row):
        raise AppError(
            code="no_score",
            message="The stored score predates the theme registers. Score it again.",
            status_code=404,
        )
    return to_read(db, row)


def save_gap_note(db: Session, engagement_id: str, domain: str, gap_key: str, write: GapNoteWrite) -> EstateScoreRead:
    latest_read = get_latest_score(db, engagement_id, domain)
    dom = _domain(domain)
    if not any(g["key"] == gap_key for g in latest_read.payload["gaps"]):
        raise AppError(code="unknown_gap", message="That gap is not in the latest register.", status_code=404)
    note = _notes(db, engagement_id, dom).get(gap_key)
    if note is None:
        note = EstateGapNote(engagement_id=engagement_id, domain=dom, gap_key=gap_key)
        db.add(note)
    if write.severity is not None:
        note.severity = write.severity
    if write.headline is not None:
        note.headline = write.headline.strip() or None
    if write.evidence is not None:
        lines = [line.strip() for line in write.evidence if line.strip()]
        note.description = "\n".join(lines) or None
    if write.action is not None:
        note.hypothesis = write.action.strip() or None
    db.commit()
    return get_latest_score(db, engagement_id, dom)


def delete_gap_note(db: Session, engagement_id: str, domain: str, gap_key: str) -> EstateScoreRead:
    dom = _domain(domain)
    note = _notes(db, engagement_id, dom).get(gap_key)
    if note is not None:
        db.delete(note)
        db.commit()
    return get_latest_score(db, engagement_id, dom)


def summaries(db: Session, engagement_id: str) -> dict[str, dict[str, Any]]:
    """Headline per assessment for the Assess index: item counts and the latest score."""
    get_engagement(db, engagement_id)
    out: dict[str, dict[str, Any]] = {}
    for dom in DOMAINS:
        kinds = SUBJECT_KINDS[dom] or ("it_role",)
        items = db.scalar(
            select(func.count())
            .select_from(InventoryItem)
            .where(InventoryItem.engagement_id == engagement_id, InventoryItem.kind.in_(kinds))
        )
        latest = find_current(db, engagement_id, dom)
        out[dom] = {
            "items": int(items or 0),
            "has_score": latest is not None,
            "index": latest.index_value if latest is not None else None,
            "band": latest.band if latest is not None else None,
            "gap_count": latest.gap_count if latest is not None else 0,
        }
    return out
