"""The strict contract for LLM-authored prose.

The model rewrites wording inside a document the rules engine already decided. It
cannot add, remove or re-tier a row, and it cannot invent an evidence request. Every
response is validated against this shape and then diffed against the skeleton; any
mismatch means the tailoring is discarded and the deterministic output ships instead.
"""

from pydantic import BaseModel, Field


class TailoredLine(BaseModel):
    """One rewritten scope-of-work line, pinned to its position in the row."""

    model_config = {"extra": "forbid"}

    index: int = Field(ge=0, description="Position within the row's lines, preserved exactly")
    text: str = Field(min_length=1)


class TailoredRow(BaseModel):
    """Rewritten prose for one KPMG row."""

    model_config = {"extra": "forbid"}

    row_id: str
    title: str = Field(min_length=1, description="The objective / focus area, tailored")
    lines: list[TailoredLine] = Field(default_factory=list)


class LlmTailoring(BaseModel):
    """The complete response the model must return."""

    model_config = {"extra": "forbid"}

    engagement_summary: str = Field(min_length=1)
    rows: list[TailoredRow] = Field(default_factory=list)


class TailoringRejected(Exception):
    """The model's output did not match the skeleton. Carries the reason for the log."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
