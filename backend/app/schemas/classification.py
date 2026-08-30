"""Classification — the archetype verdict and how it was reached.

The user's declared `dd_type_preference` always wins (DD_master G6), but the engine's
own computation is never discarded: it is retained alongside so a disagreement between
the two is visible rather than silently resolved. That disagreement is informative —
it tells a reviewer the intake and the declaration point different ways.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.signals import Signal


class DdType(str, Enum):
    enterprise = "enterprise"
    product = "product"
    blended = "blended"


Confidence = Literal["high", "medium", "low"]


class Classification(BaseModel):
    """Which deck to emit, and the reasoning behind it."""

    dd_type: DdType = Field(description="The archetype actually used for this scope")
    dd_mix: int = Field(ge=0, le=100, description="0 = pure enterprise, 100 = pure product")
    confidence: Confidence

    computed_dd_type: DdType = Field(description="What the engine derived, before any override")
    computed_dd_mix: int = Field(ge=0, le=100)

    override_applied: bool = False
    override_source: str | None = Field(
        default=None, description="The intake value that overrode the computed archetype"
    )

    signals: list[Signal] = Field(default_factory=list)
    unknown_count: int = 0
    confidence_reasons: list[str] = Field(default_factory=list)

    @property
    def disagrees(self) -> bool:
        """True when the user's declaration and the engine's derivation differ."""
        return self.override_applied and self.dd_type is not self.computed_dd_type

    @property
    def mix_signals(self) -> list[Signal]:
        return [s for s in self.signals if s.detail.get("mix_delta")]
