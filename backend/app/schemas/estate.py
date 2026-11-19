"""Estate assessment — the inventories, the four estate assessments, and their payloads.

docs/phases/PHASE6_PLAN.md, docs/phases/PHASE8_PLAN.md and
docs/reference/DD_ASSESSMENT_FRAMEWORK.md.

Three layers, the same split as the business-process assessment:

* **content** — field definitions, questions and gap themes, loaded from
  `reference/estate/*.yaml`;
* **working data** — the inventory the target supplies and the analyst's answers, edited
  continuously and never versioned;
* **the score** — a point-in-time judgement, versioned and stored, with consultant edits to
  its gaps overlaid at read time so a re-score never discards them.

Phase 8 (2026-11-18): every register is a register of **themes**. Rules still fire on
single applications, platforms, roles and projects, but those are observations — the
evidence under a theme — never a gap of their own. A diligence reports what moves the value
of the deal, not a defect list per system.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.assess import Band

InventoryKind = Literal["application", "data_domain", "platform", "it_role", "it_contract", "it_project", "cyber_tool"]
EstateDomain = Literal["applications", "data_tech", "team_governance", "strategy_projects"]
FieldType = Literal["text", "long_text", "select", "multi_select", "date", "number", "process_list", "app_refs"]
Severity = Literal["High", "Medium", "Low"]
SEVERITIES: tuple[Severity, ...] = ("High", "Medium", "Low")
DdType = Literal["enterprise", "product", "blended"]

# The deal-impact lens: why a gap matters to the value of the deal [DD_master §1.1, p. 70]
# — a one-time cost, a recurring cost, a risk, or a dependency for what comes after close.
ImpactLens = Literal["one_off_investment", "run_cost", "plan_risk", "continuity", "compliance", "integration"]
IMPACT_LABELS: dict[str, str] = {
    "one_off_investment": "One-off investment",
    "run_cost": "Run-rate cost",
    "plan_risk": "Risk to the plan",
    "continuity": "Continuity risk",
    "compliance": "Compliance exposure",
    "integration": "Integration or separation dependency",
}

INVENTORY_KINDS: tuple[InventoryKind, ...] = (
    "application",
    "data_domain",
    "platform",
    "it_role",
    "it_contract",
    "it_project",
    "cyber_tool",
)
ESTATE_SUBJECT = "estate"  # the subject id for the questionnaire answered once per engagement
SCORE_SCHEMA_VERSION = 2  # payloads below this predate the theme registers: re-score


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
    # Earlier names for the sheet, still accepted on upload (Phase 8 renamed some).
    sheet_aliases: list[str] = Field(default_factory=list)
    ref_prefix: str
    source: str = ""
    # Rows the template writes with only the name filled in (the cyber tools checklist).
    # A returned row that is still just its seeded name is skipped, not created.
    seed_names: list[str] = Field(default_factory=list)
    fields: list[FieldDef]


class InventoryDefinition(BaseModel):
    model_config = {"extra": "forbid"}

    kinds: dict[InventoryKind, KindDef]


class ThemeDef(BaseModel):
    """One gap theme: what a finding of this kind means for the deal, and what to do.

    A theme fires when any observation is raised against it. The gap it produces carries
    the theme's headline, implication, impact lens and action; the observations become its
    evidence. Severity is the highest of its observations' — each observation states its
    own, or takes `severity` here.
    """

    model_config = {"extra": "forbid"}

    id: str
    area: str  # a diligence area id in reference/report/report.yaml
    headline: str
    implication: str
    impact: list[ImpactLens] = Field(min_length=1)
    action: str  # "Target should…"; may use {subjects} and {count}
    severity: Severity = "Medium"


class JudgementOption(BaseModel):
    model_config = {"extra": "forbid"}

    label: str
    # Maturity credit, 0..1. None: the question does not apply and is left out of the score.
    value: float | None = None
    # A weak answer raises an observation against the question's theme.
    finding: str | None = None
    severity: Severity | None = None


class JudgementSection(BaseModel):
    model_config = {"extra": "forbid"}

    key: str
    label: str
    weight: float = 1.0
    source: str = ""


class JudgementQuestion(BaseModel):
    """A question the analyst answers from interviews and evidence, one option each."""

    model_config = {"extra": "forbid"}

    id: str
    section: str
    text: str
    help: str = ""
    source: str = ""
    weight: float = 1.0
    theme: str | None = None
    # Empty: every deal. Otherwise only these DD types see it.
    applies_to: list[DdType] = Field(default_factory=list)
    # Only where AI is material to the target (scope rule A11).
    requires_ai: bool = False
    options: list[JudgementOption]


class ScaleQuestion(BaseModel):
    """An application question answered on a numbered scale."""

    model_config = {"extra": "forbid"}

    id: str
    group: Literal["criticality", "automation", "ai"]
    text: str
    help: str = ""
    scale: tuple[int, int]
    levels: dict[int, str]


class ApplicationRules(BaseModel):
    model_config = {"extra": "forbid"}

    critical_min: int
    manual_automation_max: int
    weak_process_bands: list[str]
    ad_hoc_type: str
    eol_lifecycles: list[str]
    high_customisation: list[str]
    manual_integration: list[str]
    weak_dr: list[str]
    duplication_exempt_categories: list[str] = Field(default_factory=list)
    analytics_category: str
    ai_low_max: float
    ai_min_answered: int


class ApplicationsConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    questions: list[ScaleQuestion]
    portfolio_sections: list[JudgementSection]
    portfolio_questions: list[JudgementQuestion]
    rules: ApplicationRules
    themes: list[ThemeDef]


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
    theme: str


class CheckSection(BaseModel):
    model_config = {"extra": "forbid"}

    key: str
    label: str
    checks: list[Check]


class DataTechRules(BaseModel):
    model_config = {"extra": "forbid"}

    domain_score_below: float
    engineering_high_on_fail: list[str] = Field(default_factory=list)
    weak_dr: list[str]
    critical_min: int


class DataTechConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    domain_questions: list[OptionQuestion]
    platform_questions: list[OptionQuestion]
    check_statuses: dict[str, float | None]
    check_sections: list[CheckSection]
    section_weights: dict[str, float]
    # Cyber tools inventory: a tool purpose (matched on the row's name) → the checks it
    # is evidence for. A tool is never a pass; a tool the target says it lacks is a fail.
    tool_checks: dict[str, list[str]] = Field(default_factory=dict)
    rules: DataTechRules
    themes: list[ThemeDef]


class TeamRules(BaseModel):
    model_config = {"extra": "forbid"}

    critical_min: int
    outsourced_share_max: float
    short_tenure_years: float
    short_tenure_share: float
    contract_months: int


class TeamGovernanceConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    sections: list[JudgementSection]
    questions: list[JudgementQuestion]
    rules: TeamRules
    themes: list[ThemeDef]


class ProjectRules(BaseModel):
    model_config = {"extra": "forbid"}

    open_statuses: list[str]
    planned_status: str
    done_statuses: list[str]
    burn_gap_points: float
    vendor_share: float
    critical_min: int
    stop_triage: str
    priority_triage: list[str]
    off_track: str
    delivery_section_weight: float


class StrategyProjectsConfig(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    sections: list[JudgementSection]
    questions: list[JudgementQuestion]
    project_questions: list[JudgementQuestion]
    rules: ProjectRules
    themes: list[ThemeDef]


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
    group_label: str = ""
    source: str = ""
    options: list[AnswerOption]


class EstateSubject(BaseModel):
    """One thing being assessed: an inventory item, or the questionnaire answered once."""

    id: str
    kind: Literal["application", "data_domain", "platform", "it_project", "estate"]
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
    # question_id -> what the target's inventories say about it (cyber tools, IT team).
    # Shown beside the question; never an answer by itself.
    evidence: dict[str, list[str]] = Field(default_factory=dict)
    # Which variant of the questionnaire this deal sees.
    dd_type: str = "enterprise"
    ai_material: bool = False
    latest_score_version: int | None = None


# ===================================================================== score payloads


class GapObservation(BaseModel):
    """One rule firing or one weak answer — the evidence under a theme."""

    text: str
    severity: Severity
    subjects: list[str] = Field(default_factory=list)
    source: str = ""


class GapGenerated(BaseModel):
    headline: str
    evidence: list[str]
    action: str
    severity: Severity


class Gap(BaseModel):
    key: str  # theme:<id>, stable across re-scores so edits survive
    display_id: str
    theme: str
    area: str
    headline: str
    evidence: list[str]
    implication: str
    impact: list[str]
    action: str
    severity: Severity
    subjects: list[str] = Field(default_factory=list)
    observations: list[GapObservation] = Field(default_factory=list)
    generated: GapGenerated | None = None
    edited: bool = False


class GapCounts(BaseModel):
    High: int = 0
    Medium: int = 0
    Low: int = 0


class SectionScore(BaseModel):
    key: str
    label: str
    score: float | None
    weight: float
    evidence: int


class _ScoreBase(BaseModel):
    schema_version: int = SCORE_SCHEMA_VERSION
    generator: str
    generated_at: datetime
    index: float | None = None
    band: Band | None = None
    band_label: str = ""
    band_meaning: str = ""
    gaps: list[Gap]
    gap_counts: GapCounts
    coverage_note: str = ""
    executive_summary: str = ""
    pointers: list[str] = Field(default_factory=list)


# ------------------------------------------------------------------ applications


class ApplicationResult(BaseModel):
    item_id: str
    ref: str
    name: str
    category: str = ""
    answered: int
    question_count: int
    criticality: int | None = None
    automation: int | None = None
    automation_label: str = ""
    ai: int | None = None
    ai_label: str = ""
    lifecycle: str = ""
    # What the facts say about it, in a word or two: "End of life", "Key person"…
    flags: list[str] = Field(default_factory=list)


class ApplicationCounts(BaseModel):
    applications: int = 0
    assessed: int = 0
    critical: int = 0
    end_of_life: int = 0
    manual_critical: int = 0


class ApplicationsScorePayload(_ScoreBase):
    domain: Literal["applications"] = "applications"
    # Criticality-weighted automation level × 20 — the same 0-100 scale and bands as the
    # business processes. None until at least one application has an automation answer.
    ai_index: float | None = None
    counts: ApplicationCounts
    applications: list[ApplicationResult]
    portfolio: list[SectionScore] = Field(default_factory=list)


# ------------------------------------------------------------------ data & infrastructure


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
    # analyst: answered on the questionnaire; inventory: defaulted from the cyber tools
    # inventory because the analyst has not answered it yet.
    source: Literal["analyst", "inventory", ""] = ""
    evidence: list[str] = Field(default_factory=list)


class DataTechScorePayload(_ScoreBase):
    domain: Literal["data_tech"] = "data_tech"
    sections: list[SectionScore]
    domains: list[DomainResult]
    platforms: list[PlatformResult]
    checks: list[CheckResult]


# ------------------------------------------------------------------ team & governance


class PeopleSummary(BaseModel):
    """Arithmetic on the IT team inventory — facts the target supplied, counted."""

    headcount: int = 0
    in_house: int = 0
    outsourced: int = 0
    contractor: int = 0
    parent_shared: int = 0
    outsourced_share_pct: float | None = None
    sole_holders: list[str] = Field(default_factory=list)
    single_person_critical_apps: list[str] = Field(default_factory=list)
    short_tenure_share_pct: float | None = None
    has_leadership_role: bool = False
    by_function: dict[str, int] = Field(default_factory=dict)


class TeamGovernanceScorePayload(_ScoreBase):
    domain: Literal["team_governance"] = "team_governance"
    sections: list[SectionScore]
    people: PeopleSummary
    answered: int = 0
    question_count: int = 0


# ------------------------------------------------------------------ strategy & projects


class ProjectResult(BaseModel):
    item_id: str
    ref: str
    name: str
    status: str = ""
    allocated: float | None = None
    used: float | None = None
    remaining: float | None = None
    pct_complete: float | None = None
    spend_pct: float | None = None
    planned_end: str = ""
    triage: str = ""
    confidence: str = ""
    flags: list[str] = Field(default_factory=list)


class PortfolioSummary(BaseModel):
    projects: int = 0
    open: int = 0
    planned: int = 0
    allocated_total: float | None = None
    used_total: float | None = None
    # Remaining allocation on in-flight and planned projects: what the buyer inherits.
    remaining_commitment: float | None = None
    change_budget: float | None = None
    change_budget_year: str = ""
    unfunded: float | None = None
    over_budget: int = 0
    late: int = 0
    stop_candidates: int = 0


class StrategyProjectsScorePayload(_ScoreBase):
    domain: Literal["strategy_projects"] = "strategy_projects"
    sections: list[SectionScore]
    projects: list[ProjectResult]
    portfolio: PortfolioSummary
    answered: int = 0
    question_count: int = 0


class EstateScoreRead(BaseModel):
    id: str
    engagement_id: str
    domain: EstateDomain
    version: int
    generator: str
    # One of the four payloads, by `domain`. Typed loosely at the envelope so the
    # frontend can narrow on `payload.domain`.
    payload: dict[str, Any]
    created_at: datetime


class GapNoteWrite(BaseModel):
    """A consultant's edit to one gap. Omitted fields keep the generated text."""

    model_config = {"extra": "forbid"}

    severity: Severity | None = None
    headline: str | None = None
    evidence: list[str] | None = None
    action: str | None = None


# ===================================================================== LLM contract


class LlmEstateSummary(BaseModel):
    model_config = {"extra": "ignore"}

    executive_summary: str
    pointers: list[str] = Field(default_factory=list)
