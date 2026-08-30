"""A selected scope row: which KPMG row is in scope, at what depth, and why."""

from pydantic import BaseModel, Field

from app.schemas.kpmg_library import ScopeRow

# DD_master §7. Tier 0 means explicitly excluded, with the reason stated.
TIER_NAMES = {
    0: "Not in scope",
    1: "Screen",
    2: "Assess",
    3: "Deep dive",
}


class SelectedRow(BaseModel):
    """One KPMG row that made it into the scope, with its audit trail."""

    row: ScopeRow
    deck: str
    tier: int = Field(ge=0, le=3)
    tier_reason: str
    triggered_by: list[str] = Field(default_factory=list, description="Rule ids that opened this row")
    adjustments: list[str] = Field(default_factory=list, description="Human-readable tier changes")
    out_of_scope_note: str | None = None

    model_config = {"arbitrary_types_allowed": True}

    @property
    def tier_name(self) -> str:
        return TIER_NAMES[self.tier]

    @property
    def in_scope(self) -> bool:
        return self.tier > 0


class Exclusion(BaseModel):
    """Something deliberately not covered, and why. DD_master G4."""

    subject: str
    reason: str
    rule_code: str | None = None
