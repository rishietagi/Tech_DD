"""Persistence for the Initial Request List. Versioned, never destructive.

Mirrors `services/scope/service.py`. The one structural difference: **responses live in
their own table**, so regenerating an IRL never clobbers answers someone has typed. When
a new version is generated, responses carried on stable question ids are copied forward.
"""

from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.irl import InformationRequestList, IrlDocumentStatus, IrlResponse
from app.schemas.irl import ImportResponsesResult, IrlPayload, IrlQuestion, IrlTracking
from app.schemas.research import ResearchPayload
from app.schemas.scope import ScopeOfWorkPayloadV2
from app.services.checklist.ranking import rank_questions
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.irl.composer import group_functions
from app.services.irl.import_xlsx import import_responses
from app.services.irl.llm import LlmIrlGenerator, RulesIrlGenerator
from app.services.research.service import find_latest_research
from app.services.scope import service as scope_service


def _generator_for(name: str | None) -> LlmIrlGenerator | RulesIrlGenerator:
    """Explicit request wins; otherwise follow the same setting the scope engine uses."""
    resolved = name or get_settings().scope_generator
    return LlmIrlGenerator() if resolved == "llm" else RulesIrlGenerator()


def generate_irl(
    db: Session,
    engagement_id: str,
    generator_name: str | None = None,
) -> InformationRequestList:
    """Build a request list from the latest scope, and store it as a new version."""
    engagement = get_engagement(db, engagement_id)

    # The IRL asks for the evidence the scope decided it needs, so a scope is a real
    # precondition rather than a convenience.
    try:
        scope_row = scope_service.get_latest_scope(db, engagement_id)
    except AppError as exc:
        if exc.code == "no_scope":
            raise AppError(
                code="not_scoped",
                message=(
                    "Generate a scope of work first. The request list is built from the "
                    "evidence the scope decided it needs."
                ),
                status_code=409,
            ) from exc
        raise

    payload_json = scope_row.payload_json
    if payload_json.get("schema_version") != 2:
        raise AppError(
            code="scope_not_supported",
            message="Only schema v2 scopes can produce a request list",
            status_code=409,
        )
    scope = ScopeOfWorkPayloadV2.model_validate(payload_json)

    intake = assemble_intake_full(engagement)

    # Research makes the questions specific and the function names fit the business, but
    # its absence must never block generation.
    research_row = find_latest_research(db, engagement_id)
    research: ResearchPayload | None = None
    if research_row is not None:
        try:
            research = ResearchPayload.model_validate(research_row.payload_json)
        except Exception:  # noqa: BLE001 - stale payload shape must not break the IRL
            research = None

    previous = _latest_irl(db, engagement_id)
    previous_functions = _functions_of(previous)

    generator = _generator_for(generator_name)
    if isinstance(generator, LlmIrlGenerator):
        payload = generator.generate(
            intake,
            scope,
            research=research,
            source_scope_version=scope_row.version,
            previous_functions=previous_functions,
        )
    else:
        payload = generator.generate(
            intake, scope, research=research, source_scope_version=scope_row.version
        )

    # Hand-written work survives regeneration (Rishi, 2026-09-02): questions the analyst
    # added are carried over, and questions they reworded keep their wording. Same
    # principle as responses — regenerating must never destroy what a person typed.
    _carry_forward_manual_work(previous, payload)

    irl = InformationRequestList(
        engagement_id=engagement_id,
        version=(previous.version if previous else 0) + 1,
        generator=payload.generator,
        source_scope_version=scope_row.version,
        payload_json=payload.model_dump(mode="json"),
    )
    db.add(irl)
    db.flush()

    _carry_forward_responses(db, previous, irl, payload)

    db.commit()
    db.refresh(irl)
    return irl


def _carry_forward_manual_work(
    previous: InformationRequestList | None, payload: IrlPayload
) -> None:
    """Preserve analyst additions and edits across a regeneration.

    Two different things are carried, for the same reason responses are (Rishi's call,
    2026-09-02 — he chose "carry them forward, keep edits" over resetting):

    * **Added questions** are appended to the new list. They exist precisely because the
      generator did not think of them, so a regeneration will not think of them either.
    * **Reworded questions** keep the analyst's wording, where the question still exists
      in the new list. The engine's fresh text is stored as `original_question`, so a
      reviewer can still see what the regeneration would have said.

    The trade, stated plainly: an edited question may drift out of step with a scope that
    has since changed. That is visible — the question is flagged `edited_by_human` — and
    it is the lesser harm against silently discarding someone's rewording.
    """
    if previous is None:
        return

    try:
        old = IrlPayload.model_validate(previous.payload_json)
    except Exception:  # noqa: BLE001 - a stale payload shape must not block regeneration
        return

    fresh = {q.id: q for q in payload.questions}

    for question in old.questions:
        if question.source == "manual":
            if question.id not in fresh:
                payload.questions.append(question.model_copy(deep=True))
            continue

        if question.edited_by_human:
            target = fresh.get(question.id)
            if target is not None:
                # Keep the human wording; record what this run would have written.
                target.original_question = target.question
                target.question = question.question
                target.edited_by_human = True

    payload.functions = group_functions(payload.questions)


def _latest_irl(db: Session, engagement_id: str) -> InformationRequestList | None:
    return db.execute(
        select(InformationRequestList)
        .where(InformationRequestList.engagement_id == engagement_id)
        .order_by(InformationRequestList.version.desc())
        .limit(1)
    ).scalar_one_or_none()


def _functions_of(irl: InformationRequestList | None) -> list[str] | None:
    """The previous run's **business function** names, fed back so naming stays stable.

    Read off the questions, not off `payload.functions`: since 2026-09-02 that list holds
    scope-area headings, not function names. Feeding scope areas back to the model as
    "previous functions" would tell it to name its owner column after the deck's headings,
    which is precisely the confusion the two-column split exists to avoid.
    """
    if irl is None:
        return None

    seen: list[str] = []
    for question in irl.payload_json.get("questions") or []:
        if not isinstance(question, dict):
            continue
        name = str(question.get("function") or "").strip()
        if name and name not in seen:
            seen.append(name)
    return seen or None


def _carry_forward_responses(
    db: Session,
    previous: InformationRequestList | None,
    fresh: InformationRequestList,
    payload: IrlPayload,
) -> None:
    """Copy answers onto the new version wherever the question id still exists.

    Seed ids are derived from the scope row (`PD-01-E1`), so they survive a regeneration
    against an unchanged scope — which is exactly when a user would be upset to lose
    their typing. Model-added questions get positional ids and will not always match;
    those answers stay on the old version rather than being mapped onto a question that
    may now say something different.
    """
    if previous is None:
        return

    existing = {r.question_id: r.response_text for r in previous.responses}
    if not existing:
        return

    live_ids = {q.id for q in payload.questions}
    for question_id, text in existing.items():
        if question_id in live_ids and text.strip():
            db.add(
                IrlResponse(irl_id=fresh.id, question_id=question_id, response_text=text)
            )


def get_latest_irl(db: Session, engagement_id: str) -> InformationRequestList:
    get_engagement(db, engagement_id)
    irl = _latest_irl(db, engagement_id)
    if irl is None:
        raise AppError(
            code="no_irl",
            message="No request list has been generated for this engagement yet",
            status_code=404,
        )
    return irl


def get_irl_version(db: Session, engagement_id: str, version: int) -> InformationRequestList:
    get_engagement(db, engagement_id)
    irl = db.execute(
        select(InformationRequestList).where(
            InformationRequestList.engagement_id == engagement_id,
            InformationRequestList.version == version,
        )
    ).scalar_one_or_none()
    if irl is None:
        raise AppError(
            code="no_irl_version",
            message=f"Request list version {version} does not exist",
            status_code=404,
        )
    return irl


def list_irl_versions(db: Session, engagement_id: str) -> list[InformationRequestList]:
    get_engagement(db, engagement_id)
    return list(
        db.execute(
            select(InformationRequestList)
            .where(InformationRequestList.engagement_id == engagement_id)
            .order_by(InformationRequestList.version.desc())
        ).scalars()
    )


def responses_for(irl: InformationRequestList) -> dict[str, str]:
    return {r.question_id: r.response_text for r in irl.responses}


def save_response(
    db: Session, engagement_id: str, question_id: str, text: str
) -> InformationRequestList:
    """Upsert one answer on the latest version.

    An empty string deletes the row rather than storing blank text, so "cleared" and
    "never answered" are the same state on read.
    """
    irl = get_latest_irl(db, engagement_id)

    known = {q.get("id") for q in irl.payload_json.get("questions") or []}
    if question_id not in known:
        raise AppError(
            code="unknown_question",
            message=f"No question {question_id} in this request list",
            status_code=404,
        )

    existing = db.execute(
        select(IrlResponse).where(
            IrlResponse.irl_id == irl.id, IrlResponse.question_id == question_id
        )
    ).scalar_one_or_none()

    cleaned = text.strip()
    if not cleaned:
        if existing is not None:
            db.delete(existing)
    elif existing is not None:
        existing.response_text = cleaned
    else:
        db.add(IrlResponse(irl_id=irl.id, question_id=question_id, response_text=cleaned))

    db.commit()
    db.refresh(irl)
    return irl


# ------------------------------------------------------- hand-editing (2026-09-02)
#
# An analyst may add a request the generated list missed, reword one, or remove one that
# does not apply. All three mutate `payload_json`, which is the trap recorded in
# docs/PROJECT_LOG.md: `dict(payload)` is a *shallow* copy, so mutating a nested question
# edits the loaded value in place, SQLAlchemy sees no change and silently drops the write.
# Every function below therefore deep-copies and calls `flag_modified`.


def _rewrite_payload(db: Session, irl: InformationRequestList, payload: IrlPayload) -> None:
    """Persist a modified payload, defeating the shallow-copy trap."""
    irl.payload_json = deepcopy(payload.model_dump(mode="json"))
    flag_modified(irl, "payload_json")
    db.commit()
    db.refresh(irl)


def _payload_of(irl: InformationRequestList) -> IrlPayload:
    return IrlPayload.model_validate(irl.payload_json)


def add_question(
    db: Session,
    engagement_id: str,
    question: str,
    function: str,
    scope_area: str = "",
) -> InformationRequestList:
    """Append an analyst-written request to the latest version."""
    irl = get_latest_irl(db, engagement_id)
    payload = _payload_of(irl)

    # Numbered from the count of existing manual questions so ids stay readable and never
    # collide with the generator's `ADD-nnn` or a seed's `ROW-En`.
    existing = sum(1 for q in payload.questions if q.source == "manual")
    new_id = f"MAN-{existing + 1:03d}"
    while any(q.id == new_id for q in payload.questions):
        existing += 1
        new_id = f"MAN-{existing + 1:03d}"

    payload.questions.append(
        IrlQuestion(
            id=new_id,
            function=function.strip(),
            scope_area=scope_area.strip(),
            question=question.strip(),
            source="manual",
        )
    )
    payload.functions = group_functions(payload.questions)

    _rewrite_payload(db, irl, payload)
    return irl


def update_question(
    db: Session,
    engagement_id: str,
    question_id: str,
    question: str | None = None,
    function: str | None = None,
    scope_area: str | None = None,
) -> InformationRequestList:
    """Reword a request, or move it to a different function or scope area.

    The original wording is kept beside the edit rather than replaced, the same pattern
    the scope rows use for human overrides: a reviewer can always see what the engine
    produced and what a person changed it to.
    """
    irl = get_latest_irl(db, engagement_id)
    payload = _payload_of(irl)

    target = next((q for q in payload.questions if q.id == question_id), None)
    if target is None:
        raise AppError(
            code="unknown_question",
            message=f"No question {question_id} in this request list",
            status_code=404,
        )

    if question is not None and question.strip() and question.strip() != target.question:
        if not target.edited_by_human:
            target.original_question = target.question
        target.question = question.strip()
        target.edited_by_human = True

    if function is not None and function.strip():
        target.function = function.strip()
    if scope_area is not None:
        target.scope_area = scope_area.strip()

    payload.functions = group_functions(payload.questions)
    _rewrite_payload(db, irl, payload)
    return irl


def delete_question(
    db: Session, engagement_id: str, question_id: str
) -> InformationRequestList:
    """Remove a request, and any response and document status hanging off it.

    The response goes with it deliberately: leaving an orphan row would mean a later
    regeneration silently resurrected an answer against a question nobody can see.
    """
    irl = get_latest_irl(db, engagement_id)
    payload = _payload_of(irl)

    if not any(q.id == question_id for q in payload.questions):
        raise AppError(
            code="unknown_question",
            message=f"No question {question_id} in this request list",
            status_code=404,
        )

    payload.questions = [q for q in payload.questions if q.id != question_id]
    payload.functions = group_functions(payload.questions)
    _rewrite_payload(db, irl, payload)

    for row in db.execute(
        select(IrlResponse).where(
            IrlResponse.irl_id == irl.id, IrlResponse.question_id == question_id
        )
    ).scalars():
        db.delete(row)
    for status in db.execute(
        select(IrlDocumentStatus).where(
            IrlDocumentStatus.irl_id == irl.id,
            IrlDocumentStatus.question_id == question_id,
        )
    ).scalars():
        db.delete(status)

    db.commit()
    db.refresh(irl)
    return irl


def import_responses_from_workbook(
    db: Session, engagement_id: str, content: bytes
) -> tuple[InformationRequestList, ImportResponsesResult]:
    """Scrape a completed workbook's Response column into the response table."""
    irl = get_latest_irl(db, engagement_id)
    payload = _payload_of(irl)

    responses, result = import_responses(content, payload, responses_for(irl))

    for question_id, text in responses.items():
        existing = db.execute(
            select(IrlResponse).where(
                IrlResponse.irl_id == irl.id, IrlResponse.question_id == question_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.response_text = text
        else:
            db.add(
                IrlResponse(irl_id=irl.id, question_id=question_id, response_text=text)
            )

    db.commit()
    db.refresh(irl)
    return irl, result


# ------------------------------------------------- tracking merged in (2026-09-02)
#
# The checklist's per-request tracking now renders inside the IRL, so the analyst works
# one screen. Storage is unchanged: `irl_response` holds what the client wrote and
# `irl_document_status` what the deal team observed. They keep different authors and
# different lifecycles — the shared-drive scanner will write status without touching a
# client's typed answer — so merging them into one table would be wrong even though they
# now render together.


def tracking_for(db: Session, engagement_id: str, irl: InformationRequestList) -> dict[str, IrlTracking]:
    """Status, document type, remarks and priority for every question in this IRL.

    Priority is computed from the scope rather than stored, exactly as the checklist does
    it — the two views must never disagree, and the only way to guarantee that is one
    source of truth.
    """
    try:
        payload = IrlPayload.model_validate(irl.payload_json)
    except Exception:  # noqa: BLE001 - a stale payload must not break the read
        return {}

    ranked = rank_questions(payload.questions, _scope_for_ranking(db, engagement_id))
    stored = {s.question_id: s for s in irl.document_statuses}

    merged: dict[str, IrlTracking] = {}
    for question in payload.questions:
        priority, reason = ranked.get(question.id, ("medium", "Not ranked"))
        record = stored.get(question.id)
        merged[question.id] = IrlTracking(
            status=record.status if record else "not_received",
            document_type=record.document_type if record else "",
            remarks=record.notes if record else "",
            priority=priority,
            priority_reason=reason,
            set_by_human=record.set_by_human if record else False,
            updated_at=record.updated_at if record else None,
        )
    return merged


def _scope_for_ranking(db: Session, engagement_id: str) -> ScopeOfWorkPayloadV2 | None:
    """The scope the ranking reads tiers from. Absent scope degrades, never raises."""
    try:
        row = scope_service.get_latest_scope(db, engagement_id)
    except AppError:
        return None
    if row.payload_json.get("schema_version") != 2:
        return None
    try:
        return ScopeOfWorkPayloadV2.model_validate(row.payload_json)
    except Exception:  # noqa: BLE001 - a stale scope must not break the IRL
        return None


def save_tracking(
    db: Session,
    engagement_id: str,
    question_id: str,
    status: str | None = None,
    document_type: str | None = None,
    remarks: str | None = None,
) -> InformationRequestList:
    """Set what the deal team observes about one request's document.

    Marked `set_by_human` so a later shared-drive scan does not overwrite a judgement
    someone made deliberately — the first of the scanner's four rules.
    """
    irl = get_latest_irl(db, engagement_id)

    known = {q.get("id") for q in irl.payload_json.get("questions") or []}
    if question_id not in known:
        raise AppError(
            code="unknown_question",
            message=f"No question {question_id} in this request list",
            status_code=404,
        )

    record = db.execute(
        select(IrlDocumentStatus).where(
            IrlDocumentStatus.irl_id == irl.id,
            IrlDocumentStatus.question_id == question_id,
        )
    ).scalar_one_or_none()

    if record is None:
        record = IrlDocumentStatus(irl_id=irl.id, question_id=question_id)
        db.add(record)

    if status is not None:
        record.status = status
    if document_type is not None:
        record.document_type = document_type.strip()
    if remarks is not None:
        record.notes = remarks.strip()
    record.set_by_human = True

    db.commit()
    db.refresh(irl)
    return irl
