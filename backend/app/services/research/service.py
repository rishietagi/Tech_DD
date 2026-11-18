"""Persistence for company research. Versioned, never destructive.

Mirrors `services/scope/service.py`: a run is stored as a new version, prior runs are
kept, and the latest is what the UI reads. Research costs an API call against a small
quota, so it is fetched once and stored — not re-run on every page view.
"""

import copy
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.errors import AppError
from app.models.research import CompanyResearch
from app.schemas.research import BusinessBrief, ResearchEdit, ResearchPayload
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.intelligence.mode import use_llm
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

    # Research has no rules version — facts about a company cannot be derived. With the
    # AI off it is entered by hand instead (POST /research/manual).
    if not use_llm("company-research"):
        raise AppError(
            code="research_unavailable",
            message=(
                "Web research needs the AI, which is off (AI_MODE=off or no key). "
                "Write the research brief by hand instead."
            ),
            status_code=503,
        )

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


_BRIEF_SECTIONS = tuple(BusinessBrief.model_fields)
_CATEGORIES = {"overview", "financial", "technology", "incident", "regulatory", "market", "people", "other"}


def save_research_edit(db: Session, engagement_id: str, edit: ResearchEdit) -> CompanyResearch:
    """Write the research by hand, or correct the latest run in place.

    No run yet → a new `manual` version. Otherwise the latest version is edited and the
    text it replaced is kept in `human_edits` the first time each field changes.
    """
    engagement = get_engagement(db, engagement_id)
    unknown = set(edit.business_brief or {}) - set(_BRIEF_SECTIONS)
    if unknown:
        raise AppError(
            code="validation_error",
            message=f"Unknown brief sections: {sorted(unknown)}",
            status_code=422,
        )

    latest = find_latest_research(db, engagement_id)
    if latest is None:
        intake = assemble_intake_full(engagement)
        payload = ResearchPayload(
            generator="manual",
            company_name=intake.target.company_name,
            summary="",
            business_brief=BusinessBrief(),
            researched_at=datetime.now(UTC),
        ).model_dump(mode="json")
        latest = CompanyResearch(
            engagement_id=engagement_id,
            version=1,
            generator="manual",
            company_name=intake.target.company_name,
            payload_json=payload,
        )
        db.add(latest)
        db.flush()

    data: dict[str, Any] = copy.deepcopy(latest.payload_json)
    originals = data.setdefault("human_edits", {})

    if edit.summary is not None:
        originals.setdefault("summary", data.get("summary", ""))
        data["summary"] = edit.summary.strip()
    if edit.business_brief is not None:
        brief = data.get("business_brief") or BusinessBrief().model_dump(mode="json")
        for section, text in edit.business_brief.items():
            current = brief.get(section) or {"text": "", "source_ids": []}
            originals.setdefault(f"brief.{section}", current.get("text", ""))
            brief[section] = {**current, "text": text.strip()}
        data["business_brief"] = brief
    if edit.findings is not None:
        originals.setdefault("findings", copy.deepcopy(data.get("findings", [])))
        previous = {f.get("topic"): f for f in data.get("findings", [])}
        data["findings"] = [
            {
                "topic": f.topic.strip(),
                "detail": f.detail.strip(),
                "category": f.category if f.category in _CATEGORIES else "other",
                # A finding kept unchanged keeps its sources; a new or rewritten one has none.
                "source_ids": previous.get(f.topic, {}).get("source_ids", [])
                if previous.get(f.topic, {}).get("detail") == f.detail
                else [],
            }
            for f in edit.findings
        ]

    latest.payload_json = data
    flag_modified(latest, "payload_json")
    db.commit()
    db.refresh(latest)
    return latest
