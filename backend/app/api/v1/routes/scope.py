import re

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models.scope_of_work import ScopeOfWork
from app.schemas.scope import ScopeOfWorkRead, ScopeOfWorkVersionSummary
from app.schemas.scope_api import (
    GenerateScopeRequest,
    ScopePreviewResponse,
    WorkstreamOverrideRequest,
)
from app.services.engagements import get_engagement
from app.services.scope import service as scope_service
from app.services.scope.export import render_markdown_from_payload
from app.services.scope.export_pdf import pdf_filename, render_pdf_from_payload

router = APIRouter(prefix="/engagements/{engagement_id}/scope", tags=["scope"])


def _to_read(scope: ScopeOfWork) -> ScopeOfWorkRead:
    return ScopeOfWorkRead.model_validate(
        {
            "id": scope.id,
            "engagement_id": scope.engagement_id,
            "version": scope.version,
            "generator": scope.generator,
            "dd_type": scope.dd_type,
            "dd_mix": scope.dd_mix,
            "payload": scope.payload_json,
            "created_at": scope.created_at,
        }
    )


@router.post("", response_model=ScopeOfWorkRead)
def generate_scope(
    engagement_id: str,
    payload: GenerateScopeRequest | None = None,
    db: Session = Depends(get_db),
) -> ScopeOfWorkRead:
    request = payload or GenerateScopeRequest()
    return _to_read(scope_service.generate_scope(db, engagement_id, request.generator))


@router.post("/preview", response_model=ScopePreviewResponse)
def preview_scope(engagement_id: str, db: Session = Depends(get_db)) -> ScopePreviewResponse:
    """Classification from a draft intake. Tolerates an incomplete intake by design."""
    return scope_service.preview_scope(db, engagement_id)


@router.get("", response_model=ScopeOfWorkRead)
def get_latest_scope(engagement_id: str, db: Session = Depends(get_db)) -> ScopeOfWorkRead:
    return _to_read(scope_service.get_latest_scope(db, engagement_id))


@router.get("/versions", response_model=list[ScopeOfWorkVersionSummary])
def list_scope_versions(engagement_id: str, db: Session = Depends(get_db)) -> list[ScopeOfWorkVersionSummary]:
    versions = scope_service.list_scope_versions(db, engagement_id)
    return [ScopeOfWorkVersionSummary.model_validate(v) for v in versions]


@router.get("/export", response_class=PlainTextResponse)
def export_latest_scope(engagement_id: str, db: Session = Depends(get_db)) -> PlainTextResponse:
    """The latest scope as Markdown, as a file download."""
    engagement = get_engagement(db, engagement_id)
    scope = scope_service.get_latest_scope(db, engagement_id)

    try:
        markdown = render_markdown_from_payload(scope.payload_json, engagement.deal_name, scope.version)
    except ValueError as exc:
        raise AppError(code="not_exportable", message=str(exc), status_code=409) from exc

    slug = re.sub(r"[^a-z0-9]+", "-", engagement.deal_name.lower()).strip("-") or "scope"
    filename = f"{slug}-scope-v{scope.version}.md"
    return PlainTextResponse(
        markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Declared BEFORE /{version}: FastAPI matches in declaration order, and "export.pdf"
# would otherwise be captured by the version path parameter.
@router.get("/export.pdf")
def export_latest_scope_pdf(engagement_id: str, db: Session = Depends(get_db)) -> Response:
    """The latest scope as a client-facing PDF, as a file download.

    Narrower than the Markdown export by design: the internal audit trail (signals,
    rule provenance) is omitted. See `services/scope/export_pdf.py`.
    """
    engagement = get_engagement(db, engagement_id)
    scope = scope_service.get_latest_scope(db, engagement_id)

    try:
        pdf = render_pdf_from_payload(scope.payload_json, engagement.deal_name, scope.version)
    except ValueError as exc:
        raise AppError(code="not_exportable", message=str(exc), status_code=409) from exc

    filename = pdf_filename(engagement.deal_name, scope.version)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{version}", response_model=ScopeOfWorkRead)
def get_scope_version(engagement_id: str, version: int, db: Session = Depends(get_db)) -> ScopeOfWorkRead:
    return _to_read(scope_service.get_scope_version(db, engagement_id, version))


@router.patch("/{version}/rows/{row_id}", response_model=ScopeOfWorkRead)
def override_scope_row(
    engagement_id: str,
    version: int,
    row_id: str,
    payload: WorkstreamOverrideRequest,
    db: Session = Depends(get_db),
) -> ScopeOfWorkRead:
    """Human tier or title override on one row. The engine's original is preserved."""
    return _to_read(scope_service.override_scope_row(db, engagement_id, version, row_id, payload))
