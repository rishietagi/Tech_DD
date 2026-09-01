"""Persistence for the Initial Request List. Versioned, never destructive.

Mirrors `services/scope/service.py`. The one structural difference: **responses live in
their own table**, so regenerating an IRL never clobbers answers someone has typed. When
a new version is generated, responses carried on stable question ids are copied forward.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.irl import InformationRequestList, IrlResponse
from app.schemas.irl import IrlPayload
from app.schemas.research import ResearchPayload
from app.schemas.scope import ScopeOfWorkPayloadV2
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.irl.llm import LlmIrlGenerator, RulesIrlGenerator
from app.services.research.service import find_latest_research
from app.services.scope import service as scope_service


def _generator_for(name: str | None) -> LlmIrlGenerator | RulesIrlGenerator:
    """Explicit request wins; otherwise follow the same setting the scope engine uses."""
    resolved = name or get_settings().scope_generator
    return LlmIrlGenerator() if resolved == "llm" else RulesIrlGenerator()


def generate_irl(
    db: Session,
    engagement_id: str,
    generator_name: str | None = None,
) -> InformationRequestList:
    """Build a request list from the latest scope, and store it as a new version."""
    engagement = get_engagement(db, engagement_id)

    # The IRL asks for the evidence the scope decided it needs, so a scope is a real
    # precondition rather than a convenience.
    try:
        scope_row = scope_service.get_latest_scope(db, engagement_id)
    except AppError as exc:
        if exc.code == "no_scope":
            raise AppError(
                code="not_scoped",
                message=(
                    "Generate a scope of work first. The request list is built from the "
                    "evidence the scope decided it needs."
                ),
                status_code=409,
            ) from exc
        raise

    payload_json = scope_row.payload_json
    if payload_json.get("schema_version") != 2:
        raise AppError(
            code="scope_not_supported",
            message="Only schema v2 scopes can produce a request list",
            status_code=409,
        )
    scope = ScopeOfWorkPayloadV2.model_validate(payload_json)

    intake = assemble_intake_full(engagement)

    # Research makes the questions specific and the function names fit the business, but
    # its absence must never block generation.
    research_row = find_latest_research(db, engagement_id)
    research: ResearchPayload | None = None
    if research_row is not None:
        try:
            research = ResearchPayload.model_validate(research_row.payload_json)
        except Exception:  # noqa: BLE001 - stale payload shape must not break the IRL
            research = None

    previous = _latest_irl(db, engagement_id)
    previous_functions = _functions_of(previous)

    generator = _generator_for(generator_name)
    if isinstance(generator, LlmIrlGenerator):
        payload = generator.generate(
            intake,
            scope,
            research=research,
            source_scope_version=scope_row.version,
            previous_functions=previous_functions,
        )
    else:
        payload = generator.generate(
            intake, scope, research=research, source_scope_version=scope_row.version
        )

    irl = InformationRequestList(
        engagement_id=engagement_id,
        version=(previous.version if previous else 0) + 1,
        generator=payload.generator,
        source_scope_version=scope_row.version,
        payload_json=payload.model_dump(mode="json"),
    )
    db.add(irl)
    db.flush()

    _carry_forward_responses(db, previous, irl, payload)

    db.commit()
    db.refresh(irl)
    return irl


def _latest_irl(db: Session, engagement_id: str) -> InformationRequestList | None:
    return db.execute(
        select(InformationRequestList)
        .where(InformationRequestList.engagement_id == engagement_id)
        .order_by(InformationRequestList.version.desc())
        .limit(1)
    ).scalar_one_or_none()


def _functions_of(irl: InformationRequestList | None) -> list[str] | None:
    """The previous run's function names, fed back so naming stays stable."""
    if irl is None:
        return None
    functions = irl.payload_json.get("functions") or []
    names = [
        str(f["name"]) for f in functions if isinstance(f, dict) and f.get("name")
    ]
    return names or None


def _carry_forward_responses(
    db: Session,
    previous: InformationRequestList | None,
    fresh: InformationRequestList,
    payload: IrlPayload,
) -> None:
    """Copy answers onto the new version wherever the question id still exists.

    Seed ids are derived from the scope row (`PD-01-E1`), so they survive a regeneration
    against an unchanged scope — which is exactly when a user would be upset to lose
    their typing. Model-added questions get positional ids and will not always match;
    those answers stay on the old version rather than being mapped onto a question that
    may now say something different.
    """
    if previous is None:
        return

    existing = {r.question_id: r.response_text for r in previous.responses}
    if not existing:
        return

    live_ids = {q.id for q in payload.questions}
    for question_id, text in existing.items():
        if question_id in live_ids and text.strip():
            db.add(
                IrlResponse(irl_id=fresh.id, question_id=question_id, response_text=text)
            )


def get_latest_irl(db: Session, engagement_id: str) -> InformationRequestList:
    get_engagement(db, engagement_id)
    irl = _latest_irl(db, engagement_id)
    if irl is None:
        raise AppError(
            code="no_irl",
            message="No request list has been generated for this engagement yet",
            status_code=404,
        )
    return irl


def get_irl_version(db: Session, engagement_id: str, version: int) -> InformationRequestList:
    get_engagement(db, engagement_id)
    irl = db.execute(
        select(InformationRequestList).where(
            InformationRequestList.engagement_id == engagement_id,
            InformationRequestList.version == version,
        )
    ).scalar_one_or_none()
    if irl is None:
        raise AppError(
            code="no_irl_version",
            message=f"Request list version {version} does not exist",
            status_code=404,
        )
    return irl


def list_irl_versions(db: Session, engagement_id: str) -> list[InformationRequestList]:
    get_engagement(db, engagement_id)
    return list(
        db.execute(
            select(InformationRequestList)
            .where(InformationRequestList.engagement_id == engagement_id)
            .order_by(InformationRequestList.version.desc())
        ).scalars()
    )


def responses_for(irl: InformationRequestList) -> dict[str, str]:
    return {r.question_id: r.response_text for r in irl.responses}


def save_response(
    db: Session, engagement_id: str, question_id: str, text: str
) -> InformationRequestList:
    """Upsert one answer on the latest version.

    An empty string deletes the row rather than storing blank text, so "cleared" and
    "never answered" are the same state on read.
    """
    irl = get_latest_irl(db, engagement_id)

    known = {q.get("id") for q in irl.payload_json.get("questions") or []}
    if question_id not in known:
        raise AppError(
            code="unknown_question",
            message=f"No question {question_id} in this request list",
            status_code=404,
        )

    existing = db.execute(
        select(IrlResponse).where(
            IrlResponse.irl_id == irl.id, IrlResponse.question_id == question_id
        )
    ).scalar_one_or_none()

    cleaned = text.strip()
    if not cleaned:
        if existing is not None:
            db.delete(existing)
    elif existing is not None:
        existing.response_text = cleaned
    else:
        db.add(IrlResponse(irl_id=irl.id, question_id=question_id, response_text=cleaned))

    db.commit()
    db.refresh(irl)
    return irl
