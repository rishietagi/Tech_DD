import copy
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.scope_of_work import ScopeOfWork
from app.schemas.scope_api import ScopePreviewResponse, WorkstreamOverrideRequest
from app.schemas.selection import TIER_NAMES
from app.services.engagements import (
    assemble_intake_draft,
    assemble_intake_full,
    get_engagement,
)
from app.services.scope.depth import calibrate_depth
from app.services.scope.factory import get_scope_generator, resolve_generator_name
from app.services.scope.scoring import classify
from app.services.scope.selection import select_rows
from app.services.scope.signals import extract_signals


def generate_scope(
    db: Session,
    engagement_id: str,
    generator_name: str | None = None,
) -> ScopeOfWork:
    engagement = get_engagement(db, engagement_id)
    if engagement.status not in ("filed", "scoped"):
        raise AppError(
            code="not_filed",
            message="Engagement must be filed before a scope can be generated",
            status_code=409,
        )

    settings = get_settings()
    if generator_name:
        settings = settings.model_copy(update={"scope_generator": generator_name})

    intake = assemble_intake_full(engagement)
    generator = get_scope_generator(settings)
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
        # The payload knows what actually happened ("llm", or "rules (llm ...)"
        # when tailoring was rejected); the setting only says what was asked for.
        generator=getattr(payload, "generator", None) or resolve_generator_name(settings),
        dd_type=payload.dd_type.value if payload.dd_type else None,
        dd_mix=payload.dd_mix,
        payload_json=payload.model_dump(mode="json"),
    )
    db.add(scope)
    engagement.status = "scoped"

    # The engine's verdict is the best answer available, so lift it onto the denorm
    # for listing and filtering.
    if engagement.denorm and payload.dd_type:
        engagement.denorm.dd_type = payload.dd_type.value
        engagement.denorm.dd_mix = payload.dd_mix

    db.commit()
    db.refresh(scope)
    return scope


def preview_scope(db: Session, engagement_id: str) -> ScopePreviewResponse:
    """Classification only, from a draft intake. Must never raise on incompleteness."""
    engagement = get_engagement(db, engagement_id)
    intake, is_complete = assemble_intake_draft(engagement)

    signals = extract_signals(intake)
    classification = classify(intake, signals)
    rows = select_rows(intake, classification, signals)
    rows, _, _ = calibrate_depth(rows, intake, classification, signals)

    return ScopePreviewResponse(
        classification=classification,
        row_count=len([r for r in rows if r.in_scope]),
        deck=classification.dd_type.value,
        is_complete=is_complete,
    )


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


def get_scope_version(db: Session, engagement_id: str, version: int) -> ScopeOfWork:
    get_engagement(db, engagement_id)
    scope = db.execute(
        select(ScopeOfWork).where(
            ScopeOfWork.engagement_id == engagement_id, ScopeOfWork.version == version
        )
    ).scalar_one_or_none()
    if scope is None:
        raise AppError(
            code="no_scope_version",
            message=f"Version {version} does not exist for this engagement",
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


def override_scope_row(
    db: Session,
    engagement_id: str,
    version: int,
    row_id: str,
    payload: WorkstreamOverrideRequest,
) -> ScopeOfWork:
    """Apply a human edit to one row.

    DD_master G6: the human overrides the engine. The engine's original values are
    preserved on the row rather than replaced, so the edit stays visible as an edit.
    """
    scope = get_scope_version(db, engagement_id, version)
    # A deep copy is required: a shallow dict() shares the nested row dicts with the
    # loaded value, so mutating a row would edit the original in place and SQLAlchemy
    # would see an unchanged column and silently discard the write.
    data: dict[str, Any] = copy.deepcopy(scope.payload_json)

    if data.get("schema_version") != 2:
        raise AppError(
            code="unsupported_scope_version",
            message="Only schema v2 scopes support row overrides",
            status_code=409,
        )

    rows = data.get("rows", [])
    target = next((r for r in rows if r["id"] == row_id), None)
    if target is None:
        raise AppError(
            code="row_not_found",
            message=f"Row {row_id} is not part of this scope",
            status_code=404,
        )

    if not target.get("edited_by_human"):
        target["original_tier"] = target["tier"]
        target["original_title"] = target["title"]

    if payload.tier is not None:
        target["tier"] = payload.tier
        target["tier_name"] = TIER_NAMES[payload.tier]
    if payload.title is not None:
        target["title"] = payload.title

    target["edited_by_human"] = True
    if payload.reason:
        target["override_reason"] = payload.reason
        target.setdefault("adjustments", []).append(f"human override: {payload.reason}")
    else:
        target.setdefault("adjustments", []).append("human override")

    # Reassign the fresh object and flag the column, so the change is persisted.
    scope.payload_json = data
    flag_modified(scope, "payload_json")
    db.commit()
    db.refresh(scope)
    return scope
