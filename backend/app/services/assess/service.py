"""Persistence and assembly for the Assess module.

Two different lifecycles, handled differently on purpose:

* **Answers and custom questions are not versioned.** They are the analyst's working
  notes; there is one current set, edited continuously, and a version history of
  half-typed answers would be noise.
* **Scores are versioned**, like every other generated deliverable. Re-scoring after more
  answers arrive produces a new version rather than mutating the old one, so a reader can
  see how the assessment moved as evidence arrived.

The questionnaire itself is assembled on read from the YAML plus the engagement's own
custom questions — nothing about it is stored, so a corrected question text reaches every
engagement at once.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.assess import ProcessAnswer, ProcessAssessmentScore, ProcessCustomQuestion
from app.schemas.assess import (
    AnswerRead,
    AssessmentRead,
    AssessmentScorePayload,
    ProcessListResponse,
    ProcessQuestionnaire,
    ProcessStep,
    ProcessSummary,
    Question,
)
from app.services.assess.library import (
    ProcessNotDefinedError,
    get_process_registry,
    get_questionnaire,
)
from app.services.assess.llm import LlmScoreGenerator, RulesScoreGenerator
from app.services.engagements import assemble_intake_full, get_engagement

logger = logging.getLogger(__name__)


def _generator_for(name: str | None) -> LlmScoreGenerator | RulesScoreGenerator:
    """Explicit request wins; otherwise follow the same setting the scope engine uses."""
    resolved = name or get_settings().scope_generator
    return LlmScoreGenerator() if resolved == "llm" else RulesScoreGenerator()


# --------------------------------------------------------------------------- reads


def _custom_questions(
    db: Session, engagement_id: str, process_key: str
) -> list[ProcessCustomQuestion]:
    return list(
        db.scalars(
            select(ProcessCustomQuestion)
            .where(
                ProcessCustomQuestion.engagement_id == engagement_id,
                ProcessCustomQuestion.process_key == process_key,
            )
            .order_by(ProcessCustomQuestion.created_at)
        )
    )


def load_answers(db: Session, engagement_id: str, process_key: str) -> dict[str, str]:
    """Every recorded answer for one process, keyed by question or nudge id."""
    rows = db.scalars(
        select(ProcessAnswer).where(
            ProcessAnswer.engagement_id == engagement_id,
            ProcessAnswer.process_key == process_key,
        )
    )
    return {row.question_id: row.value for row in rows}


def build_steps(
    questionnaire: ProcessQuestionnaire, customs: list[ProcessCustomQuestion]
) -> list[ProcessStep]:
    """The YAML steps with each engagement's own added questions merged in.

    Custom questions are appended to their step rather than collected at the end, so they
    read in the context the analyst added them in. They carry `is_custom` and no options,
    which is what keeps them out of the score.
    """
    by_step: dict[str, list[ProcessCustomQuestion]] = {}
    for custom in customs:
        by_step.setdefault(custom.step_key, []).append(custom)

    steps: list[ProcessStep] = []
    for step in questionnaire.steps:
        extra = [
            Question(id=c.question_id, text=c.text, type="text", is_custom=True)
            for c in by_step.get(step.key, [])
        ]
        steps.append(
            step.model_copy(update={"questions": [*step.questions, *extra]}) if extra else step
        )
    return steps


def count_questions(steps: list[ProcessStep]) -> int:
    """Questions plus nudges — a nudge is a question once its condition has fired.

    Counted unconditionally rather than only when visible, because whether a nudge is
    showing depends on an answer that can change; a denominator that moved as the analyst
    typed would make progress unreadable.
    """
    return sum(len(q.nudges) + 1 for step in steps for q in step.questions)


def count_answered(steps: list[ProcessStep], answers: dict[str, str]) -> int:
    ids = {q.id for step in steps for q in step.questions}
    ids |= {n.id for step in steps for q in step.questions for n in q.nudges}
    return sum(1 for qid in ids if (answers.get(qid) or "").strip())


def list_processes(db: Session, engagement_id: str) -> ProcessListResponse:
    """Every business process, with progress against the ones that are defined."""
    get_engagement(db, engagement_id)
    registry = get_process_registry()

    summaries: list[ProcessSummary] = []
    for entry in registry.processes:
        summary = ProcessSummary(
            key=entry.key,
            name=entry.name,
            short_name=entry.short_name,
            description=entry.description,
            defined=entry.defined,
        )
        if entry.defined:
            questionnaire = get_questionnaire(entry.key)
            steps = build_steps(questionnaire, _custom_questions(db, engagement_id, entry.key))
            answers = load_answers(db, engagement_id, entry.key)
            summary.question_count = count_questions(steps)
            summary.answered_count = count_answered(steps, answers)

            latest = find_latest_score(db, engagement_id, entry.key)
            if latest is not None:
                summary.has_score = True
                summary.index = latest.index_value
                summary.band = latest.band  # type: ignore[assignment]
        summaries.append(summary)

    return ProcessListResponse(engagement_id=engagement_id, processes=summaries)


def get_assessment(db: Session, engagement_id: str, process_key: str) -> AssessmentRead:
    """The questionnaire plus whatever has been answered against it."""
    get_engagement(db, engagement_id)
    questionnaire = get_questionnaire(process_key)

    steps = build_steps(questionnaire, _custom_questions(db, engagement_id, process_key))
    answers = load_answers(db, engagement_id, process_key)
    latest = find_latest_score(db, engagement_id, process_key)

    return AssessmentRead(
        engagement_id=engagement_id,
        process_key=questionnaire.process_key,
        name=questionnaire.name,
        short_name=questionnaire.short_name,
        description=questionnaire.description,
        model_ref=questionnaire.model_ref,
        questionnaire_version=questionnaire.version,
        steps=steps,
        answers={qid: AnswerRead(question_id=qid, value=value) for qid, value in answers.items()},
        question_count=count_questions(steps),
        answered_count=count_answered(steps, answers),
        latest_score_version=latest.version if latest is not None else None,
    )


# --------------------------------------------------------------------------- writes


def _known_ids(db: Session, engagement_id: str, questionnaire: ProcessQuestionnaire) -> set[str]:
    ids: set[str] = set()
    for step in questionnaire.steps:
        for question in step.questions:
            ids.add(question.id)
            ids.update(n.id for n in question.nudges)
    ids.update(
        c.question_id for c in _custom_questions(db, engagement_id, questionnaire.process_key)
    )
    return ids


def save_answer(
    db: Session, engagement_id: str, process_key: str, question_id: str, value: str
) -> AssessmentRead:
    """Upsert one answer. Writing an empty value clears it.

    An unknown question id is rejected rather than stored: a typo would otherwise create
    an orphan row that never renders and never scores, and would be invisible until
    someone went looking in the database.
    """
    get_engagement(db, engagement_id)
    questionnaire = get_questionnaire(process_key)

    if question_id not in _known_ids(db, engagement_id, questionnaire):
        raise AppError(
            code="unknown_question",
            message=f"{question_id!r} is not a question in the {questionnaire.name} questionnaire",
            status_code=404,
        )

    row = db.scalar(
        select(ProcessAnswer).where(
            ProcessAnswer.engagement_id == engagement_id,
            ProcessAnswer.process_key == process_key,
            ProcessAnswer.question_id == question_id,
        )
    )
    if row is None:
        row = ProcessAnswer(
            engagement_id=engagement_id,
            process_key=process_key,
            question_id=question_id,
            value=value,
        )
        db.add(row)
    else:
        row.value = value

    db.commit()
    return get_assessment(db, engagement_id, process_key)


def add_custom_question(
    db: Session, engagement_id: str, process_key: str, step_key: str, text: str
) -> AssessmentRead:
    """Add a question the questionnaire did not anticipate, under a named step."""
    get_engagement(db, engagement_id)
    questionnaire = get_questionnaire(process_key)

    if step_key not in {step.key for step in questionnaire.steps}:
        raise AppError(
            code="unknown_step",
            message=f"{step_key!r} is not a step in the {questionnaire.name} questionnaire",
            status_code=404,
        )

    existing = _custom_questions(db, engagement_id, process_key)
    # Ids are scoped by engagement and process and numbered from the count, so they stay
    # readable and stable. Deleting a custom question is not offered, so the counter
    # cannot collide with a reused number.
    question_id = f"{questionnaire.short_name.upper()}-CUSTOM-{len(existing) + 1:03d}"

    db.add(
        ProcessCustomQuestion(
            engagement_id=engagement_id,
            process_key=process_key,
            step_key=step_key,
            question_id=question_id,
            text=text.strip(),
        )
    )
    db.commit()
    return get_assessment(db, engagement_id, process_key)


# --------------------------------------------------------------------------- scoring


def find_latest_score(
    db: Session, engagement_id: str, process_key: str
) -> ProcessAssessmentScore | None:
    return db.scalar(
        select(ProcessAssessmentScore)
        .where(
            ProcessAssessmentScore.engagement_id == engagement_id,
            ProcessAssessmentScore.process_key == process_key,
        )
        .order_by(ProcessAssessmentScore.version.desc())
        .limit(1)
    )


def get_latest_score(db: Session, engagement_id: str, process_key: str) -> ProcessAssessmentScore:
    get_engagement(db, engagement_id)
    # Validates the process key and rejects an undefined one, so a bad key does not
    # surface as "no score" and send the analyst looking for a scoring bug.
    get_questionnaire(process_key)

    row = find_latest_score(db, engagement_id, process_key)
    if row is None:
        raise AppError(
            code="no_score",
            message="This process has not been scored yet",
            status_code=404,
        )
    return row


def _engagement_context(db: Session, engagement_id: str) -> dict[str, Any]:
    """The target and the thesis, so the summary can be about this deal.

    Failure here is not allowed to block scoring: the context makes the narrative
    specific, but an assessment is perfectly scoreable without it.
    """
    try:
        engagement = get_engagement(db, engagement_id)
        intake = assemble_intake_full(engagement)
    except Exception as exc:  # noqa: BLE001 - context is an enhancement, never a dependency
        logger.warning("Could not assemble intake context for scoring (%s).", exc)
        return {}

    return {
        "company_name": intake.target.company_name,
        "sector": intake.target.sector,
        "line_of_business": intake.target.line_of_business,
        "headcount": intake.target.headcount,
        "core_systems": intake.technology.core_systems,
        "hosting_model": intake.technology.hosting_model,
        "deal_rationale": intake.rationale.rationale_narrative,
        "focus_areas": intake.rationale.focus_areas,
        "post_close_intent": intake.structure.post_close_intent,
    }


def generate_score(
    db: Session,
    engagement_id: str,
    process_key: str,
    generator_name: str | None = None,
) -> ProcessAssessmentScore:
    """Score the recorded answers and store the result as a new version."""
    get_engagement(db, engagement_id)
    questionnaire = get_questionnaire(process_key)

    steps = build_steps(questionnaire, _custom_questions(db, engagement_id, process_key))
    answers = load_answers(db, engagement_id, process_key)

    # Custom questions never score, but their answers are evidence the narrative should
    # see, so they reach the model through the merged questionnaire.
    merged = questionnaire.model_copy(update={"steps": steps})

    generator = _generator_for(generator_name)
    payload = generator.score(merged, answers, _engagement_context(db, engagement_id))

    latest = find_latest_score(db, engagement_id, process_key)
    version = (latest.version + 1) if latest is not None else 1

    row = ProcessAssessmentScore(
        engagement_id=engagement_id,
        process_key=process_key,
        version=version,
        generator=payload.generator,
        index_value=payload.index,
        band=payload.band,
        refined=any(step.refined for step in payload.steps),
        payload_json=payload.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_score_versions(
    db: Session, engagement_id: str, process_key: str
) -> list[ProcessAssessmentScore]:
    get_engagement(db, engagement_id)
    return list(
        db.scalars(
            select(ProcessAssessmentScore)
            .where(
                ProcessAssessmentScore.engagement_id == engagement_id,
                ProcessAssessmentScore.process_key == process_key,
            )
            .order_by(ProcessAssessmentScore.version.desc())
        )
    )


def payload_of(row: ProcessAssessmentScore) -> AssessmentScorePayload:
    return AssessmentScorePayload.model_validate(row.payload_json)


__all__ = [
    "ProcessNotDefinedError",
    "add_custom_question",
    "generate_score",
    "get_assessment",
    "get_latest_score",
    "list_processes",
    "list_score_versions",
    "load_answers",
    "payload_of",
    "save_answer",
]
