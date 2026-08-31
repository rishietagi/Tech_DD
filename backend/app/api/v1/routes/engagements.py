from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.engagement import (
    EngagementCreate,
    EngagementListResponse,
    EngagementRead,
    EngagementSummary,
    EngagementUpdate,
)
from app.schemas.intake import SECTION_DRAFT_MODELS
from app.services import engagements as engagement_service

router = APIRouter(prefix="/engagements", tags=["engagements"])

_VALID_SECTIONS = set(SECTION_DRAFT_MODELS.keys())


@router.post("", response_model=EngagementRead, status_code=status.HTTP_201_CREATED)
def create_engagement(payload: EngagementCreate, db: Session = Depends(get_db)) -> EngagementRead:
    engagement = engagement_service.create_engagement(db, payload)
    return EngagementRead.from_engagement(engagement)


@router.get("", response_model=EngagementListResponse)
def list_engagements(
    q: str | None = None,
    status_filter: str | None = None,
    dd_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> EngagementListResponse:
    items, total = engagement_service.list_engagements(
        db, q=q, status=status_filter, dd_type=dd_type, limit=limit, offset=offset
    )
    return EngagementListResponse(items=[EngagementSummary.model_validate(item) for item in items], total=total)


@router.get("/{engagement_id}", response_model=EngagementRead)
def get_engagement(engagement_id: str, db: Session = Depends(get_db)) -> EngagementRead:
    engagement = engagement_service.get_engagement(db, engagement_id)
    return EngagementRead.from_engagement(engagement)


@router.patch("/{engagement_id}", response_model=EngagementRead)
def update_engagement(engagement_id: str, payload: EngagementUpdate, db: Session = Depends(get_db)) -> EngagementRead:
    engagement = engagement_service.update_engagement(db, engagement_id, payload)
    return EngagementRead.from_engagement(engagement)


@router.delete("/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_engagement(
    engagement_id: str,
    permanent: bool = False,
    db: Session = Depends(get_db),
) -> None:
    """Archive by default; `?permanent=true` removes the row and its children for good.

    Archiving stays the default so an existing caller keeps the behaviour it had.
    Permanent deletion works on any status, including already-archived rows.
    """
    if permanent:
        engagement_service.delete_engagement(db, engagement_id)
    else:
        engagement_service.archive_engagement(db, engagement_id)


@router.patch("/{engagement_id}/intake/{section}", response_model=EngagementRead)
def patch_intake_section(
    engagement_id: str, section: str, payload: dict[str, object], db: Session = Depends(get_db)
) -> EngagementRead:
    if section not in _VALID_SECTIONS:
        raise AppError(code="invalid_section", message=f"Unknown intake section '{section}'", status_code=404)

    draft_model = SECTION_DRAFT_MODELS[section]
    validated = draft_model.model_validate(payload)
    engagement = engagement_service.patch_intake_section(
        db, engagement_id, section, validated.model_dump(exclude_unset=True)
    )
    return EngagementRead.from_engagement(engagement)


@router.post("/{engagement_id}/submit", response_model=EngagementRead)
def submit_engagement(engagement_id: str, db: Session = Depends(get_db)) -> EngagementRead:
    engagement = engagement_service.submit_engagement(db, engagement_id)
    return EngagementRead.from_engagement(engagement)
