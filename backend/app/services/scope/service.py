from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.scope_of_work import ScopeOfWork
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.scope.factory import get_scope_generator, resolve_generator_name


def generate_scope(db: Session, engagement_id: str) -> ScopeOfWork:
    engagement = get_engagement(db, engagement_id)
    if engagement.status not in ("filed", "scoped"):
        raise AppError(
            code="not_filed",
            message="Engagement must be filed before a scope can be generated",
            status_code=409,
        )

    intake = assemble_intake_full(engagement)
    generator = get_scope_generator(get_settings())
    payload = generator.generate(intake)

    last_version = db.execute(
        select(ScopeOfWork.version)
        .where(ScopeOfWork.engagement_id == engagement_id)
        .order_by(ScopeOfWork.version.desc())
        .limit(1)
    ).scalar()
    next_version = (last_version or 0) + 1

    scope = ScopeOfWork(
        engagement_id=engagement_id,
        version=next_version,
        generator=resolve_generator_name(get_settings()),
        dd_type=payload.dd_type,
        dd_mix=payload.dd_mix,
        payload_json=payload.model_dump(mode="json"),
    )
    db.add(scope)

    engagement.status = "scoped"

    db.commit()
    db.refresh(scope)
    return scope


def get_latest_scope(db: Session, engagement_id: str) -> ScopeOfWork:
    get_engagement(db, engagement_id)
    scope = db.execute(
        select(ScopeOfWork)
        .where(ScopeOfWork.engagement_id == engagement_id)
        .order_by(ScopeOfWork.version.desc())
        .limit(1)
    ).scalar_one_or_none()
    if scope is None:
        raise AppError(
            code="no_scope",
            message="No scope has been generated for this engagement yet",
            status_code=404,
        )
    return scope


def list_scope_versions(db: Session, engagement_id: str) -> list[ScopeOfWork]:
    get_engagement(db, engagement_id)
    return list(
        db.execute(
            select(ScopeOfWork).where(ScopeOfWork.engagement_id == engagement_id).order_by(ScopeOfWork.version.desc())
        ).scalars()
    )
