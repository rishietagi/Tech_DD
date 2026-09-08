from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assess import ProcessAssessmentScore
from app.schemas.assess import (
    AnswerWrite,
    AssessmentRead,
    AssessmentScoreRead,
    CustomQuestionCreate,
    ProcessListResponse,
    ScoreVersionSummary,
)
from app.services.assess import service as assess_service

router = APIRouter(prefix="/engagements/{engagement_id}/assess", tags=["assess"])


class GenerateScoreRequest(BaseModel):
    """Optional generator override, matching the scope and IRL endpoints."""

    model_config = {"extra": "forbid"}

    generator: str | None = None


def _to_read(row: ProcessAssessmentScore) -> AssessmentScoreRead:
    return AssessmentScoreRead.model_validate(
        {
            "id": row.id,
            "engagement_id": row.engagement_id,
            "process_key": row.process_key,
            "version": row.version,
            "generator": row.generator,
            "payload": row.payload_json,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    )


@router.get("/processes", response_model=ProcessListResponse)
def list_processes(engagement_id: str, db: Session = Depends(get_db)) -> ProcessListResponse:
    """Every business process, with progress against the ones that are defined.

    The four undefined processes are listed rather than hidden, so the shape of the
    module is visible; each carries `defined: false` and no counts.
    """
    return assess_service.list_processes(db, engagement_id)


@router.get("/{process_key}", response_model=AssessmentRead)
def get_assessment(
    engagement_id: str, process_key: str, db: Session = Depends(get_db)
) -> AssessmentRead:
    """The questionnaire and every answer recorded against it.

    409 `process_not_defined` for a process that is named but has no questionnaire yet —
    not a 404, which would wrongly imply the process does not exist.
    """
    return assess_service.get_assessment(db, engagement_id, process_key)


@router.patch("/{process_key}/answers/{question_id}", response_model=AssessmentRead)
def save_answer(
    engagement_id: str,
    process_key: str,
    question_id: str,
    payload: AnswerWrite,
    db: Session = Depends(get_db),
) -> AssessmentRead:
    """Record one answer and/or its remarks.

    Both fields are optional: `null` leaves that field alone, an empty string clears it.
    The option and the remark are edited by separate controls, so saving one must never
    wipe the other.

    Returns the whole assessment so the caller's progress count stays consistent with the
    answer it just wrote.
    """
    return assess_service.save_answer(
        db, engagement_id, process_key, question_id, payload.value, payload.remarks
    )


@router.post("/{process_key}/questions", response_model=AssessmentRead)
def add_custom_question(
    engagement_id: str,
    process_key: str,
    payload: CustomQuestionCreate,
    db: Session = Depends(get_db),
) -> AssessmentRead:
    """Add a question the questionnaire did not anticipate, under a named step.

    Custom questions capture evidence but never score: they have no options and no place
    on the maturity ladder.
    """
    return assess_service.add_custom_question(
        db, engagement_id, process_key, payload.step_key, payload.text
    )


# Declared before `/{process_key}/score/versions`' sibling routes and, more importantly,
# kept distinct from the `/{process_key}` GET above. FastAPI matches in declaration order,
# so a bare `/{process_key}` placed after these would be fine, but a `/{version}`-style
# catch-all must never precede them — the same trap already recorded for export.pdf.
@router.post("/{process_key}/score", response_model=AssessmentScoreRead)
def generate_score(
    engagement_id: str,
    process_key: str,
    payload: GenerateScoreRequest | None = None,
    db: Session = Depends(get_db),
) -> AssessmentScoreRead:
    """Score the recorded answers and store the result as a new version."""
    request = payload or GenerateScoreRequest()
    return _to_read(
        assess_service.generate_score(db, engagement_id, process_key, request.generator)
    )


@router.get("/{process_key}/score", response_model=AssessmentScoreRead)
def get_latest_score(
    engagement_id: str, process_key: str, db: Session = Depends(get_db)
) -> AssessmentScoreRead:
    """The most recent score. 404 `no_score` if this process has not been scored."""
    return _to_read(assess_service.get_latest_score(db, engagement_id, process_key))


@router.get("/{process_key}/score/versions", response_model=list[ScoreVersionSummary])
def list_score_versions(
    engagement_id: str, process_key: str, db: Session = Depends(get_db)
) -> list[ScoreVersionSummary]:
    rows = assess_service.list_score_versions(db, engagement_id, process_key)
    return [
        ScoreVersionSummary(
            version=row.version,
            generator=row.generator,
            index=row.index_value,
            band=row.band,
            created_at=row.created_at,
        )
        for row in rows
    ]
