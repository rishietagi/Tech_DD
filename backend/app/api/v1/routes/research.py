from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.research import CompanyResearch
from app.schemas.research import ResearchEdit, ResearchPayload, ResearchRead, ResearchVersionSummary
from app.services.engagements import get_engagement
from app.services.research import service as research_service
from app.services.research.export_docx import docx_filename, render

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

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


@router.get("/export.docx")
def export_research(engagement_id: str, db: Session = Depends(get_db)) -> Response:
    """The latest research brief, edits included, as a Word document."""
    engagement = get_engagement(db, engagement_id)
    research = research_service.get_latest_research(db, engagement_id)
    content = render(
        ResearchPayload.model_validate(research.payload_json),
        deal_name=engagement.deal_name,
        company_name=research.company_name or "",
        version=research.version,
    )
    return Response(
        content=content,
        media_type=DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{docx_filename(engagement.deal_name)}"'},
    )


@router.get("/versions", response_model=list[ResearchVersionSummary])
def list_research_versions(
    engagement_id: str, db: Session = Depends(get_db)
) -> list[ResearchVersionSummary]:
    versions = research_service.list_research_versions(db, engagement_id)
    return [ResearchVersionSummary.model_validate(v) for v in versions]


@router.put("", response_model=ResearchRead)
def edit_research(
    engagement_id: str, payload: ResearchEdit, db: Session = Depends(get_db)
) -> ResearchRead:
    """Write the research by hand (AI off), or correct the latest run before it is used.

    The text a hand edit replaced is kept in `human_edits`.
    """
    return _to_read(research_service.save_research_edit(db, engagement_id, payload))
