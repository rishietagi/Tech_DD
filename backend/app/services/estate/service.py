"""Persistence and assembly for the application and data & technology assessments.

Same lifecycles as the business-process assessment: answers are working notes (one
current set, not versioned); scores are versioned; consultant edits to gaps are an overlay
applied at read time so a re-score never discards them.
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
)
from app.services.assess.service import find_latest_score
from app.services.engagements import get_engagement
from app.services.estate import applications as app_rules
from app.services.estate import data_tech as dt_rules
from app.services.estate.gaps import count, overlay
from app.services.estate.inventory import items_of, process_refs
from app.services.estate.library import get_applications_config, get_data_tech_config
from app.services.estate.llm import EstateSummariser, rules_summary
from app.services.intelligence.mode import use_llm

logger = logging.getLogger(__name__)

DOMAINS: tuple[EstateDomain, ...] = ("applications", "data_tech")
CHECK_LABELS = {
    "pass": "Pass — in place and evidenced",
    "partial": "Partial — partly in place",
    "fail": "Fail — not in place",
    "unknown": "Unknown — not yet established",
}


def _domain(domain: str) -> EstateDomain:
    if domain not in DOMAINS:
        raise AppError(
            code="unknown_domain",
            message=f"{domain!r} is not an estate assessment. Use applications or data_tech.",
            status_code=404,
        )
    return domain  # type: ignore[return-value]


# ------------------------------------------------------------------ questions


def question_sets(domain: EstateDomain) -> dict[str, list[EstateQuestion]]:
    if domain == "applications":
        config = get_applications_config()
        return {
            "application": [
                EstateQuestion(
                    id=q.id,
                    text=q.text,
                    help=q.help,
                    group=q.group,
                    options=[
                        AnswerOption(value=str(level), label=f"{level} — {text}")
                        for level, text in sorted(q.levels.items())
                    ],
                )
                for q in config.questions
            ]
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
                options=[AnswerOption(value=k, label=v) for k, v in CHECK_LABELS.items()],
            )
            for s in dt.check_sections
            for c in s.checks
        ],
    }


def _subject_kinds(domain: EstateDomain) -> tuple[str, ...]:
    return ("application",) if domain == "applications" else ("data_domain", "platform")


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


def _subtitle(item: InventoryItem) -> str:
    fields = item.fields or {}
    keys = {
        "application": ("category", "vendor"),
        "data_domain": ("sensitivity",),
        "platform": ("category", "lifecycle"),
    }[item.kind]
    return " · ".join(str(fields[k]) for k in keys if fields.get(k))


def get_estate(db: Session, engagement_id: str, domain: str) -> EstateRead:
    get_engagement(db, engagement_id)
    dom = _domain(domain)
    sets = question_sets(dom)
    answers = load_answers(db, engagement_id, dom)

    subjects: list[EstateSubject] = []
    for kind in _subject_kinds(dom):
        for item in items_of(db, engagement_id, kind):  # type: ignore[arg-type]
            ids = {q.id for q in sets[kind]}
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
    if dom == "data_tech":
        given = _values(answers.get(ESTATE_SUBJECT, {}))
        subjects.append(
            EstateSubject(
                id=ESTATE_SUBJECT,
                kind="estate",
                ref="EST",
                name="Estate checks",
                subtitle="Resilience, engineering practice, cyber security",
                answered=len(given),
                question_count=len(sets["estate"]),
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
        latest_score_version=latest.version if latest is not None else None,
    )


def save_answer(db: Session, engagement_id: str, domain: str, write: EstateAnswerWrite) -> EstateRead:
    """Upsert one answer. Rejects an unknown subject, question or option outright —
    an orphan row never renders and never scores, so it would be invisible."""
    get_engagement(db, engagement_id)
    dom = _domain(domain)
    sets = question_sets(dom)

    if write.subject_id == ESTATE_SUBJECT:
        if dom != "data_tech":
            raise AppError(
                code="unknown_subject", message="Estate checks belong to data & technology.", status_code=404
            )
        kind = "estate"
    else:
        item = db.get(InventoryItem, write.subject_id)
        if item is None or item.engagement_id != engagement_id or item.kind not in _subject_kinds(dom):
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
                        "subject": names.get(subject, "Estate checks"),
                        "question": qid,
                        "answer": row.value,
                        "remarks": row.remarks.strip(),
                    }
                )
    return out


def _use_llm(generator_name: str | None) -> bool:
    return use_llm("estate-summary", generator_name)


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
    answers = load_answers(db, engagement_id, dom)
    now = datetime.now(UTC)

    if dom == "applications":
        apps = [
            app_rules.AppInput(
                item_id=i.id, ref=i.ref, fields=dict(i.fields or {}), answers=_values(answers.get(i.id, {}))
            )
            for i in items_of(db, engagement_id, "application")
        ]
        result = app_rules.score_applications(
            apps,
            get_applications_config(),
            process_refs(),
            _process_scores(db, engagement_id),
            today or now.date(),
        )
        payload: dict[str, Any] = ApplicationsScorePayload(
            generator="rules",
            generated_at=now,
            index=result.index,
            ai_index=result.ai_index,
            counts=result.counts,
            applications=result.applications,
            gaps=result.gaps,
            gap_counts=count(result.gaps),
            coverage_note=result.coverage_note,
            **app_rules.band_fields(result.index),
        ).model_dump(mode="json")
        gaps = result.gaps
    else:

        def subjects(kind: str) -> list[dt_rules.Subject]:
            return [
                dt_rules.Subject(
                    item_id=i.id, ref=i.ref, fields=dict(i.fields or {}), answers=_values(answers.get(i.id, {}))
                )
                for i in items_of(db, engagement_id, kind)  # type: ignore[arg-type]
            ]

        app_names = {
            i.ref: str((i.fields or {}).get("name") or i.ref) for i in items_of(db, engagement_id, "application")
        }
        dt = dt_rules.score_data_tech(
            subjects("data_domain"),
            subjects("platform"),
            _values(answers.get(ESTATE_SUBJECT, {})),
            app_names,
            get_data_tech_config(),
            {qid: row.remarks for qid, row in answers.get(ESTATE_SUBJECT, {}).items() if row.remarks.strip()},
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
            **app_rules.band_fields(dt.index),
        ).model_dump(mode="json")
        gaps = dt.gaps

    summary, pointers = rules_summary(dom, payload, gaps)
    payload["executive_summary"], payload["pointers"] = summary, pointers
    if _use_llm(generator_name):
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
    for attr in ("severity", "description", "hypothesis"):
        value = getattr(write, attr)
        if value is not None:
            setattr(note, attr, value.strip() or None)
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
    """Headline per domain for the Assess index: item counts and the latest score."""
    get_engagement(db, engagement_id)
    out: dict[str, dict[str, Any]] = {}
    for dom in DOMAINS:
        kinds = _subject_kinds(dom)
        items = db.scalar(
            select(func.count())
            .select_from(InventoryItem)
            .where(InventoryItem.engagement_id == engagement_id, InventoryItem.kind.in_(kinds))
        )
        latest = find_latest(db, engagement_id, dom)
        out[dom] = {
            "items": int(items or 0),
            "has_score": latest is not None,
            "index": latest.index_value if latest is not None else None,
            "band": latest.band if latest is not None else None,
            "gap_count": latest.gap_count if latest is not None else 0,
        }
    return out
