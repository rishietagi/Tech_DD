"""IT budget review — the budgeting process and spend against budget, never a cost model.

The boundary is the 2026-09-14 one, restated in `reference/estate/it_budget.yaml`: no
percentage of revenue, no benchmark band, no model of what technology should cost. What is
computed here is arithmetic on figures the target reported — variance against its own
budget, movement year on year, the run/change mix as reported — and the findings raised by
how the budget is built and controlled.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.estate import ItBudget
from app.schemas.estate import GapNoteWrite
from app.schemas.it_budget import (
    BudgetFinding,
    BudgetLine,
    ItBudgetConfig,
    ItBudgetInputs,
    ItBudgetQuestionRead,
    ItBudgetRead,
    ItBudgetReview,
    LineReview,
    LineYear,
    YearTotal,
)
from app.services.engagements import get_engagement
from app.services.estate.gaps import (
    Observation,
    build_theme_gaps,
    delete_note,
    load_notes,
    overlay,
    write_note,
)
from app.services.estate.library import get_it_budget_config

_RANK = {"High": 0, "Medium": 1, "Low": 2}


def default_inputs(config: ItBudgetConfig, today: datetime | None = None) -> ItBudgetInputs:
    """The last N completed financial years, with the default lines and no figures.

    Labelled by calendar year because the target's year-end is not known; the analyst
    relabels them (FY24, FY2024/25) to match the accounts.
    """
    year = (today or datetime.now(UTC)).year
    years = [f"FY{y}" for y in range(year - config.default_period_years, year)]
    return ItBudgetInputs(
        years=years,
        lines=[
            BudgetLine(
                id=f"L{i:02d}",
                name=line.name,
                kind=line.kind,
                budget=[None] * len(years),
                actual=[None] * len(years),
            )
            for i, line in enumerate(config.default_lines, start=1)
        ],
    )


def _pct(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(100 * numerator / denominator, 1)  # type: ignore[operator]


def _at(values: list[float | None], i: int) -> float | None:
    return values[i] if i < len(values) else None


def review(inputs: ItBudgetInputs, config: ItBudgetConfig) -> ItBudgetReview:
    tol, move = config.variance_tolerance_pct, config.yoy_movement_pct
    findings: list[BudgetFinding] = []
    lines: list[LineReview] = []

    for line in inputs.lines:
        years: list[LineYear] = []
        previous_actual: float | None = None
        for i, label in enumerate(inputs.years):
            budget, actual = _at(line.budget, i), _at(line.actual, i)
            variance = actual - budget if budget is not None and actual is not None else None
            variance_pct = _pct(variance, budget)
            outside = variance_pct is not None and abs(variance_pct) > tol
            yoy = (
                _pct(actual - previous_actual, previous_actual)
                if actual is not None and previous_actual is not None
                else None
            )
            yoy_flag = yoy is not None and abs(yoy) > move
            years.append(
                LineYear(
                    year=label,
                    budget=budget,
                    actual=actual,
                    variance=round(variance, 2) if variance is not None else None,
                    variance_pct=variance_pct,
                    outside_tolerance=outside,
                    yoy_pct=yoy,
                    yoy_flag=yoy_flag,
                )
            )
            if outside and variance_pct is not None:
                findings.append(
                    BudgetFinding(
                        severity="Medium" if abs(variance_pct) > 2 * tol else "Low",
                        source="variance",
                        text=(
                            f"{line.name}, {label}: actual "
                            f"{'over' if variance_pct > 0 else 'under'} budget by "
                            f"{abs(variance_pct):.1f}% — outside the ±{tol:.0f}% tolerance."
                        ),
                    )
                )
            if yoy_flag and yoy is not None:
                findings.append(
                    BudgetFinding(
                        severity="Low",
                        source="movement",
                        text=(
                            f"{line.name}: actual spend {'rose' if yoy > 0 else 'fell'} "
                            f"{abs(yoy):.1f}% into {label}. Ask management what drove it."
                        ),
                    )
                )
            if actual is not None:
                previous_actual = actual
        if any(a is not None for a in line.actual) and all(b is None for b in line.budget):
            findings.append(
                BudgetFinding(
                    severity="Medium",
                    source="missing",
                    text=f"{line.name} has reported spend but no budget in any year.",
                )
            )
        lines.append(LineReview(id=line.id, name=line.name, kind=line.kind, years=years))

    totals: list[YearTotal] = []
    for i, label in enumerate(inputs.years):
        budgets = [b for line in inputs.lines if (b := _at(line.budget, i)) is not None]
        actuals = [(a, line.kind) for line in inputs.lines if (a := _at(line.actual, i)) is not None]
        actual_total = round(sum(a for a, _ in actuals), 2) if actuals else None
        budget_total = round(sum(budgets), 2) if budgets else None
        run = sum(a for a, kind in actuals if kind == "run")
        change = sum(a for a, kind in actuals if kind == "change")
        # Variance is like-for-like: only lines carrying both figures that year. Spend with
        # no budget has its own finding, and counting it here would report an unbudgeted
        # recharge as an overrun of the budgeted lines.
        paired = [
            (b, a)
            for line in inputs.lines
            if (b := _at(line.budget, i)) is not None and (a := _at(line.actual, i)) is not None
        ]
        paired_budget = sum(b for b, _ in paired)
        paired_actual = sum(a for _, a in paired)
        totals.append(
            YearTotal(
                year=label,
                budget=budget_total,
                actual=actual_total,
                variance_pct=_pct(paired_actual - paired_budget, paired_budget) if paired else None,
                run_share_pct=_pct(run, actual_total) if actual_total else None,
                change_share_pct=_pct(change, actual_total) if actual_total else None,
            )
        )

    answered = 0
    for question in config.process_questions:
        answer = inputs.answers.get(question.id)
        value = answer.value.strip() if answer else ""
        if not value:
            continue
        answered += 1
        option = next((o for o in question.options if o.label == value), None)
        if option is not None and option.finding and option.severity:
            findings.append(
                BudgetFinding(
                    severity=option.severity,
                    source="process",
                    text=option.finding.strip(),
                    question_id=question.id,
                )
            )

    findings.sort(key=lambda f: (_RANK[f.severity], f.source != "process"))
    themes_by_question = {q.id: q.theme for q in config.process_questions}
    observations = [
        Observation(
            theme=(
                themes_by_question.get(f.question_id or "", "budget_process")
                if f.source == "process"
                else "budget_movement" if f.source == "movement" else "budget_variance"
            ),
            text=f.text,
            severity=f.severity,
            source=f"budget:{f.source}",
        )
        for f in findings
    ]
    has_figures = any(v is not None for line in inputs.lines for v in [*line.budget, *line.actual])
    notes = []
    if not has_figures:
        notes.append("No budget or actual figures entered yet.")
    if answered < len(config.process_questions):
        notes.append(f"{answered} of {len(config.process_questions)} budgeting-process questions answered.")
    return ItBudgetReview(
        lines=lines,
        totals=totals,
        findings=findings,
        gaps=build_theme_gaps(observations, config.themes, "BU"),
        tolerance_pct=tol,
        movement_pct=move,
        answered=answered,
        question_count=len(config.process_questions),
        coverage_note=" ".join(notes),
    )


# ------------------------------------------------------------------ persistence


def _row(db: Session, engagement_id: str) -> ItBudget | None:
    return db.scalar(select(ItBudget).where(ItBudget.engagement_id == engagement_id))


def _validate(inputs: ItBudgetInputs, config: ItBudgetConfig) -> None:
    n = len(inputs.years)
    errors: list[dict[str, str]] = []
    ids = [line.id for line in inputs.lines]
    if len(set(ids)) != len(ids):
        errors.append({"field": "lines", "message": "Line ids must be unique."})
    for i, line in enumerate(inputs.lines):
        if not line.name.strip():
            errors.append({"field": f"lines.{i}.name", "message": "Every line needs a name."})
        if len(line.budget) > n or len(line.actual) > n:
            errors.append({"field": f"lines.{i}", "message": "More figures than years in the review period."})
        for value in [*line.budget, *line.actual]:
            if value is not None and value < 0:
                errors.append({"field": f"lines.{i}", "message": "Figures cannot be negative."})
                break
    labels = {q.id: {o.label for o in q.options} for q in config.process_questions}
    for qid, answer in inputs.answers.items():
        if qid not in labels:
            errors.append({"field": f"answers.{qid}", "message": "Unknown question."})
        elif answer.value and answer.value not in labels[qid]:
            errors.append({"field": f"answers.{qid}", "message": "Not one of the options."})
    if errors:
        raise AppError(
            code="validation_error",
            message="The budget could not be saved.",
            status_code=422,
            field_errors=errors,
        )


def _pad(inputs: ItBudgetInputs) -> ItBudgetInputs:
    """Align every line's figures to the period length, so the screen can index by year."""
    n = len(inputs.years)
    for line in inputs.lines:
        line.budget = (list(line.budget) + [None] * n)[:n]
        line.actual = (list(line.actual) + [None] * n)[:n]
    return inputs


def get_budget(db: Session, engagement_id: str) -> ItBudgetRead:
    get_engagement(db, engagement_id)
    config = get_it_budget_config()
    row = _row(db, engagement_id)
    inputs = _pad(ItBudgetInputs.model_validate(row.inputs_json)) if row is not None else default_inputs(config)
    result = review(inputs, config)
    # The consultant's edits to the findings (2026-11-19: "exportable, so editable"), applied
    # on read like every other register — the review itself is recomputed every time.
    result.gaps = overlay(result.gaps, load_notes(db, engagement_id, NOTE_DOMAIN))
    return ItBudgetRead(
        engagement_id=engagement_id,
        inputs=inputs,
        questions=[
            ItBudgetQuestionRead(id=q.id, text=q.text, options=[o.label for o in q.options])
            for q in config.process_questions
        ],
        review=result,
        saved=row is not None,
        updated_at=row.updated_at if row is not None else None,
    )


NOTE_DOMAIN = "it_budget"


def save_gap_note(db: Session, engagement_id: str, gap_key: str, write: GapNoteWrite) -> ItBudgetRead:
    current = get_budget(db, engagement_id)
    if not any(g.key == gap_key for g in current.review.gaps):
        raise AppError(code="unknown_gap", message="That finding is not in the current review.", status_code=404)
    write_note(db, engagement_id, NOTE_DOMAIN, gap_key, write)
    return get_budget(db, engagement_id)


def delete_gap_note(db: Session, engagement_id: str, gap_key: str) -> ItBudgetRead:
    delete_note(db, engagement_id, NOTE_DOMAIN, gap_key)
    return get_budget(db, engagement_id)


def save_budget(db: Session, engagement_id: str, inputs: ItBudgetInputs) -> ItBudgetRead:
    get_engagement(db, engagement_id)
    config = get_it_budget_config()
    _validate(inputs, config)
    data = _pad(inputs).model_dump(mode="json")
    row = _row(db, engagement_id)
    if row is None:
        db.add(ItBudget(engagement_id=engagement_id, inputs_json=data))
    else:
        row.inputs_json = data
    db.commit()
    return get_budget(db, engagement_id)
