from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models.engagement import Engagement, EngagementDenorm, EngagementIntake
from app.reference.enums import DdTypePreference, EngagementStatus
from app.schemas.engagement import EngagementCreate, EngagementUpdate
from app.schemas.intake import (
    SECTION_JSON_COLUMNS,
    SECTION_REQUIRED_MODELS,
    IntakeFull,
)

INTAKE_STEP_ORDER = ["context", "rationale", "structure", "target", "technology", "objectives"]

# The user's declared archetype maps straight onto denorm.dd_type. "Let the platform
# decide" leaves it NULL until the scope engine computes one (TODO(phase-2): backfill
# from the generated scope's classification).
_DD_TYPE_VALUE_MAP = {
    DdTypePreference.enterprise.value: "enterprise",
    DdTypePreference.product.value: "product",
    DdTypePreference.blended.value: "blended",
}


def create_engagement(db: Session, payload: EngagementCreate) -> Engagement:
    engagement = Engagement(deal_name=payload.deal_name, status=EngagementStatus.draft.value)
    db.add(engagement)
    db.flush()

    db.add(EngagementIntake(engagement_id=engagement.id))
    db.add(EngagementDenorm(engagement_id=engagement.id))
    db.commit()
    db.refresh(engagement)
    return engagement


def get_engagement(db: Session, engagement_id: str) -> Engagement:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None or engagement.status == EngagementStatus.archived.value:
        raise NotFoundError(f"Engagement {engagement_id} not found")
    return engagement


def list_engagements(
    db: Session,
    q: str | None = None,
    status: str | None = None,
    dd_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Engagement], int]:
    stmt = select(Engagement).where(Engagement.status != EngagementStatus.archived.value)

    if status:
        stmt = stmt.where(Engagement.status == status)
    if q:
        stmt = stmt.where(Engagement.deal_name.ilike(f"%{q}%"))
    if dd_type:
        stmt = stmt.join(EngagementDenorm).where(EngagementDenorm.dd_type == dd_type)

    total = len(db.execute(stmt).scalars().all())
    stmt = stmt.order_by(Engagement.updated_at.desc()).limit(limit).offset(offset)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def update_engagement(db: Session, engagement_id: str, payload: EngagementUpdate) -> Engagement:
    engagement = get_engagement(db, engagement_id)
    if payload.deal_name is not None:
        engagement.deal_name = payload.deal_name
    if payload.current_step is not None:
        engagement.current_step = payload.current_step
    db.commit()
    db.refresh(engagement)
    return engagement


def archive_engagement(db: Session, engagement_id: str) -> None:
    engagement = get_engagement(db, engagement_id)
    engagement.status = EngagementStatus.archived.value
    db.commit()


def patch_intake_section(db: Session, engagement_id: str, section: str, data: dict[str, object]) -> Engagement:
    engagement = get_engagement(db, engagement_id)
    intake = engagement.intake
    column = SECTION_JSON_COLUMNS[section]

    existing = getattr(intake, column) or {}
    merged = {**existing, **data}
    setattr(intake, column, merged)

    if section == "context":
        deal_name = _as_str(merged.get("deal_name"))
        if deal_name:
            engagement.deal_name = deal_name

    _sync_denorm(engagement, section, merged)

    if engagement.status == EngagementStatus.draft.value:
        engagement.current_step = section

    db.commit()
    db.refresh(engagement)
    return engagement


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _sync_denorm(engagement: Engagement, section: str, merged: dict[str, object]) -> None:
    denorm = engagement.denorm
    if section == "target":
        denorm.company_name = _as_str(merged.get("company_name"))
        denorm.sector = _as_str(merged.get("sector"))
        denorm.digital_maturity = _as_str(merged.get("digital_maturity"))
    elif section == "structure":
        denorm.investment_type = _as_str(merged.get("investment_type"))
        denorm.stake = _as_str(merged.get("stake"))
    elif section == "objectives":
        preference = _as_str(merged.get("dd_type_preference"))
        if preference and preference in _DD_TYPE_VALUE_MAP:
            denorm.dd_type = _DD_TYPE_VALUE_MAP[preference]
        elif preference == DdTypePreference.let_platform_decide.value:
            denorm.dd_type = None
            denorm.dd_mix = None


def assemble_intake_full(engagement: Engagement) -> IntakeFull:
    intake = engagement.intake
    field_errors: list[dict[str, str]] = []
    section_values: dict[str, object] = {}

    for section in INTAKE_STEP_ORDER:
        column = SECTION_JSON_COLUMNS[section]
        raw = getattr(intake, column) or {}
        model_cls = SECTION_REQUIRED_MODELS[section]
        try:
            section_values[section] = model_cls.model_validate(raw)
        except ValidationError as exc:
            for error in exc.errors():
                loc = ".".join(str(part) for part in error["loc"])
                field_errors.append({"field": f"{section}.{loc}", "message": error["msg"]})

    if field_errors:
        raise AppError(
            code="incomplete_intake",
            message="The intake is missing required fields",
            status_code=422,
            field_errors=field_errors,
        )

    return IntakeFull.model_validate(section_values)


def submit_engagement(db: Session, engagement_id: str) -> Engagement:
    engagement = get_engagement(db, engagement_id)
    assemble_intake_full(engagement)  # raises AppError with field_errors if incomplete

    engagement.status = EngagementStatus.filed.value
    engagement.filed_at = datetime.now(UTC).isoformat()
    db.commit()
    db.refresh(engagement)
    return engagement
