from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.report import ReportAssetRead, ReportEditWrite, ReportGenerateRequest, ReportRead
from app.services.engagements import get_engagement
from app.services.report import service as report_service
from app.services.report.export_pptx import filename, render

PPTX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

router = APIRouter(prefix="/engagements/{engagement_id}/report", tags=["report"])


@router.post("", response_model=ReportRead)
def generate_report(
    engagement_id: str,
    payload: ReportGenerateRequest | None = None,
    db: Session = Depends(get_db),
) -> ReportRead:
    """Build the report from every module and store a new version. Edits carry over."""
    row = report_service.generate(db, engagement_id, (payload or ReportGenerateRequest()).generator)
    return report_service.to_read(db, row)


@router.get("", response_model=ReportRead)
def get_report(engagement_id: str, db: Session = Depends(get_db)) -> ReportRead:
    """The latest version with every consultant edit applied. 404 `no_report` before the first."""
    return report_service.to_read(db, report_service.latest(db, engagement_id))


# Declared before `/elements/{key:path}` and `/assets/{id}` siblings for clarity; static
# paths win over path parameters in FastAPI regardless.
@router.get("/export.pptx")
def export_report(engagement_id: str, db: Session = Depends(get_db)) -> Response:
    """The report as PowerPoint, exactly as edited on screen."""
    engagement = get_engagement(db, engagement_id)
    row = report_service.latest(db, engagement_id)
    payload = report_service.with_edits(db, row)
    assets = {a.id: (a.mime, a.data) for a in report_service.list_assets(db, engagement_id)}
    return Response(
        content=render(payload, assets),
        media_type=PPTX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename(engagement.deal_name, row.version)}"'},
    )


@router.patch("/elements/{key}", response_model=ReportRead)
def edit_element(engagement_id: str, key: str, payload: ReportEditWrite, db: Session = Depends(get_db)) -> ReportRead:
    """Edit one element (`exec.EN-01.findings`, `context.approach`, `include` toggles…).

    Kept across regenerations for as long as the element exists.
    """
    return report_service.save_edit(db, engagement_id, key, payload.value)


@router.delete("/elements/{key}", response_model=ReportRead)
def revert_element(engagement_id: str, key: str, db: Session = Depends(get_db)) -> ReportRead:
    """Drop an edit and show the generated text again."""
    return report_service.revert_edit(db, engagement_id, key)


@router.get("/assets", response_model=list[ReportAssetRead])
def list_assets(engagement_id: str, db: Session = Depends(get_db)) -> list[ReportAssetRead]:
    return [
        ReportAssetRead(id=a.id, title=a.title, caption=a.caption, mime=a.mime, created_at=a.created_at)
        for a in report_service.list_assets(db, engagement_id)
    ]


@router.post("/assets", response_model=ReportAssetRead, status_code=201)
def upload_asset(
    engagement_id: str,
    file: UploadFile = File(...),
    title: str = Form(""),
    caption: str = Form(""),
    db: Session = Depends(get_db),
) -> ReportAssetRead:
    """A diagram the target supplied (network, infrastructure), for the appendix.

    Regenerate the report to place it — a new diagram also clears the data limitation that
    said none was provided.
    """
    data = file.file.read()
    if not data:
        raise AppError(code="empty_upload", message="The uploaded file is empty.", status_code=400)
    asset = report_service.add_asset(
        db, engagement_id, title or (file.filename or "Diagram"), caption, file.content_type or "", data
    )
    return ReportAssetRead(
        id=asset.id, title=asset.title, caption=asset.caption, mime=asset.mime, created_at=asset.created_at
    )


@router.get("/assets/{asset_id}")
def get_asset(engagement_id: str, asset_id: str, db: Session = Depends(get_db)) -> Response:
    asset = report_service.get_asset(db, engagement_id, asset_id)
    return Response(content=asset.data, media_type=asset.mime)


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(engagement_id: str, asset_id: str, db: Session = Depends(get_db)) -> Response:
    report_service.delete_asset(db, engagement_id, asset_id)
    return Response(status_code=204)
