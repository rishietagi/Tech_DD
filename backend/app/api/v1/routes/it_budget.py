from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.it_budget import ItBudgetInputs, ItBudgetRead
from app.services.estate import budget as budget_service

router = APIRouter(prefix="/engagements/{engagement_id}/it-budget", tags=["it-budget"])


@router.get("", response_model=ItBudgetRead)
def get_it_budget(engagement_id: str, db: Session = Depends(get_db)) -> ItBudgetRead:
    """Inputs (defaults until first saved), the questions, and the computed review."""
    return budget_service.get_budget(db, engagement_id)


@router.put("", response_model=ItBudgetRead)
def save_it_budget(engagement_id: str, payload: ItBudgetInputs, db: Session = Depends(get_db)) -> ItBudgetRead:
    """Replace the inputs whole and return the recomputed review."""
    return budget_service.save_budget(db, engagement_id, payload)
