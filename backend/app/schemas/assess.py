"""Process automation assessment payloads.

Three layers, deliberately separate:

* the **questionnaire** — content loaded from YAML, the same for every engagement;
* the **answers** — one analyst's responses, held in their own table;
* the **score** — a point-in-time judgement, versioned and stored.

The questionnaire and the answers are assembled on read (like the checklist). The score
is stored (unlike the checklist), because it carries an LLM-written summary and captures
what was known at a moment; re-running it after more answers arrive should produce a new
version rather than silently mutating the old one.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AnswerType = Literal["single_select", "text"]
Band = Literal["manual", "emerging", "standardised", "integrated", "optimised"]

BAND_LABELS: dict[str, str] = {
    "manual": "Manual",
    "emerging": "Emerging",
    "standardised": "Standardised",
    "integrated": "Integrated",
    "optimised": "Optimised",
}

# docs/reference/P2P_AUTOMATION_MODEL.md §5. Upper bound inclusive.
BAND_THRESHOLDS: list[tuple[int, Band]] = [
    (20, "manual"),
    (40, "emerging"),
    (60, "standardised"),
    (80, "integrated"),
    (100, "optimised"),
]

BAND_MEANINGS: dict[str, str] = {
    "manual": (
        "The process runs on people and spreadsheets. Headcount scales with volume. "
        "Expect control findings and a material systems investment in the plan."
    ),
    "emerging": (
        "Systems exist but the work is still human. Islands of automation with manual "
        "bridges between them. Integration cost is the story."
    ),
    "standardised": (
        "A defined, system-mediated process with real gaps. The usual mid-market shape. "
        "Improvement is available without replatforming."
    ),
    "integrated": (
        "Connected end to end with measured straight-through rates. Remaining gains are "
        "optimisation, not transformation."
    ),
    "optimised": (
        "Touchless by design. Rare — verify the running rates before accepting it."
    ),
}


# --------------------------------------------------------------------------- questionnaire


class NudgeCondition(BaseModel):
    """When a follow-up question should appear."""

    model_config = {"extra": "forbid", "populate_by_name": True}

    equals: str | None = None
    in_: list[str] | None = Field(default=None, alias="in")
    answered: bool | None = None


class Nudge(BaseModel):
    """A conditional follow-up: if X is the answer, ask Y.

    Nudges never score. They exist to make the evidence behind a score defensible; one
    that scored would double-count its parent question.
    """

    model_config = {"extra": "forbid"}

    id: str
    when: NudgeCondition
    ask: str


class QuestionOption(BaseModel):
    """One answer option and the maturity level it evidences."""

    model_config = {"extra": "forbid"}

    label: str
    score: int = Field(ge=0, le=5)


class Question(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    text: str
    type: AnswerType
    options: list[QuestionOption] = Field(default_factory=list)
    nudges: list[Nudge] = Field(default_factory=list)
    # True for questions an analyst added themselves. Custom questions never score —
    # they have no options and no place on the ladder.
    is_custom: bool = False

    @property
    def scores(self) -> bool:
        return self.type == "single_select" and bool(self.options)


class ProcessStep(BaseModel):
    model_config = {"extra": "forbid"}

    key: str
    sn: int
    title: str
    weight: int = Field(gt=0)
    intent: str
    questions: list[Question]


class ProcessShape(BaseModel):
    """How to read this process's front and back ends, declared as content.

    The arithmetic that produces the shape is process-agnostic — compare the mean of the
    early steps against the mean of the late ones — but *where the ends are* and *what a
    gap between them means commercially* are not. P2P has nine steps and a front-loaded
    cycle means a procurement tool never rolled through to accounts payable; O2C has
    eight and the same shape means the working capital problem grows with revenue. Both
    belong in YAML with the rest of the domain content.

    Optional: a questionnaire without a `shape` block falls back to the generic split in
    `scoring._shape_note`, so an existing file keeps working unchanged.
    """

    model_config = {"extra": "forbid"}

    # Step serial numbers, not indices — they match `ProcessStep.sn`.
    front_steps: list[int] = Field(min_length=1)
    back_steps: list[int] = Field(min_length=1)
    # Named so the even-shape sentence can say which end is which without the process
    # being hardcoded into the sentence.
    front_label: str
    back_label: str
    front_loaded: str
    back_loaded: str
    even: str


class ProcessQuestionnaire(BaseModel):
    """One process's full questionnaire, as loaded from YAML."""

    model_config = {"extra": "forbid"}

    process_key: str
    name: str
    short_name: str
    version: str
    model_ref: str
    description: str
    shape: ProcessShape | None = None
    steps: list[ProcessStep]


class ProcessSummary(BaseModel):
    """One row on the process index — what the analyst picks from."""

    key: str
    name: str
    short_name: str
    description: str
    # False for the four processes that are named but have no questionnaire yet.
    defined: bool
    question_count: int = 0
    answered_count: int = 0
    has_score: bool = False
    index: float | None = None
    band: Band | None = None
    # Findings the latest score raises (Phase 8 follow-up, 2026-11-19).
    gap_count: int = 0


class ProcessListResponse(BaseModel):
    engagement_id: str
    processes: list[ProcessSummary]


# --------------------------------------------------------------------------- answers


class AnswerRead(BaseModel):
    question_id: str
    value: str = ""
    # What the consultant heard in the room, qualifying the option picked. The option is
    # the answer; the remark is the evidence behind it.
    remarks: str = ""
    updated_at: datetime | None = None


class AnswerWrite(BaseModel):
    """Both fields optional so the UI can save an option and a remark independently.

    `None` means "leave this alone" rather than "clear it": the option and the remark are
    edited by separate controls, and saving one must never wipe the other.
    """

    model_config = {"extra": "forbid"}

    value: str | None = None
    remarks: str | None = Field(default=None, max_length=8000)


class CustomQuestionCreate(BaseModel):
    """An analyst adding a question the questionnaire did not anticipate."""

    model_config = {"extra": "forbid"}

    step_key: str
    text: str = Field(min_length=1, max_length=1000)


class AssessmentRead(BaseModel):
    """The questionnaire plus whatever has been answered against it."""

    engagement_id: str
    process_key: str
    name: str
    short_name: str
    description: str
    model_ref: str
    questionnaire_version: str
    steps: list[ProcessStep]
    answers: dict[str, AnswerRead]
    question_count: int
    answered_count: int
    latest_score_version: int | None = None


# --------------------------------------------------------------------------- scoring


class StepScore(BaseModel):
    """One step's score, and why it is what it is."""

    key: str
    sn: int
    title: str
    weight: int

    # None when no scoring question in this step was answered. Excluded from the index
    # rather than counted as zero — a blank is an absence of evidence, not evidence of
    # manual working.
    score: float | None = None
    assessed: bool = True
    level_label: str = ""
    reason: str = ""

    answered: int = 0
    scoreable: int = 0

    # What the deterministic rules produced, always kept even when the model has moved
    # the score. Both are shown, so a reader can see the adjustment and judge it.
    deterministic_score: float | None = None
    refined: bool = False
    refinement_reason: str | None = None


class ScorePointer(BaseModel):
    """A strength, a gap, or something to probe next."""

    kind: Literal["strength", "gap", "probe"]
    text: str
    step_key: str | None = None


class AssessmentScorePayload(BaseModel):
    """The stored result of one scoring run."""

    schema_version: int = 1
    process_key: str
    process_name: str
    questionnaire_version: str
    model_ref: str

    index: float
    band: Band
    band_label: str
    band_meaning: str

    # The index before any model refinement. Equal to `index` when nothing was refined.
    deterministic_index: float

    steps: list[StepScore]

    # Coverage, so a reader can tell a confident score from a thin one.
    questions_scored: int
    questions_scoreable: int
    steps_assessed: int
    steps_total: int
    coverage_note: str

    executive_summary: str
    pointers: list[ScorePointer] = Field(default_factory=list)
    shape_note: str | None = None

    generator: str
    generated_at: datetime
    disclaimer: str


class AssessmentScoreRead(BaseModel):
    id: str
    engagement_id: str
    process_key: str
    version: int
    generator: str
    payload: AssessmentScorePayload
    created_at: datetime
    updated_at: datetime


class ScoreVersionSummary(BaseModel):
    version: int
    generator: str
    index: float
    band: Band
    created_at: datetime


def band_for_index(index: float) -> Band:
    """Map a 0-100 index onto its band. See P2P_AUTOMATION_MODEL.md §5."""
    for upper, band in BAND_THRESHOLDS:
        if index <= upper:
            return band
    return "optimised"


def level_label_for(score: float) -> str:
    """The nearest rung on the maturity ladder, for display beside a step score."""
    labels = {
        0: "Manual",
        1: "Recorded",
        2: "Standardised",
        3: "Integrated",
        4: "Automated",
        5: "Optimised",
    }
    return labels.get(round(score), "")


def as_dict(payload: AssessmentScorePayload) -> dict[str, Any]:
    return payload.model_dump(mode="json")
