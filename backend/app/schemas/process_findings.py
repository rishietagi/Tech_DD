"""Findings for the business-process assessments, in the estate's theme shape.

A separate module because `schemas.estate` imports from `schemas.assess` — the gap and
theme models live there, and the process score read needs both.
"""

from pydantic import BaseModel, Field

from app.schemas.assess import AssessmentScoreRead, Band
from app.schemas.estate import Gap, GapCounts, Severity, ThemeDef

PROCESS_THEME_IDS = ("process_manual", "process_broken_cycle", "process_weak_step")


class ProcessFindingRules(BaseModel):
    model_config = {"extra": "forbid"}

    manual_bands: dict[Band, Severity]
    weak_step_max: float = Field(ge=0, le=5)
    heavy_weight: float = Field(gt=0, le=100)
    cycle_gap: float = Field(gt=0, le=5)
    named_steps: int = Field(ge=1, le=6)


class ProcessFindingsConfig(BaseModel):
    """`reference/processes/_findings.yaml`."""

    model_config = {"extra": "forbid"}

    version: str
    rules: ProcessFindingRules
    themes: list[ThemeDef]


class ProcessScoreRead(AssessmentScoreRead):
    """A process score with its findings, edits applied — computed on read, so a score
    stored before findings existed still shows them, and an edit shows without re-scoring."""

    gaps: list[Gap] = Field(default_factory=list)
    gap_counts: GapCounts = Field(default_factory=GapCounts)
