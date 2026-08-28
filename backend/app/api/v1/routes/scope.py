from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scope_of_work import ScopeOfWork
from app.schemas.scope import ScopeOfWorkRead, ScopeOfWorkVersionSummary
from app.services.scope import service as scope_service

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
def generate_scope(engagement_id: str, db: Session = Depends(get_db)) -> ScopeOfWorkRead:
    return _to_read(scope_service.generate_scope(db, engagement_id))


@router.get("", response_model=ScopeOfWorkRead)
def get_latest_scope(engagement_id: str, db: Session = Depends(get_db)) -> ScopeOfWorkRead:
    return _to_read(scope_service.get_latest_scope(db, engagement_id))


@router.get("/versions", response_model=list[ScopeOfWorkVersionSummary])
def list_scope_versions(engagement_id: str, db: Session = Depends(get_db)) -> list[ScopeOfWorkVersionSummary]:
    versions = scope_service.list_scope_versions(db, engagement_id)
    return [ScopeOfWorkVersionSummary.model_validate(v) for v in versions]
