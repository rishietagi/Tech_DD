"""IT budget review — the budgeting process, never a cost model.

The 2026-09-14 boundary applies in full: no percentage of revenue, no benchmark band, no
model of what technology should cost. What is reviewed is how the budget is built,
approved and controlled, and where reported spend landed against it.
docs/reference/ESTATE_ASSESSMENT_MODEL.md §5.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.estate import Severity

LineKind = Literal["run", "change"]


# ------------------------------------------------------------------ content (YAML)


class BudgetOption(BaseModel):
    model_config = {"extra": "forbid"}

    label: str
    finding: str | None = None
    severity: Severity | None = None


class BudgetQuestion(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    text: str
    options: list[BudgetOption]


class DefaultLine(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    kind: LineKind


class ItBudgetConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    default_period_years: int
    default_lines: list[DefaultLine]
    variance_tolerance_pct: float
    yoy_movement_pct: float
    process_questions: list[BudgetQuestion]


# ------------------------------------------------------------------ inputs


class BudgetLine(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    name: str
    kind: LineKind = "run"
    # One entry per year in the period, aligned by position. None = not supplied.
    budget: list[float | None] = Field(default_factory=list)
    actual: list[float | None] = Field(default_factory=list)


class BudgetAnswer(BaseModel):
    model_config = {"extra": "forbid"}

    value: str = ""
    remarks: str = ""


class ItBudgetInputs(BaseModel):
    """What the analyst records. Replaced whole on save — it is one small document."""

    model_config = {"extra": "forbid"}

    currency: str = ""
    unit: str = ""
    years: list[str]
    lines: list[BudgetLine]
    answers: dict[str, BudgetAnswer] = Field(default_factory=dict)
    notes: str = ""

    @field_validator("years")
    @classmethod
    def _years_unique(cls, years: list[str]) -> list[str]:
        cleaned = [y.strip() for y in years]
        if any(not y for y in cleaned):
            raise ValueError("every year needs a label")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("year labels must be unique")
        if not 1 <= len(cleaned) <= 10:
            raise ValueError("the review period must cover between 1 and 10 years")
        return cleaned


# ------------------------------------------------------------------ computed review


class LineYear(BaseModel):
    year: str
    budget: float | None
    actual: float | None
    variance: float | None  # actual - budget
    variance_pct: float | None
    outside_tolerance: bool = False
    yoy_pct: float | None = None  # movement in actual from the prior year
    yoy_flag: bool = False


class LineReview(BaseModel):
    id: str
    name: str
    kind: LineKind
    years: list[LineYear]


class YearTotal(BaseModel):
    year: str
    budget: float | None
    actual: float | None
    variance_pct: float | None
    run_share_pct: float | None  # of reported actual spend
    change_share_pct: float | None


class BudgetFinding(BaseModel):
    severity: Severity
    source: Literal["variance", "movement", "missing", "process"]
    text: str
    question_id: str | None = None


class ItBudgetReview(BaseModel):
    lines: list[LineReview]
    totals: list[YearTotal]
    findings: list[BudgetFinding]
    tolerance_pct: float
    movement_pct: float
    answered: int
    question_count: int
    coverage_note: str


class ItBudgetQuestionRead(BaseModel):
    id: str
    text: str
    options: list[str]


class ItBudgetRead(BaseModel):
    engagement_id: str
    inputs: ItBudgetInputs
    questions: list[ItBudgetQuestionRead]
    review: ItBudgetReview
    saved: bool
    updated_at: datetime | None = None
