from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.checklist import ChecklistItemUpdate, ChecklistRead
from app.services.checklist import service as checklist_service
from app.services.checklist.scanner import scan_shared_drive

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
    """Walk the shared drive and update statuses automatically.

    **Not connected yet** — returns 501 with an explanation. The route exists so the
    contract is visible in OpenAPI and the UI has something real to call once the drive
    path and matching rules are configured at deployment. See
    `services/checklist/scanner.py`.
    """
    scan_shared_drive(engagement_id)
    return checklist_service.build_checklist(db, engagement_id)  # pragma: no cover
