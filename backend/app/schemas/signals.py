"""Signals — the audit trail linking an intake answer to a scoping decision.

Every workstream that opens, every tier that moves, and the archetype mix itself trace
back to a Signal carrying the DD_master rule id that produced it. This is what lets a
reviewer ask "why is EN-04 at Tier 3?" and get an answer (DD_master G5).
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SignalEffect(str, Enum):
    mix_delta = "mix_delta"
    force_module = "force_module"
    cap_tier = "cap_tier"
    floor_tier = "floor_tier"
    tier_bump = "tier_bump"
    posture = "posture"
    inject_content = "inject_content"
    unknown = "unknown"


class Signal(BaseModel):
    """One rule firing — or, for a dormant rule, one input we could not see."""

    code: str = Field(description="DD_master §15 rule id, e.g. A2, M4, D1")
    label: str
    effect: SignalEffect
    source_field: str | None = None
    source_value: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    citation: str | None = None
    provenance: Literal["sourced", "extended"] = "sourced"

    @property
    def is_unknown(self) -> bool:
        return self.effect is SignalEffect.unknown

    def describe(self) -> str:
        """One line a reviewer can read."""
        if self.is_unknown:
            return f"{self.code}: {self.label} — not captured in this intake"
        if self.source_field and self.source_value is not None:
            return f"{self.code}: {self.label} ({self.source_field} = {self.source_value})"
        return f"{self.code}: {self.label}"


class FiredRule(BaseModel):
    """Provenance-footer entry: a rule that fired and what it did."""

    code: str
    label: str
    effect: SignalEffect
    detail: dict[str, Any] = Field(default_factory=dict)
    citation: str | None = None
    provenance: Literal["sourced", "extended"] = "sourced"

    @classmethod
    def from_signal(cls, signal: Signal) -> "FiredRule":
        return cls(
            code=signal.code,
            label=signal.label,
            effect=signal.effect,
            detail=signal.detail,
            citation=signal.citation,
            provenance=signal.provenance,
        )
