"""Assembling the checklist and recording what has arrived.

The checklist is built on read from three sources: the IRL's questions, the statuses
stored against them, and the priority computed from the scope. Nothing is stored that
could drift out of step with the request list it tracks.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.irl import InformationRequestList, IrlDocumentStatus
from app.schemas.checklist import (
    ChecklistItem,
    ChecklistItemUpdate,
    ChecklistRead,
    ChecklistSummary,
)
from app.schemas.irl import IrlPayload
from app.schemas.scope import ScopeOfWorkPayloadV2
from app.services.checklist.ranking import PRIORITY_ORDER, rank_questions
from app.services.engagements import get_engagement
from app.services.irl import service as irl_service
from app.services.scope import service as scope_service


def _scope_for(db: Session, engagement_id: str) -> ScopeOfWorkPayloadV2 | None:
    """The scope the ranking reads tiers from. Absent scope degrades, never raises."""
    try:
        row = scope_service.get_latest_scope(db, engagement_id)
    except AppError:
        return None
    if row.payload_json.get("schema_version") != 2:
        return None
    try:
        return ScopeOfWorkPayloadV2.model_validate(row.payload_json)
    except Exception:  # noqa: BLE001 - a stale scope must not break the checklist
        return None


def _statuses_for(irl: InformationRequestList) -> dict[str, IrlDocumentStatus]:
    return {s.question_id: s for s in irl.document_statuses}


def build_checklist(db: Session, engagement_id: str) -> ChecklistRead:
    """Assemble the current checklist for the latest IRL."""
    get_engagement(db, engagement_id)
    irl = irl_service.get_latest_irl(db, engagement_id)
    payload = IrlPayload.model_validate(irl.payload_json)

    scope = _scope_for(db, engagement_id)
    ranked = rank_questions(payload.questions, scope)
    stored = _statuses_for(irl)

    items: list[ChecklistItem] = []
    for question in payload.questions:
        priority, reason = ranked.get(question.id, ("medium", "Not ranked"))
        record = stored.get(question.id)
        items.append(
            ChecklistItem(
                question_id=question.id,
                function=question.function,
                document_requested=question.question,
                document_type=record.document_type if record else "",
                status=record.status if record else "not_received",
                notes=record.notes if record else "",
                priority=priority,
                priority_reason=reason,
                source_row_id=question.source_row_id,
                source_row_title=question.source_row_title,
                matched_files=list(record.matched_files or []) if record else [],
                set_by_human=record.set_by_human if record else False,
                updated_at=record.updated_at if record else None,
            )
        )

    # Most important first; within a priority, keep the IRL's own function grouping so
    # the checklist and the request list read in a recognisably similar order.
    items.sort(key=lambda i: (PRIORITY_ORDER.get(i.priority, 9), i.function, i.question_id))

    return ChecklistRead(
        engagement_id=engagement_id,
        irl_id=irl.id,
        irl_version=irl.version,
        company_name=payload.company_name,
        items=items,
        summary=_summarise(items),
        last_scanned_at=None,
    )


def _summarise(items: list[ChecklistItem]) -> ChecklistSummary:
    outstanding = [i for i in items if i.status != "received_completely"]
    return ChecklistSummary(
        total=len(items),
        received_completely=sum(1 for i in items if i.status == "received_completely"),
        received_partially=sum(1 for i in items if i.status == "received_partially"),
        not_received=sum(1 for i in items if i.status == "not_received"),
        outstanding_critical=sum(1 for i in outstanding if i.priority == "critical"),
        outstanding_high=sum(1 for i in outstanding if i.priority == "high"),
    )


def update_item(
    db: Session,
    engagement_id: str,
    question_id: str,
    update: ChecklistItemUpdate,
) -> ChecklistRead:
    """Set the status, type or notes on one request.

    Marked `set_by_human` so a later shared-drive scan does not overwrite a judgement
    someone made deliberately.
    """
    get_engagement(db, engagement_id)
    irl = irl_service.get_latest_irl(db, engagement_id)

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

    if update.status is not None:
        record.status = update.status
    if update.document_type is not None:
        record.document_type = update.document_type.strip()
    if update.notes is not None:
        record.notes = update.notes.strip()

    record.set_by_human = True

    db.commit()
    return build_checklist(db, engagement_id)
