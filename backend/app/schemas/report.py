"""The final report — content config, payload and edits. docs/phases/PHASE7_PLAN.md Part D.

The payload is built deterministically from every earlier module; an LLM may rewrite its
prose; a consultant may edit anything. Edits are an overlay keyed on stable element keys
(`exec.cyber.data_tech-recovery.headline`, `supporting.applications.panel`), applied at read time, so a
regeneration keeps them for as long as the element still exists.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["High", "Medium", "Low", "Not assessed"]
RISK_LEVELS: tuple[RiskLevel, ...] = ("High", "Medium", "Low", "Not assessed")
BlockKind = Literal["paragraph", "bullets", "table", "diagram", "image"]


# ===================================================================== content (YAML)


class AreaDef(BaseModel):
    """A diligence area of the executive summary. Gap themes name one by id."""

    model_config = {"extra": "forbid"}

    id: str
    title: str
    workstreams: list[str] = Field(default_factory=list)


class ProcessFindingDef(BaseModel):
    model_config = {"extra": "forbid"}

    area: str
    headline: str
    bullet: str
    implication: str
    action: str
    impact: list[str]
    bands: dict[str, Literal["High", "Medium", "Low"]]


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
    areas: list[AreaDef]
    max_findings_per_area: int
    max_bullets_per_finding: int
    process_finding: ProcessFindingDef
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


class ExecutiveFinding(BaseModel):
    """One finding of the executive summary — a row of the sample's Gaps & Risks table.

    Phase 8 (Rishi, 2026-11-18): one row per finding, each with its own risk and actions,
    grouped under its diligence area. Investment impact stays XXX for the engagement team.
    """

    key: str  # <assessment>-<theme>, e.g. applications-end_of_support; stable across versions
    headline: str
    bullets: list[str]
    implication: str = ""
    impact: list[str] = Field(default_factory=list)
    risk: RiskLevel
    actions: list[str]
    investment: str = "XXX"
    # Where it came from: the register entry ("AP-01") or the process.
    source: str = ""
    include: bool = True


class ExecutiveRow(BaseModel):
    """One diligence area of the executive summary and its findings."""

    area_id: str
    sn: int
    title: str
    findings: list[ExecutiveFinding] = Field(default_factory=list)
    # The area's highest risk across its included findings — the summary's RAG.
    risk: RiskLevel
    # Shown when the area has no findings: "No material gaps…" or "Not assessed…".
    note: str = ""
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
    schema_version: Literal[2] = 2
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


class LlmExecutiveFinding(BaseModel):
    model_config = {"extra": "ignore"}

    key: str
    headline: str
    bullets: list[str]
    implication: str = ""


class LlmExecutive(BaseModel):
    model_config = {"extra": "ignore"}

    findings: list[LlmExecutiveFinding]


class LlmNarrative(BaseModel):
    model_config = {"extra": "ignore"}

    objective: str | None = None
    approach: str | None = None
    outcome: str | None = None
    panels: dict[str, str] = Field(default_factory=dict)
