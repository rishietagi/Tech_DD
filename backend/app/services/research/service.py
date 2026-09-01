"""Persistence for company research. Versioned, never destructive.

Mirrors `services/scope/service.py`: a run is stored as a new version, prior runs are
kept, and the latest is what the UI reads. Research costs an API call against a small
quota, so it is fetched once and stored — not re-run on every page view.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.research import CompanyResearch
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.research.generator import (
    CompanyResearcher,
    ResearchRejected,
    ResearchUnavailable,
)


def run_research(db: Session, engagement_id: str) -> CompanyResearch:
    """Research the target and store the result as a new version."""
    engagement = get_engagement(db, engagement_id)
    if engagement.status not in ("filed", "scoped"):
        raise AppError(
            code="not_filed",
            message="Engagement must be filed before its target can be researched",
            status_code=409,
        )

    intake = assemble_intake_full(engagement)

    try:
        payload = CompanyResearcher().research(intake)
    except ResearchUnavailable as exc:
        # 503: the capability is switched off or unreachable, not a bad request.
        raise AppError(code="research_unavailable", message=str(exc), status_code=503) from exc
    except ResearchRejected as exc:
        # 422: the model answered but the answer was unusable — most often no grounding.
        raise AppError(code="research_rejected", message=str(exc), status_code=422) from exc

    last_version = db.execute(
        select(CompanyResearch.version)
        .where(CompanyResearch.engagement_id == engagement_id)
        .order_by(CompanyResearch.version.desc())
        .limit(1)
    ).scalar()

    research = CompanyResearch(
        engagement_id=engagement_id,
        version=(last_version or 0) + 1,
        generator=payload.generator,
        company_name=payload.company_name,
        payload_json=payload.model_dump(mode="json"),
    )
    db.add(research)
    db.commit()
    db.refresh(research)
    return research


def get_latest_research(db: Session, engagement_id: str) -> CompanyResearch:
    get_engagement(db, engagement_id)
    research = db.execute(
        select(CompanyResearch)
        .where(CompanyResearch.engagement_id == engagement_id)
        .order_by(CompanyResearch.version.desc())
        .limit(1)
    ).scalar_one_or_none()
    if research is None:
        raise AppError(
            code="no_research",
            message="No research has been run for this engagement yet",
            status_code=404,
        )
    return research


def find_latest_research(db: Session, engagement_id: str) -> CompanyResearch | None:
    """Latest run, or None. For callers that want research if it exists.

    The IRL generator uses this: research makes the questions better, but its absence
    must not block generation.
    """
    return db.execute(
        select(CompanyResearch)
        .where(CompanyResearch.engagement_id == engagement_id)
        .order_by(CompanyResearch.version.desc())
        .limit(1)
    ).scalar_one_or_none()


def list_research_versions(db: Session, engagement_id: str) -> list[CompanyResearch]:
    get_engagement(db, engagement_id)
    return list(
        db.execute(
            select(CompanyResearch)
            .where(CompanyResearch.engagement_id == engagement_id)
            .order_by(CompanyResearch.version.desc())
        ).scalars()
    )
