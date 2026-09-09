from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.checklist import ChecklistItemUpdate, ChecklistRead
from app.services.checklist import service as checklist_service

router = APIRouter(prefix="/engagements/{engagement_id}/checklist", tags=["checklist"])


@router.get("", response_model=ChecklistRead)
def get_checklist(engagement_id: str, db: Session = Depends(get_db)) -> ChecklistRead:
    """The checklist for the latest request list. 404 `no_irl` if none has been built."""
    return checklist_service.build_checklist(db, engagement_id)


@router.patch("/{question_id}", response_model=ChecklistRead)
def update_checklist_item(
    engagement_id: str,
    question_id: str,
    payload: ChecklistItemUpdate,
    db: Session = Depends(get_db),
) -> ChecklistRead:
    """Set the status, document type or notes on one request.

    Returns the whole checklist so the caller's summary counts stay consistent with the
    row it just changed.
    """
    return checklist_service.update_item(db, engagement_id, question_id, payload)


@router.post("/scan", response_model=ChecklistRead)
def scan_for_documents(engagement_id: str, db: Session = Depends(get_db)) -> ChecklistRead:
    """Walk the shared drive, match files to requests, and update the checklist.

    Reads every file under `SHARED_DRIVE_ROOT`, shortlists candidates per request by
    filename and folder, and — where a model is configured — judges whether what arrived
    is complete, naming the document type and writing the follow-up questions that close
    any gap.

    Returns the rebuilt checklist with a `scan` block saying what the walk did. A
    human-set status is never overwritten. See `services/checklist/scanner.py` for the
    rules this obeys.
    """
    return checklist_service.scan_drive(db, engagement_id)
