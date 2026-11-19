"""The analyst's questionnaire — one mechanism for every judgement question in Phase 8.

Applications (portfolio questions), team & governance, and strategy & projects all ask the
same kind of question: one option per question, each option worth a share of the
question's weight, and a weak option raising an observation against a theme. The pattern
is the IT budget's process questions, which Rishi had already accepted (2026-11-18).

Questions can be limited to some DD types (`applies_to`) or to deals where AI is material
(`requires_ai`, scope rule A11). A question that does not apply is not asked and not scored.
"""

import statistics
from dataclasses import dataclass

from app.schemas.estate import (
    AnswerOption,
    EstateQuestion,
    JudgementQuestion,
    JudgementSection,
    SectionScore,
    ThemeDef,
)
from app.services.estate.gaps import Observation, with_remark


@dataclass(frozen=True)
class AssessContext:
    dd_type: str = "enterprise"
    ai_material: bool = False


def applies(question: JudgementQuestion, context: AssessContext) -> bool:
    if question.applies_to and context.dd_type not in question.applies_to:
        return False
    return not (question.requires_ai and not context.ai_material)


def visible(questions: list[JudgementQuestion], context: AssessContext) -> list[JudgementQuestion]:
    return [q for q in questions if applies(q, context)]


def as_estate_questions(
    questions: list[JudgementQuestion], sections: list[JudgementSection], context: AssessContext
) -> list[EstateQuestion]:
    labels = {s.key: s.label for s in sections}
    return [
        EstateQuestion(
            id=q.id,
            text=q.text,
            help=q.help,
            group=q.section,
            group_label=labels.get(q.section, q.section),
            source=q.source,
            options=[AnswerOption(value=o.label, label=o.label) for o in q.options],
        )
        for q in visible(questions, context)
    ]


@dataclass
class JudgementResult:
    sections: list[SectionScore]
    observations: list[Observation]
    answered: int
    question_count: int


def score(
    sections: list[JudgementSection],
    questions: list[JudgementQuestion],
    answers: dict[str, str],
    remarks: dict[str, str],
    context: AssessContext,
) -> JudgementResult:
    asked = visible(questions, context)
    per_section: dict[str, list[tuple[float, float]]] = {s.key: [] for s in sections}
    evidence: dict[str, int] = {s.key: 0 for s in sections}
    observations: list[Observation] = []
    answered = 0
    for question in asked:
        chosen = (answers.get(question.id) or "").strip()
        option = next((o for o in question.options if o.label == chosen), None)
        if option is None:
            continue
        answered += 1
        evidence[question.section] += 1
        if option.value is not None:
            per_section[question.section].append((option.value, question.weight))
        if option.finding and question.theme:
            observations.append(
                Observation(
                    theme=question.theme,
                    text=with_remark(option.finding, remarks.get(question.id, "")),
                    severity=option.severity,
                    source=f"question:{question.id}",
                )
            )
    scores = [
        SectionScore(
            key=s.key,
            label=s.label,
            score=(
                round(100 * sum(v * w for v, w in per_section[s.key]) / sum(w for _, w in per_section[s.key]), 1)
                if per_section[s.key]
                else None
            ),
            weight=s.weight,
            evidence=evidence[s.key],
        )
        for s in sections
        if any(q.section == s.key for q in asked)
    ]
    return JudgementResult(sections=scores, observations=observations, answered=answered, question_count=len(asked))


def weighted_index(sections: list[SectionScore]) -> float | None:
    """Weighted mean of the sections with evidence; a section with none drops out."""
    scored = [s for s in sections if s.score is not None]
    if not scored:
        return None
    total = sum(s.weight for s in scored)
    return round(sum((s.score or 0) * s.weight for s in scored) / total, 1) if total else None


def mean(values: list[float]) -> float | None:
    return round(statistics.mean(values), 1) if values else None


def validate(
    where: str,
    sections: list[JudgementSection],
    questions: list[JudgementQuestion],
    themes: list[ThemeDef],
) -> list[str]:
    """Problems with a questionnaire's content, as messages. Empty when sound."""
    problems: list[str] = []
    section_keys = {s.key for s in sections}
    theme_ids = {t.id for t in themes}
    seen: set[str] = set()
    for question in questions:
        if question.id in seen:
            problems.append(f"{where}: duplicate question id {question.id!r}")
        seen.add(question.id)
        if question.section not in section_keys:
            problems.append(f"{where} {question.id}: unknown section {question.section!r}")
        if question.theme is not None and question.theme not in theme_ids:
            problems.append(f"{where} {question.id}: unknown theme {question.theme!r}")
        if not question.options:
            problems.append(f"{where} {question.id}: no options")
        for option in question.options:
            if option.value is not None and not 0 <= option.value <= 1:
                problems.append(f"{where} {question.id}: option value {option.value} outside 0..1")
            if option.finding and option.severity is None:
                problems.append(f"{where} {question.id}: an option with a finding needs a severity")
            if option.finding and question.theme is None:
                problems.append(f"{where} {question.id}: an option with a finding needs the question's theme")
    theme_seen: set[str] = set()
    for theme in themes:
        if theme.id in theme_seen:
            problems.append(f"{where}: duplicate theme id {theme.id!r}")
        theme_seen.add(theme.id)
    return problems
