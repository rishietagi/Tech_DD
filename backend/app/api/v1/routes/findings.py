"""Findings exports: every Assess register together, or one tab's (2026-11-19)."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.findings import registers
from app.services.findings.export_xlsx import findings_filename, render
from app.services.report.service import get_report_config

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

router = APIRouter(prefix="/engagements/{engagement_id}/findings", tags=["findings"])


def _workbook(db: Session, engagement_id: str, key: str | None) -> Response:
    engagement = get_engagement(db, engagement_id)
    try:
        target = assemble_intake_full(engagement).target.company_name or ""
    except Exception:  # noqa: BLE001 - a partial intake still exports its findings
        target = ""
    regs = registers.all_registers(db, engagement_id) if key is None else [registers.register(db, engagement_id, key)]
    title = "Assessment findings" if key is None else f"{registers.REGISTERS[key]} — findings"
    content = render(
        regs,
        deal_name=engagement.deal_name,
        target_name=target,
        area_titles={a.id: a.title for a in get_report_config().areas},
        title=title,
    )
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{findings_filename(engagement.deal_name, key)}"'},
    )


@router.get("/export.xlsx")
def export_all(engagement_id: str, db: Session = Depends(get_db)) -> Response:
    """Every assessment's score and findings in one workbook, edits applied."""
    return _workbook(db, engagement_id, None)


@router.get("/{register}/export.xlsx")
def export_one(engagement_id: str, register: str, db: Session = Depends(get_db)) -> Response:
    """One Assess tab's score and findings: business, applications, data_tech,
    team_governance, strategy_projects or it_budget."""
    if register not in registers.REGISTERS:
        raise AppError(
            code="unknown_register",
            message=f"No findings register called {register!r}.",
            status_code=404,
        )
    return _workbook(db, engagement_id, register)
