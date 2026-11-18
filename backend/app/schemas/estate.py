"""Estate assessment — the inventories, the two estate assessments, and their payloads.

docs/phases/PHASE6_PLAN.md and docs/reference/ESTATE_ASSESSMENT_MODEL.md.

Three layers, the same split as the business-process assessment:

* **content** — field definitions and questions, loaded from `reference/estate/*.yaml`;
* **working data** — the inventory the target supplies and the analyst's answers, edited
  continuously and never versioned;
* **the score** — a point-in-time judgement, versioned and stored, with consultant edits to
  its gaps overlaid at read time so a re-score never discards them.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.assess import Band

InventoryKind = Literal["application", "data_domain", "platform", "it_role", "it_contract"]
EstateDomain = Literal["applications", "data_tech"]
FieldType = Literal["text", "long_text", "select", "multi_select", "date", "process_list", "app_refs"]
Severity = Literal["High", "Medium", "Low"]
SEVERITIES: tuple[Severity, ...] = ("High", "Medium", "Low")

INVENTORY_KINDS: tuple[InventoryKind, ...] = (
    "application",
    "data_domain",
    "platform",
    "it_role",
    "it_contract",
)
ESTATE_SUBJECT = "estate"  # the subject id for estate-level checks


# ===================================================================== content (YAML)


class FieldDef(BaseModel):
    model_config = {"extra": "forbid"}

    key: str
    label: str
    type: FieldType
    required: bool = False
    options: list[str] = Field(default_factory=list)
    template_note: str = ""


class KindDef(BaseModel):
    model_config = {"extra": "forbid"}

    label: str
    sheet: str
    ref_prefix: str
    source: str = ""
    fields: list[FieldDef]


class InventoryDefinition(BaseModel):
    model_config = {"extra": "forbid"}

    kinds: dict[InventoryKind, KindDef]


class ScaleQuestion(BaseModel):
    """An application question answered on a numbered scale."""

    model_config = {"extra": "forbid"}

    id: str
    group: Literal["criticality", "business_fit", "technical_fit", "automation", "ai"]
    text: str
    help: str = ""
    scale: tuple[int, int]
    levels: dict[int, str]


class DispositionRules(BaseModel):
    model_config = {"extra": "forbid"}

    threshold: float
    matrix: dict[str, str]
    meanings: dict[str, str]
    eol_lifecycle: str
    eol_overrides: list[str]
    eol_becomes: str
    duplication_exempt_categories: list[str] = Field(default_factory=list)


class TechnicalHealthRules(BaseModel):
    model_config = {"extra": "forbid"}

    debt_weights: dict[str, float]
    debt_maps: dict[str, dict[str, float]]
    debt_bands: list[tuple[float, str]]
    critical_min: int
    weak_dr: list[str]


class ApplicationGapRules(BaseModel):
    model_config = {"extra": "forbid"}

    contract_months: int
    manual_automation_max: int
    weak_process_bands: list[str]
    incomplete_share: float
    key_person_min: int
    ad_hoc_type: str


class ApplicationsConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    questions: list[ScaleQuestion]
    disposition: DispositionRules
    technical_health: TechnicalHealthRules
    gaps: ApplicationGapRules
    hypotheses: dict[str, str]


class ValuedOption(BaseModel):
    model_config = {"extra": "forbid"}

    label: str
    # Share of the question's weight this option earns; None grants it in full where the
    # question does not apply.
    value: float | None


class OptionQuestion(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    text: str
    help: str = ""
    weight: float = 1.0
    options: list[ValuedOption]


class Check(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    text: str
    source: str = ""


class CheckSection(BaseModel):
    model_config = {"extra": "forbid"}

    key: str
    label: str
    checks: list[Check]


class DataTechGapRules(BaseModel):
    model_config = {"extra": "forbid"}

    domain_score_below: float
    no_owner_portfolio_min: int
    unknown_lifecycle_share: float
    engineering_high_on_fail: list[str] = Field(default_factory=list)


class DataTechConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    domain_questions: list[OptionQuestion]
    platform_questions: list[OptionQuestion]
    check_statuses: dict[str, float | None]
    check_sections: list[CheckSection]
    section_weights: dict[str, float]
    facility_categories: list[str] = Field(default_factory=list)
    gaps: DataTechGapRules
    hypotheses: dict[str, str]


# ===================================================================== inventory API


class ProcessRef(BaseModel):
    key: str
    name: str
    short_name: str


class InventoryItemRead(BaseModel):
    id: str
    kind: InventoryKind
    ref: str
    fields: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class InventoryRead(BaseModel):
    """Everything the inventory screens need: the definitions that build the forms, the
    items, and the processes an application can claim to support."""

    engagement_id: str
    definitions: dict[InventoryKind, KindDef]
    processes: list[ProcessRef]
    items: list[InventoryItemRead]


class InventoryItemCreate(BaseModel):
    model_config = {"extra": "forbid"}

    kind: InventoryKind
    fields: dict[str, Any] = Field(default_factory=dict)


class InventoryItemUpdate(BaseModel):
    """Partial: only the keys sent are changed. An empty string or empty list clears one."""

    model_config = {"extra": "forbid"}

    fields: dict[str, Any]


class InventoryImportSummary(BaseModel):
    kind: InventoryKind
    sheet: str
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    warnings: list[str] = Field(default_factory=list)


class InventoryImportResult(BaseModel):
    summaries: list[InventoryImportSummary]
    note: str = ""


# ===================================================================== answering view


class AnswerOption(BaseModel):
    value: str
    label: str


class EstateQuestion(BaseModel):
    id: str
    text: str
    help: str = ""
    group: str = ""
    options: list[AnswerOption]


class EstateSubject(BaseModel):
    """One thing being assessed: an inventory item, or the estate itself."""

    id: str
    kind: Literal["application", "data_domain", "platform", "estate"]
    ref: str
    name: str
    subtitle: str = ""
    answered: int
    question_count: int


class EstateAnswerRead(BaseModel):
    value: str = ""
    remarks: str = ""


class EstateAnswerWrite(BaseModel):
    """Both optional: `None` leaves a field alone, an empty string clears it."""

    model_config = {"extra": "forbid"}

    subject_id: str
    question_id: str
    value: str | None = None
    remarks: str | None = None


class EstateRead(BaseModel):
    engagement_id: str
    domain: EstateDomain
    subjects: list[EstateSubject]
    # Keyed by subject kind: application / data_domain / platform / estate.
    questions: dict[str, list[EstateQuestion]]
    # subject_id -> question_id -> answer
    answers: dict[str, dict[str, EstateAnswerRead]]
    latest_score_version: int | None = None


# ===================================================================== score payloads


class GapSubject(BaseModel):
    kind: str
    item_id: str = ""
    ref: str = ""
    name: str


class GapGenerated(BaseModel):
    description: str
    hypothesis: str
    severity: Severity


class Gap(BaseModel):
    key: str
    display_id: str
    scope: Literal["item", "portfolio"]
    category: str
    subject: GapSubject
    title: str
    findings: list[str]
    description: str
    hypothesis: str
    severity: Severity
    generated: GapGenerated | None = None
    edited: bool = False


class GapCounts(BaseModel):
    High: int = 0
    Medium: int = 0
    Low: int = 0
    item: int = 0
    portfolio: int = 0


class ApplicationResult(BaseModel):
    item_id: str
    ref: str
    name: str
    category: str = ""
    answered: int
    question_count: int
    assessed: bool
    partial: bool
    criticality: int | None = None
    business_fit: float | None = None
    technical_fit: float | None = None
    disposition: str
    disposition_statement: str
    consolidate_into: str | None = None
    automation: int | None = None
    automation_label: str = ""
    ai: int | None = None
    ai_label: str = ""
    debt: int | None = None
    debt_band: str | None = None
    spof_status: Literal["SPOF", "Check", "OK"] = "OK"
    spof: list[str] = Field(default_factory=list)
    spof_checks: list[str] = Field(default_factory=list)
    scalability_status: Literal["At risk", "Watch", "OK"] = "OK"
    scalability: list[str] = Field(default_factory=list)


class ApplicationCounts(BaseModel):
    applications: int = 0
    assessed: int = 0
    by_disposition: dict[str, int] = Field(default_factory=dict)
    high_debt: int = 0
    spof: int = 0
    scalability_risk: int = 0


class ApplicationsScorePayload(BaseModel):
    schema_version: int = 1
    domain: Literal["applications"] = "applications"
    generator: str
    generated_at: datetime
    # Criticality-weighted automation level × 20 — the same 0-100 scale and bands as the
    # business processes. None until at least one application has an automation answer.
    index: float | None = None
    band: Band | None = None
    band_label: str = ""
    band_meaning: str = ""
    ai_index: float | None = None
    counts: ApplicationCounts
    applications: list[ApplicationResult]
    gaps: list[Gap]
    gap_counts: GapCounts
    coverage_note: str = ""
    executive_summary: str = ""
    pointers: list[str] = Field(default_factory=list)


class SectionScore(BaseModel):
    key: str
    label: str
    score: float | None
    weight: float
    evidence: int


class DomainResult(BaseModel):
    item_id: str
    ref: str
    name: str
    sensitivity: str = ""
    holds_personal_data: bool = False
    owner_named: bool = False
    answered: int
    question_count: int
    score: int | None = None


class PlatformResult(BaseModel):
    item_id: str
    ref: str
    name: str
    category: str = ""
    lifecycle: str = ""
    answered: int
    question_count: int
    score: int | None = None
    hosted_apps: list[str] = Field(default_factory=list)


class CheckResult(BaseModel):
    id: str
    section: str
    text: str
    status: str  # pass | partial | fail | unknown | unanswered


class DataTechScorePayload(BaseModel):
    schema_version: int = 1
    domain: Literal["data_tech"] = "data_tech"
    generator: str
    generated_at: datetime
    index: float | None = None
    band: Band | None = None
    band_label: str = ""
    band_meaning: str = ""
    sections: list[SectionScore]
    domains: list[DomainResult]
    platforms: list[PlatformResult]
    checks: list[CheckResult]
    gaps: list[Gap]
    gap_counts: GapCounts
    coverage_note: str = ""
    executive_summary: str = ""
    pointers: list[str] = Field(default_factory=list)


class EstateScoreRead(BaseModel):
    id: str
    engagement_id: str
    domain: EstateDomain
    version: int
    generator: str
    # Applications or data & technology, by `domain`. Typed loosely at the envelope so
    # the frontend can narrow on `payload.domain`.
    payload: dict[str, Any]
    created_at: datetime


class GapNoteWrite(BaseModel):
    """A consultant's edit to one gap. Omitted fields keep the generated text."""

    model_config = {"extra": "forbid"}

    severity: Severity | None = None
    description: str | None = None
    hypothesis: str | None = None


# ===================================================================== LLM contract


class LlmEstateSummary(BaseModel):
    model_config = {"extra": "ignore"}

    executive_summary: str
    pointers: list[str] = Field(default_factory=list)
