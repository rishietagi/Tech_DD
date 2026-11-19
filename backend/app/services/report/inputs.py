"""Everything the report is built from, gathered once into plain data.

The builder is pure — it takes this and returns a payload — so it can be tested against a
hand-made `ReportInputs` without a database, and so it is obvious what the report depends
on: every earlier module, and nothing else.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Item:
    """One inventory item: its ref and its fields."""

    ref: str
    fields: dict[str, Any]

    def text(self, key: str) -> str:
        value = self.fields.get(key)
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return "" if value is None else str(value).strip()

    def listed(self, key: str) -> list[str]:
        value = self.fields.get(key)
        return [str(v) for v in value] if isinstance(value, list) else []

    @property
    def name(self) -> str:
        return self.text("name") or self.ref


@dataclass
class IrlRequest:
    id: str
    question: str
    scope_area: str
    source_row_id: str | None
    kind: str
    status: str  # not_received | received_partially | received_completely
    follow_ups: list[str] = field(default_factory=list)


@dataclass
class ProcessResult:
    key: str
    name: str
    short_name: str
    index: float
    band: str
    band_label: str


@dataclass
class ReportInputs:
    deal_name: str
    target_name: str
    investor_name: str
    dd_type: str
    dd_mix: int | None
    access_level: str
    today: date
    cutoff: date | None
    scope_rows: list[dict[str, Any]]
    irl: list[IrlRequest]
    research_summary: str
    research_what_they_do: str
    applications_score: dict[str, Any] | None
    data_tech_score: dict[str, Any] | None
    processes: list[ProcessResult]
    budget: dict[str, Any] | None
    budget_saved: bool
    inventory: dict[str, list[Item]]
    process_names: dict[str, str]
    assets: list[dict[str, str]] = field(default_factory=list)
    # Phase 8 assessments; None until scored.
    team_governance_score: dict[str, Any] | None = None
    strategy_projects_score: dict[str, Any] | None = None

    def items(self, kind: str) -> list[Item]:
        return self.inventory.get(kind, [])
