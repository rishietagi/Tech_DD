from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.research import CompanyResearch
from app.schemas.research import ResearchRead, ResearchVersionSummary
from app.services.research import service as research_service

router = APIRouter(prefix="/engagements/{engagement_id}/research", tags=["research"])


def _to_read(research: CompanyResearch) -> ResearchRead:
    return ResearchRead.model_validate(
        {
            "id": research.id,
            "engagement_id": research.engagement_id,
            "version": research.version,
            "generator": research.generator,
            "company_name": research.company_name,
            "payload": research.payload_json,
            "created_at": research.created_at,
        }
    )


@router.post("", response_model=ResearchRead)
def run_research(engagement_id: str, db: Session = Depends(get_db)) -> ResearchRead:
    """Research the target against live web sources and store the run.

    503 when the capability is switched off (no API key); 422 when the model answered
    but the answer could not be grounded in real sources.
    """
    return _to_read(research_service.run_research(db, engagement_id))


@router.get("", response_model=ResearchRead)
def get_latest_research(engagement_id: str, db: Session = Depends(get_db)) -> ResearchRead:
    return _to_read(research_service.get_latest_research(db, engagement_id))


@router.get("/versions", response_model=list[ResearchVersionSummary])
def list_research_versions(
    engagement_id: str, db: Session = Depends(get_db)
) -> list[ResearchVersionSummary]:
    versions = research_service.list_research_versions(db, engagement_id)
    return [ResearchVersionSummary.model_validate(v) for v in versions]
