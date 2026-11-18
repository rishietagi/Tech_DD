"""The final report — content config, payload and edits. docs/phases/PHASE7_PLAN.md Part D.

The payload is built deterministically from every earlier module; an LLM may rewrite its
prose; a consultant may edit anything. Edits are an overlay keyed on stable element keys
(`exec.EN-01.findings`, `supporting.applications.panel`), applied at read time, so a
regeneration keeps them for as long as the element still exists.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["High", "Medium", "Low", "Not assessed"]
RISK_LEVELS: tuple[RiskLevel, ...] = ("High", "Medium", "Low", "Not assessed")
BlockKind = Literal["paragraph", "bullets", "table", "diagram", "image"]


# ===================================================================== content (YAML)


class RouteRule(BaseModel):
    model_config = {"extra": "forbid"}

    prefer: list[str] = Field(default_factory=list)
    fallback: str


class SectionDef(BaseModel):
    model_config = {"extra": "forbid"}

    title: str


class ReportConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    cover: dict[str, str]
    dd_labels: dict[str, str]
    executive_titles: dict[str, str]
    context: dict[str, Any]
    routing: dict[str, RouteRule]
    max_findings_per_area: int
    max_actions_per_area: int
    implications: dict[str, str]
    actions: dict[str, str]
    no_findings: str
    not_assessed: str
    limitations: dict[str, str]
    limitation_routing: dict[str, str]
    supporting: dict[str, list[str]]
    sections: dict[str, SectionDef]
    appendix: list[str]
    appendix_titles: dict[str, str]
    source_line: str
    glossary: dict[str, str]


# ===================================================================== payload


class Cover(BaseModel):
    codename: str
    title: str
    subtitle: str
    date_label: str


class Context(BaseModel):
    objective: str
    approach: str
    outcome: str
    key_areas: list[str]
    cutoff: str


class GlossaryEntry(BaseModel):
    term: str
    expansion: str


class ScopeArea(BaseModel):
    area_id: str
    title: str
    considerations: list[str]
    include: bool = True


class Limitation(BaseModel):
    area_id: str
    title: str
    items: list[str]
    include: bool = True


class ExecutiveRow(BaseModel):
    area_id: str
    sn: int
    title: str
    findings: list[str]
    implication: str
    risk: RiskLevel
    actions: list[str]
    investment: str = "XXX"
    # What the row was built from, so a reader can trace every finding to the register.
    gap_keys: list[str] = Field(default_factory=list)
    include: bool = True


class Block(BaseModel):
    id: str
    kind: BlockKind
    title: str = ""
    text: str = ""
    items: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    diagram: dict[str, Any] | None = None
    asset_id: str | None = None
    include: bool = True


class ReportSection(BaseModel):
    id: str
    title: str
    panel: str = ""
    blocks: list[Block] = Field(default_factory=list)
    include: bool = True


class ReportPayload(BaseModel):
    schema_version: Literal[1] = 1
    generator: str
    skill_versions: dict[str, str] = Field(default_factory=dict)
    generated_at: datetime
    dd_type: str
    dd_mix: int | None = None
    target_name: str = ""
    investor_name: str = ""
    cover: Cover
    context: Context
    glossary: list[GlossaryEntry]
    in_scope: list[ScopeArea]
    limitations: list[Limitation]
    executive_title: str
    executive: list[ExecutiveRow]
    supporting: list[ReportSection]
    appendix: list[ReportSection]
    source_line: str
    # Filled at read time from the overlay: the keys a consultant has changed.
    edited_keys: list[str] = Field(default_factory=list)


class ReportRead(BaseModel):
    id: str
    engagement_id: str
    version: int
    generator: str
    payload: ReportPayload
    created_at: datetime


class ReportEditWrite(BaseModel):
    """A consultant's edit to one element. The value's shape follows the element:
    a string for text, a list of strings for bullets, a bool for `include`, a list of
    rows for a table."""

    model_config = {"extra": "forbid"}

    value: Any


class ReportAssetRead(BaseModel):
    id: str
    title: str
    caption: str
    mime: str
    created_at: datetime


class ReportGenerateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    generator: str | None = None


# ===================================================================== LLM contract


class LlmExecutiveRow(BaseModel):
    model_config = {"extra": "ignore"}

    area_id: str
    findings: list[str]
    implication: str


class LlmExecutive(BaseModel):
    model_config = {"extra": "ignore"}

    rows: list[LlmExecutiveRow]


class LlmNarrative(BaseModel):
    model_config = {"extra": "ignore"}

    objective: str | None = None
    approach: str | None = None
    outcome: str | None = None
    panels: dict[str, str] = Field(default_factory=dict)
