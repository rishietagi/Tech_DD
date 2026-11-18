from typing import Any

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.estate import (
    EstateAnswerWrite,
    EstateRead,
    EstateScoreRead,
    GapNoteWrite,
    InventoryImportResult,
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    InventoryKind,
    InventoryRead,
)
from app.services.engagements import get_engagement
from app.services.estate import inventory as inventory_service
from app.services.estate import service as estate_service
from app.services.estate.inventory_xlsx import render_template
from app.services.irl.export_xlsx import xlsx_filename

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

inventory_router = APIRouter(prefix="/engagements/{engagement_id}/inventory", tags=["inventory"])
estate_router = APIRouter(prefix="/engagements/{engagement_id}/estate", tags=["estate"])


# ======================================================================= inventory


@inventory_router.get("", response_model=InventoryRead)
def list_inventory(
    engagement_id: str,
    kind: InventoryKind | None = Query(default=None),
    db: Session = Depends(get_db),
) -> InventoryRead:
    """Field definitions, the processes an application can support, and the items."""
    return inventory_service.list_inventory(db, engagement_id, kind)


@inventory_router.post("", response_model=InventoryItemRead, status_code=201)
def create_item(engagement_id: str, payload: InventoryItemCreate, db: Session = Depends(get_db)) -> InventoryItemRead:
    item = inventory_service.create_item(db, engagement_id, payload.kind, payload.fields)
    return inventory_service.item_to_read(item)


# Declared before `/{item_id}` so `template.xlsx` and `import` are never read as an id.
@inventory_router.get("/{kind}/template.xlsx")
def download_template(engagement_id: str, kind: InventoryKind, db: Session = Depends(get_db)) -> Response:
    """One inventory as a workbook, pre-filled with what is already recorded."""
    engagement = get_engagement(db, engagement_id)
    content = render_template(kind, inventory_service.items_of(db, engagement_id), inventory_service.process_refs())
    stem = xlsx_filename(engagement.deal_name, 1).replace("-irl-v1.xlsx", "")
    filename = f"{stem}-{kind.replace('_', '-')}-inventory.xlsx"
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@inventory_router.post("/{kind}/import", response_model=InventoryImportResult)
def import_inventory(
    engagement_id: str,
    kind: InventoryKind,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> InventoryImportResult:
    """Create or update items from a returned template. Never clears a value."""
    content = file.file.read()
    if not content:
        raise AppError(code="empty_upload", message="The uploaded file is empty.", status_code=400)
    # A data-domain or platform template also carries the application sheet, so the
    # applications in it are applied too — an ID the target added there must resolve.
    kinds: tuple[InventoryKind, ...] = (kind,) if kind == "application" else ("application", kind)
    return inventory_service.import_workbook(db, engagement_id, content, kinds)


@inventory_router.patch("/{item_id}", response_model=InventoryItemRead)
def update_item(
    engagement_id: str, item_id: str, payload: InventoryItemUpdate, db: Session = Depends(get_db)
) -> InventoryItemRead:
    item = inventory_service.update_item(db, engagement_id, item_id, payload.fields)
    return inventory_service.item_to_read(item)


@inventory_router.delete("/{item_id}", status_code=204)
def delete_item(engagement_id: str, item_id: str, db: Session = Depends(get_db)) -> Response:
    inventory_service.delete_item(db, engagement_id, item_id)
    return Response(status_code=204)


# ======================================================================= estate assessment


class ScoreRequest(BaseModel):
    model_config = {"extra": "forbid"}

    generator: str | None = None


@estate_router.get("/summary")
def estate_summary(engagement_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Headline per assessment for the Assess index."""
    return estate_service.summaries(db, engagement_id)


@estate_router.get("/{domain}", response_model=EstateRead)
def get_estate(engagement_id: str, domain: str, db: Session = Depends(get_db)) -> EstateRead:
    """Subjects, their questions, and every answer recorded."""
    return estate_service.get_estate(db, engagement_id, domain)


@estate_router.patch("/{domain}/answers", response_model=EstateRead)
def save_answer(
    engagement_id: str, domain: str, payload: EstateAnswerWrite, db: Session = Depends(get_db)
) -> EstateRead:
    """One answer and/or its remarks. `null` leaves a field alone; "" clears it."""
    return estate_service.save_answer(db, engagement_id, domain, payload)


@estate_router.post("/{domain}/score", response_model=EstateScoreRead)
def generate_score(
    engagement_id: str,
    domain: str,
    payload: ScoreRequest | None = None,
    db: Session = Depends(get_db),
) -> EstateScoreRead:
    """Score the answers and the inventory, and store a new version with its gap register."""
    request = payload or ScoreRequest()
    row = estate_service.generate_score(db, engagement_id, domain, request.generator)
    return estate_service.to_read(db, row)


@estate_router.get("/{domain}/score", response_model=EstateScoreRead)
def get_score(engagement_id: str, domain: str, db: Session = Depends(get_db)) -> EstateScoreRead:
    """The latest score with consultant edits overlaid. 404 `no_score` before the first."""
    return estate_service.get_latest_score(db, engagement_id, domain)


@estate_router.patch("/{domain}/gaps/{gap_key}", response_model=EstateScoreRead)
def edit_gap(
    engagement_id: str,
    domain: str,
    gap_key: str,
    payload: GapNoteWrite,
    db: Session = Depends(get_db),
) -> EstateScoreRead:
    """Overlay a consultant's edit. It survives re-scoring."""
    return estate_service.save_gap_note(db, engagement_id, domain, gap_key, payload)


@estate_router.delete("/{domain}/gaps/{gap_key}", response_model=EstateScoreRead)
def revert_gap(engagement_id: str, domain: str, gap_key: str, db: Session = Depends(get_db)) -> EstateScoreRead:
    """Drop the edit and show the generated text again."""
    return estate_service.delete_gap_note(db, engagement_id, domain, gap_key)
