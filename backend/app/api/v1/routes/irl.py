from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models.irl import InformationRequestList
from app.schemas.irl import (
    GenerateIrlRequest,
    ImportResponsesResult,
    IrlQuestionCreate,
    IrlQuestionUpdate,
    IrlRead,
    IrlResponseUpdate,
    IrlTrackingUpdate,
    IrlVersionSummary,
)
from app.services.engagements import get_engagement
from app.services.irl import service as irl_service
from app.services.irl.export_xlsx import render_xlsx_from_payload, xlsx_filename

router = APIRouter(prefix="/engagements/{engagement_id}/irl", tags=["irl"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _to_read(irl: InformationRequestList, db: Session | None = None) -> IrlRead:
    """The list, its responses, and (when a session is given) its tracking.

    `db` is optional so the read stays cheap where tracking is not wanted; every route
    that renders the table passes it, because the IRL screen now shows status and remarks
    inline rather than sending the analyst to a second page.
    """
    return IrlRead.model_validate(
        {
            "id": irl.id,
            "engagement_id": irl.engagement_id,
            "version": irl.version,
            "generator": irl.generator,
            "source_scope_version": irl.source_scope_version,
            "payload": irl.payload_json,
            "responses": irl_service.responses_for(irl),
            "tracking": (
                irl_service.tracking_for(db, irl.engagement_id, irl) if db is not None else {}
            ),
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
    return _to_read(irl_service.generate_irl(db, engagement_id, request.generator), db)


@router.get("", response_model=IrlRead)
def get_latest_irl(engagement_id: str, db: Session = Depends(get_db)) -> IrlRead:
    return _to_read(irl_service.get_latest_irl(db, engagement_id), db)


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
        irl_service.save_response(db, engagement_id, question_id, payload.response_text),
        db,
    )


# ------------------------------------------------------- hand-editing (2026-09-02)
#
# All declared BEFORE /{version}, which would otherwise capture "questions" and "import"
# as a version number — the same ordering trap already recorded for export.pdf.


@router.post("/questions", response_model=IrlRead)
def add_irl_question(
    engagement_id: str,
    payload: IrlQuestionCreate,
    db: Session = Depends(get_db),
) -> IrlRead:
    """Add a request the generated list did not anticipate."""
    return _to_read(
        irl_service.add_question(
            db, engagement_id, payload.question, payload.function, payload.scope_area
        ),
        db,
    )


@router.patch("/questions/{question_id}", response_model=IrlRead)
def update_irl_question(
    engagement_id: str,
    question_id: str,
    payload: IrlQuestionUpdate,
    db: Session = Depends(get_db),
) -> IrlRead:
    """Reword a request, or move it to a different function or scope area.

    The engine's original wording is kept beside the edit, so a reviewer can always see
    what was changed.
    """
    return _to_read(
        irl_service.update_question(
            db,
            engagement_id,
            question_id,
            question=payload.question,
            function=payload.function,
            scope_area=payload.scope_area,
        ),
        db,
    )


@router.delete("/questions/{question_id}", response_model=IrlRead)
def delete_irl_question(
    engagement_id: str, question_id: str, db: Session = Depends(get_db)
) -> IrlRead:
    """Remove a request. Its response and document status go with it."""
    return _to_read(irl_service.delete_question(db, engagement_id, question_id), db)


@router.post("/import", response_model=ImportResponsesResult)
def import_irl_responses(
    engagement_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportResponsesResult:
    """Upload a completed workbook and scrape its Response column.

    Matches on the hidden Request ID column, falling back to exact question text. Blank
    cells never clear an existing answer, and unmatched rows are reported rather than
    silently dropped.
    """
    content = file.file.read()
    if not content:
        raise AppError(
            code="empty_upload",
            message="The uploaded file is empty.",
            status_code=400,
        )

    _, result = irl_service.import_responses_from_workbook(db, engagement_id, content)
    return result


@router.patch("/tracking/{question_id}", response_model=IrlRead)
def save_irl_tracking(
    engagement_id: str,
    question_id: str,
    payload: IrlTrackingUpdate,
    db: Session = Depends(get_db),
) -> IrlRead:
    """Record what the deal team observes about one request's document.

    Status, document type and remarks, set from the IRL screen. None of this reaches the
    client workbook — it is the team's own assessment of what has arrived.
    """
    irl = irl_service.save_tracking(
        db,
        engagement_id,
        question_id,
        status=payload.status,
        document_type=payload.document_type,
        remarks=payload.remarks,
    )
    return _to_read(irl, db)


@router.get("/{version}", response_model=IrlRead)
def get_irl_version(
    engagement_id: str, version: int, db: Session = Depends(get_db)
) -> IrlRead:
    return _to_read(irl_service.get_irl_version(db, engagement_id, version))
