from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.irl import InformationRequestList
from app.schemas.irl import (
    GenerateIrlRequest,
    IrlRead,
    IrlResponseUpdate,
    IrlVersionSummary,
)
from app.services.engagements import get_engagement
from app.services.irl import service as irl_service
from app.services.irl.export_xlsx import render_xlsx_from_payload, xlsx_filename

router = APIRouter(prefix="/engagements/{engagement_id}/irl", tags=["irl"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _to_read(irl: InformationRequestList) -> IrlRead:
    return IrlRead.model_validate(
        {
            "id": irl.id,
            "engagement_id": irl.engagement_id,
            "version": irl.version,
            "generator": irl.generator,
            "source_scope_version": irl.source_scope_version,
            "payload": irl.payload_json,
            "responses": irl_service.responses_for(irl),
            "created_at": irl.created_at,
        }
    )


@router.post("", response_model=IrlRead)
def generate_irl(
    engagement_id: str,
    payload: GenerateIrlRequest | None = None,
    db: Session = Depends(get_db),
) -> IrlRead:
    """Build a request list from the latest scope. 409 if no scope exists yet."""
    request = payload or GenerateIrlRequest()
    return _to_read(irl_service.generate_irl(db, engagement_id, request.generator))


@router.get("", response_model=IrlRead)
def get_latest_irl(engagement_id: str, db: Session = Depends(get_db)) -> IrlRead:
    return _to_read(irl_service.get_latest_irl(db, engagement_id))


@router.get("/versions", response_model=list[IrlVersionSummary])
def list_irl_versions(
    engagement_id: str, db: Session = Depends(get_db)
) -> list[IrlVersionSummary]:
    versions = irl_service.list_irl_versions(db, engagement_id)
    return [IrlVersionSummary.model_validate(v) for v in versions]


# Declared BEFORE /{version}: FastAPI matches in declaration order, and "export.xlsx"
# would otherwise be captured by the version path parameter.
@router.get("/export.xlsx")
def export_irl_xlsx(engagement_id: str, db: Session = Depends(get_db)) -> Response:
    """The request list as an Excel workbook: Function | Question | Response.

    Response is the column the target fills in. Anything already answered in the app is
    written into it, so the workbook round-trips.
    """
    engagement = get_engagement(db, engagement_id)
    irl = irl_service.get_latest_irl(db, engagement_id)

    workbook = render_xlsx_from_payload(irl.payload_json, irl_service.responses_for(irl))
    filename = xlsx_filename(engagement.deal_name, irl.version)

    return Response(
        content=workbook,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/responses/{question_id}", response_model=IrlRead)
def save_irl_response(
    engagement_id: str,
    question_id: str,
    payload: IrlResponseUpdate,
    db: Session = Depends(get_db),
) -> IrlRead:
    """Save one answer against the latest version. An empty string clears it."""
    return _to_read(
        irl_service.save_response(db, engagement_id, question_id, payload.response_text)
    )


@router.get("/{version}", response_model=IrlRead)
def get_irl_version(
    engagement_id: str, version: int, db: Session = Depends(get_db)
) -> IrlRead:
    return _to_read(irl_service.get_irl_version(db, engagement_id, version))
