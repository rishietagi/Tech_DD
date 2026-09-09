"""Deterministic scoring for a process automation assessment.

The arithmetic is defined in `docs/reference/P2P_AUTOMATION_MODEL.md` §4-§5 and is
deliberately simple enough to reproduce by hand from the questionnaire — a consultant who
disagrees with a number should be able to see exactly where it came from and argue with
the evidence rather than with the tool.

Two rules carry most of the weight, and both exist to stop the score inventing findings:

1. **An unanswered question is excluded from the denominator, never scored as zero.** A
   blank is an absence of evidence, not evidence of manual working.
2. **A step with no answered scoring questions is `not_assessed`** and drops out of the
   index entirely, its weight redistributed across the steps that were assessed. Scoring
   a wholly unassessed step would let a half-finished questionnaire produce a confident
   number.
"""

from datetime import UTC, datetime

from app.schemas.assess import (
    BAND_LABELS,
    BAND_MEANINGS,
    AssessmentScorePayload,
    ProcessQuestionnaire,
    ProcessShape,
    ProcessStep,
    ScorePointer,
    StepScore,
    band_for_index,
    level_label_for,
)

DISCLAIMER = (
    "This score reflects the answers recorded by the deal team at the time it was run. "
    "It grades automation maturity only — not process design quality, commercial "
    "performance or system fitness — and is a calibration to be read alongside the "
    "evidence, not a substitute for it."
)

# Below this, a step's score rests on so few answers that reporting it without comment
# would overstate what is known.
_THIN_COVERAGE = 0.5

# A step at or below this is a gap worth naming in the pointers; at or above the other,
# a strength. Between them the step is unremarkable and adding it to the summary would
# dilute the things that matter.
_GAP_AT = 2.0
_STRENGTH_AT = 3.5


def _step_score(step: ProcessStep, answers: dict[str, str]) -> StepScore:
    """Score one step from the answers given against it."""
    option_scores: dict[str, dict[str, int]] = {
        q.id: {o.label: o.score for o in q.options} for q in step.questions if q.scores
    }
    scoreable = len(option_scores)

    collected: list[int] = []
    for question_id, options in option_scores.items():
        value = (answers.get(question_id) or "").strip()
        if not value:
            continue
        if value in options:
            collected.append(options[value])
        # An answer that is not one of the options is ignored rather than raising. The
        # questionnaire can change under a stored answer — an option retitled, a question
        # rewritten — and a score that refuses to compute because of a stale label would
        # be worse than one that reports reduced coverage.

    if not collected:
        return StepScore(
            key=step.key,
            sn=step.sn,
            title=step.title,
            weight=step.weight,
            score=None,
            assessed=False,
            level_label="",
            reason="Not assessed — no scoring question in this step has been answered",
            answered=0,
            scoreable=scoreable,
            deterministic_score=None,
        )

    mean = round(sum(collected) / len(collected), 1)
    label = level_label_for(mean)
    coverage = len(collected) / scoreable if scoreable else 0.0

    reason = f"{label} ({mean}/5) from {len(collected)} of {scoreable} scoring questions"
    if coverage < _THIN_COVERAGE:
        reason += " — thin coverage, treat as indicative"

    return StepScore(
        key=step.key,
        sn=step.sn,
        title=step.title,
        weight=step.weight,
        score=mean,
        assessed=True,
        level_label=label,
        reason=reason,
        answered=len(collected),
        scoreable=scoreable,
        deterministic_score=mean,
    )


def compute_index(steps: list[StepScore]) -> float:
    """Weighted mean of the assessed steps, normalised to 0-100.

    Unassessed steps drop out of both the numerator and the denominator, which is what
    redistributes their weight across the rest.
    """
    assessed = [s for s in steps if s.assessed and s.score is not None]
    if not assessed:
        return 0.0
    weight_total = sum(s.weight for s in assessed)
    if weight_total == 0:
        return 0.0
    weighted = sum((s.score or 0.0) * s.weight for s in assessed)
    return round((weighted / weight_total) * 20, 1)


def _shape_note(steps: list[StepScore], shape: ProcessShape | None = None) -> str | None:
    """Name the recurring shapes from the process's own automation model, §6.

    The index alone hides these: a front-loaded 52 and a uniform 52 imply remediation
    costs an order of magnitude apart.

    The *arithmetic* is process-agnostic — the mean of the early steps against the mean
    of the late ones — but where the ends sit and what a gap between them means are not.
    Both come from the questionnaire's `shape` block, so a new process declares its own
    commercial reading in YAML rather than inheriting P2P's. A questionnaire with no
    `shape` block falls back to the nine-step P2P split and its wording.
    """
    assessed = [s for s in steps if s.assessed and s.score is not None]
    if len(assessed) < 4:
        return None

    if shape is not None:
        front = [s for s in assessed if s.sn in shape.front_steps]
        back = [s for s in assessed if s.sn in shape.back_steps]
    else:
        front = [s for s in assessed if s.sn <= 3]
        back = [s for s in assessed if s.sn >= 7]
    if not front or not back:
        return None

    front_mean = sum(s.score or 0 for s in front) / len(front)
    back_mean = sum(s.score or 0 for s in back) / len(back)
    gap = front_mean - back_mean
    measured = f" (front {front_mean:.1f}/5, back {back_mean:.1f}/5)"

    if shape is not None:
        if gap >= 1.0:
            return f"{shape.front_loaded}{measured}"
        if gap <= -1.0:
            return f"{shape.back_loaded}{measured}"
        return f"{shape.even}{measured}"

    if gap >= 1.0:
        return (
            "Front-loaded: the requisition and approval end is materially more automated "
            f"({front_mean:.1f}/5) than the invoice and payment end ({back_mean:.1f}/5). "
            "This is the classic signature of a procurement tool bought and never fully "
            "rolled through to accounts payable — the FTE cost usually remains at the "
            "back end, where a synergy case tends to assume it has gone."
        )
    if gap <= -1.0:
        return (
            "Back-loaded: the invoice and payment end is materially more automated "
            f"({back_mean:.1f}/5) than the requisition and approval end ({front_mean:.1f}/5). "
            "Finance has modernised what it controls, but spend is not being influenced "
            "before it is committed — savings cases resting on category management will "
            "tend to underdeliver."
        )
    return (
        f"Broadly even across the cycle (front {front_mean:.1f}/5, back {back_mean:.1f}/5), "
        "so the constraint is the overall level rather than one weak end."
    )


def _pointers(steps: list[StepScore], questionnaire: ProcessQuestionnaire) -> list[ScorePointer]:
    """Strengths, gaps, and what to probe next.

    Ordered by weight rather than by score, so the pointers name the steps that matter
    commercially rather than simply the lowest numbers.
    """
    pointers: list[ScorePointer] = []
    assessed = [s for s in steps if s.assessed and s.score is not None]

    gaps = sorted(
        [s for s in assessed if (s.score or 0) <= _GAP_AT],
        key=lambda s: (-s.weight, s.score or 0),
    )
    for step in gaps[:4]:
        pointers.append(
            ScorePointer(
                kind="gap",
                step_key=step.key,
                text=(
                    f"{step.title} scores {step.score}/5 ({step.level_label}) and carries "
                    f"{step.weight}% of the process weight — the largest single drag on the index."
                    if step is gaps[0]
                    else f"{step.title} scores {step.score}/5 ({step.level_label}), "
                    f"at {step.weight}% of process weight."
                ),
            )
        )

    strengths = sorted(
        [s for s in assessed if (s.score or 0) >= _STRENGTH_AT],
        key=lambda s: (-(s.score or 0), -s.weight),
    )
    for step in strengths[:3]:
        pointers.append(
            ScorePointer(
                kind="strength",
                step_key=step.key,
                text=f"{step.title} is a relative strength at {step.score}/5 ({step.level_label}).",
            )
        )

    # Probes: the unassessed steps, heaviest first. These are the fastest way to make the
    # score more defensible, so they are named explicitly rather than left implicit in a
    # coverage percentage.
    unassessed = sorted(
        [s for s in steps if not s.assessed], key=lambda s: -s.weight
    )
    for position, step in enumerate(unassessed[:4]):
        # Only the heaviest can be the one that would move the index most — saying it of
        # every unassessed step made the claim meaningless. Found by reading the output.
        text = (
            f"{step.title} has not been assessed and carries {step.weight}% of the weight — "
            "answering it would move the index more than any other outstanding step."
            if position == 0
            else f"{step.title} has not been assessed ({step.weight}% of the weight)."
        )
        pointers.append(ScorePointer(kind="probe", step_key=step.key, text=text))

    thin = [s for s in assessed if s.scoreable and s.answered / s.scoreable < _THIN_COVERAGE]
    for step in sorted(thin, key=lambda s: -s.weight)[:2]:
        pointers.append(
            ScorePointer(
                kind="probe",
                step_key=step.key,
                text=(
                    f"{step.title} rests on {step.answered} of {step.scoreable} scoring "
                    "questions. Treat the score as indicative until the rest are answered."
                ),
            )
        )

    if not pointers:
        pointers.append(
            ScorePointer(
                kind="probe",
                text=(
                    f"No step in {questionnaire.name} has been assessed yet. Answer the "
                    "scoring questions to produce a meaningful index."
                ),
            )
        )
    return pointers


def _coverage_note(steps: list[StepScore], scored: int, scoreable: int) -> str:
    assessed = [s for s in steps if s.assessed]
    note = (
        f"Scored on {scored} of {scoreable} scoring questions, covering "
        f"{len(assessed)} of {len(steps)} process steps."
    )
    if len(assessed) < len(steps):
        missing = [s.title for s in steps if not s.assessed]
        note += (
            f" The weight of the unassessed step{'s' if len(missing) > 1 else ''} "
            f"({', '.join(missing)}) has been redistributed across those that were assessed, "
            "rather than counted as zero."
        )
    return note


def _fallback_summary(
    questionnaire: ProcessQuestionnaire,
    index: float,
    band: str,
    steps: list[StepScore],
) -> str:
    """The summary written without the model.

    Terser than the generated one, never absent — the same property the scope engine
    holds. It states the index, the band, the shape and the heaviest gap, which is the
    minimum a reader needs to act.
    """
    assessed = [s for s in steps if s.assessed and s.score is not None]
    if not assessed:
        return (
            f"{questionnaire.name} has not yet been assessed. No scoring question has been "
            "answered, so no index can be computed."
        )

    parts = [
        f"{questionnaire.name} scores {index}/100 on the automation index, placing it in "
        f"the {BAND_LABELS[band]} band. {BAND_MEANINGS[band]}"
    ]

    weakest = min(assessed, key=lambda s: (s.score or 0, -s.weight))
    strongest = max(assessed, key=lambda s: (s.score or 0, s.weight))
    parts.append(
        f"The weakest assessed step is {weakest.title} at {weakest.score}/5 "
        f"({weakest.level_label}); the strongest is {strongest.title} at {strongest.score}/5 "
        f"({strongest.level_label})."
    )

    # The shape is carried on its own field and rendered beside the summary, so repeating
    # it verbatim here would print the same paragraph twice on the page. Only the
    # unassessed steps are worth adding, because they bound what the number is worth.
    unassessed = [s for s in steps if not s.assessed]
    if unassessed:
        names = ", ".join(s.title for s in unassessed)
        parts.append(
            f"{len(unassessed)} step{'s' if len(unassessed) > 1 else ''} "
            f"({names}) {'have' if len(unassessed) > 1 else 'has'} not been assessed, so the "
            "index rests on the remainder."
        )

    return " ".join(parts)


def score_assessment(
    questionnaire: ProcessQuestionnaire,
    answers: dict[str, str],
) -> AssessmentScorePayload:
    """Compute the deterministic score. The LLM layer may refine this afterwards."""
    steps = [_step_score(step, answers) for step in questionnaire.steps]

    index = compute_index(steps)
    band = band_for_index(index)

    scored = sum(s.answered for s in steps)
    scoreable = sum(s.scoreable for s in steps)
    assessed_steps = sum(1 for s in steps if s.assessed)

    return AssessmentScorePayload(
        process_key=questionnaire.process_key,
        process_name=questionnaire.name,
        questionnaire_version=questionnaire.version,
        model_ref=questionnaire.model_ref,
        index=index,
        deterministic_index=index,
        band=band,
        band_label=BAND_LABELS[band],
        band_meaning=BAND_MEANINGS[band],
        steps=steps,
        questions_scored=scored,
        questions_scoreable=scoreable,
        steps_assessed=assessed_steps,
        steps_total=len(steps),
        coverage_note=_coverage_note(steps, scored, scoreable),
        executive_summary=_fallback_summary(questionnaire, index, band, steps),
        pointers=_pointers(steps, questionnaire),
        shape_note=_shape_note(steps, questionnaire.shape),
        generator="rules",
        generated_at=datetime.now(UTC),
        disclaimer=DISCLAIMER,
    )
