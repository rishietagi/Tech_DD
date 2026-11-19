from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.estate import GapNoteWrite
from app.schemas.it_budget import FinancialsImportResult, ItBudgetInputs, ItBudgetRead
from app.services.engagements import get_engagement
from app.services.estate import budget as budget_service
from app.services.estate import budget_xlsx
from app.services.irl.export_xlsx import xlsx_filename

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

router = APIRouter(prefix="/engagements/{engagement_id}/it-budget", tags=["it-budget"])


@router.get("", response_model=ItBudgetRead)
def get_it_budget(engagement_id: str, db: Session = Depends(get_db)) -> ItBudgetRead:
    """Inputs (defaults until first saved), the questions, and the computed review."""
    return budget_service.get_budget(db, engagement_id)


@router.put("", response_model=ItBudgetRead)
def save_it_budget(engagement_id: str, payload: ItBudgetInputs, db: Session = Depends(get_db)) -> ItBudgetRead:
    """Replace the inputs whole and return the recomputed review."""
    return budget_service.save_budget(db, engagement_id, payload)


@router.patch("/gaps/{gap_key}", response_model=ItBudgetRead)
def edit_gap(engagement_id: str, gap_key: str, payload: GapNoteWrite, db: Session = Depends(get_db)) -> ItBudgetRead:
    """Edit one budget finding. Kept across every recomputation of the review."""
    return budget_service.save_gap_note(db, engagement_id, gap_key, payload)


@router.delete("/gaps/{gap_key}", response_model=ItBudgetRead)
def revert_gap(engagement_id: str, gap_key: str, db: Session = Depends(get_db)) -> ItBudgetRead:
    return budget_service.delete_gap_note(db, engagement_id, gap_key)


@router.get("/template.xlsx")
def download_financials_template(engagement_id: str, db: Session = Depends(get_db)) -> Response:
    """The IT financials sheet on its own, pre-filled with what is recorded."""
    engagement = get_engagement(db, engagement_id)
    content = budget_xlsx.render_template(budget_service.get_budget(db, engagement_id).inputs)
    stem = xlsx_filename(engagement.deal_name, 1).replace("-irl-v1.xlsx", "")
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{stem}-it-financials.xlsx"'},
    )


@router.post("/import", response_model=FinancialsImportResult)
def import_financials(
    engagement_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> FinancialsImportResult:
    """Fill the budget from a returned IT financials sheet. Never clears a figure."""
    content = file.file.read()
    if not content:
        raise AppError(code="empty_upload", message="The uploaded file is empty.", status_code=400)
    get_engagement(db, engagement_id)
    result = budget_xlsx.import_financials(db, engagement_id, content)
    if result is None:
        raise AppError(
            code="import_failed",
            message=f"No '{budget_xlsx.SHEET}' sheet with year columns was found in that workbook.",
            status_code=400,
        )
    return result
