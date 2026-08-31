"""Scope-of-work payloads.

v1 is the Phase 1 placeholder shape and is retained so existing rows still deserialise.
v2 is the KPMG deck: rows in the house taxonomy, plus the classification, sequencing,
cost plan, exclusions and provenance that make the document defensible.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.reference.enums import DdType
from app.schemas.classification import Classification
from app.schemas.selection import Exclusion
from app.schemas.signals import FiredRule

# --------------------------------------------------------------------------- v1


class Workstream(BaseModel):
    """Phase 1 placeholder shape. Retained for backwards compatibility only."""

    name: str
    summary: str
    objectives: list[str]
    key_questions: list[str]
    evidence_requests: list[str]


class ScopeOfWorkPayload(BaseModel):
    schema_version: Literal[1] = 1
    dd_type: DdType | None = None
    dd_mix: int | None = None
    is_placeholder: bool
    placeholder_notice: str | None = None
    workstreams: list[Workstream]


# --------------------------------------------------------------------------- v2


class ScopeLine(BaseModel):
    """One line of client-facing scope-of-work text."""

    text: str
    source_provenance: Literal["sourced", "extended"] = "sourced"


class ScopedRow(BaseModel):
    """One KPMG row as it appears in the delivered document."""

    id: str
    sn: int
    deck: Literal["product", "enterprise"]

    # Client-facing. `title` is the Objective (product) or Focus Area (enterprise);
    # `lines` are the Scope of Work sentence(s) or the Key considerations bullets.
    title: str
    lines: list[ScopeLine]

    tier: int = Field(ge=0, le=3)
    tier_name: str
    tier_reason: str
    adjustments: list[str] = Field(default_factory=list)

    evidence_requests: list[str] = Field(default_factory=list)
    triggered_by: list[str] = Field(default_factory=list)
    workstreams: list[str] = Field(default_factory=list)
    dd_master_ref: str | None = None
    out_of_scope_note: str | None = None

    # Human override (DD_master G6). The engine's originals are kept alongside the
    # edit rather than replaced, so a reviewer can see what was changed and why.
    edited_by_human: bool = False
    original_tier: int | None = None
    original_title: str | None = None
    override_reason: str | None = None


class SequencePhase(BaseModel):
    """A week-banded slice of the plan. DD_master §7's iterative model, made concrete."""

    name: str
    weeks: str
    focus: str
    # What the phase hands to the next one. The broad pass exists to produce the areas
    # of focus that the deep dive then works on, and a plan that does not state that
    # handoff reads as two unrelated activities. Optional: the closing phase produces
    # the report itself, not an input to anything further.
    output: str | None = None
    row_ids: list[str] = Field(default_factory=list)


class CostLine(BaseModel):
    category: Literal["one_time", "recurring"]
    label: str
    basis: str


class CostPlan(BaseModel):
    """What the scope will produce on cost — always ranges, never point estimates.

    DD_master §8.3 is emphatic: "cost estimates provided to the deal team should be
    order-of-magnitude ranges" and every estimate documents its assumptions.
    """

    approach: str
    lines: list[CostLine] = Field(default_factory=list)
    assumptions_register: list[str] = Field(default_factory=list)
    required: bool = False


class TeamShape(BaseModel):
    core_team: list[str] = Field(default_factory=list)
    specialists: list[str] = Field(default_factory=list)
    note: str | None = None


class ScopeOfWorkPayloadV2(BaseModel):
    """The delivered scope of work."""

    schema_version: Literal[2] = 2
    is_placeholder: bool = False
    generator: str
    library_version: str
    rules_version: str
    prompt_version: str | None = None

    deck_title: str
    deck_subtitle: str

    classification: Classification
    engagement_summary: str
    objectives: list[str] = Field(default_factory=list)

    rows: list[ScopedRow]
    sequencing: list[SequencePhase] = Field(default_factory=list)
    cost_plan: CostPlan
    team_shape: TeamShape
    diligence_risks: list[str] = Field(default_factory=list)
    exclusions: list[Exclusion] = Field(default_factory=list)
    provenance: list[FiredRule] = Field(default_factory=list)

    # Content blocks injected by the C-rules (ERP cost note, data-room map, etc.).
    notes: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def dd_type(self) -> DdType:
        return DdType(self.classification.dd_type.value)

    @property
    def dd_mix(self) -> int:
        return self.classification.dd_mix


AnyScopePayload = ScopeOfWorkPayload | ScopeOfWorkPayloadV2


# ------------------------------------------------------------------------ reads


class ScopeOfWorkRead(BaseModel):
    id: str
    engagement_id: str
    version: int
    generator: str
    dd_type: str | None = None
    dd_mix: int | None = None
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ScopeOfWorkVersionSummary(BaseModel):
    version: int
    generator: str
    created_at: datetime

    model_config = {"from_attributes": True}
