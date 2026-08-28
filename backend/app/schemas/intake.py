"""One Pydantic schema per intake section (initial_plan.md §3).

Each section schema has every field Optional so `PATCH .../intake/{section}` can
save a partial draft. `POST /submit` re-validates the same data against the
`*Required` companion, which mirrors the section but with the `*` fields in
initial_plan.md §3 made mandatory. This keeps one field list per section instead
of duplicating them, while still enforcing the strict shape at file-time.
"""

from datetime import date

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

from app.reference.enums import (
    AccessLevel,
    AiMlDependence,
    BudgetBand,
    BuildVsBuy,
    BusinessModel,
    CloudProvider,
    CodeAccess,
    ComplianceRegime,
    CoreSystem,
    CustomerConcentration,
    DataSensitivity,
    DdObjective,
    DdTypePreference,
    DealStage,
    DeliverableFormat,
    DigitalMaturity,
    HoldPeriod,
    HostingModel,
    InvestmentType,
    InvestorTechCapability,
    InvestorType,
    OutsourcingReliance,
    PostCloseIntent,
    ProcessType,
    RevenueModel,
    RevenueStage,
    Sector,
    Stake,
    TechIsProduct,
    ValueCreationLever,
)


class SectionBase(BaseModel):
    model_config = {"extra": "forbid", "use_enum_values": True}


# --- Step 1: Deal Context -----------------------------------------------------


class DealContext(SectionBase):
    deal_name: str | None = Field(default=None, min_length=1, max_length=255)
    context_narrative: str | None = Field(default=None, min_length=40)
    deal_stage: DealStage | None = None
    process_type: ProcessType | None = None
    source_of_deal: str | None = None


class DealContextRequired(DealContext):
    deal_name: str = Field(min_length=1, max_length=255)
    context_narrative: str = Field(min_length=40)
    deal_stage: DealStage
    process_type: ProcessType


# --- Step 2: Rationale ---------------------------------------------------------


class Rationale(SectionBase):
    rationale_narrative: str | None = Field(default=None, min_length=40)
    value_creation_levers: list[ValueCreationLever] | None = None
    deal_breakers: str | None = None
    known_concerns: str | None = None


class RationaleRequired(Rationale):
    rationale_narrative: str = Field(min_length=40)
    value_creation_levers: list[ValueCreationLever] = Field(min_length=1)


# --- Step 3: Deal Structure -----------------------------------------------------


class DealStructure(SectionBase):
    investment_type: InvestmentType | None = None
    stake: Stake | None = None
    stake_percent: float | None = Field(default=None, ge=0, le=100)
    post_close_intent: PostCloseIntent | None = None
    carve_out_or_tsa: bool | None = None
    hold_period_years: HoldPeriod | None = None


class DealStructureRequired(DealStructure):
    investment_type: InvestmentType
    stake: Stake
    post_close_intent: PostCloseIntent
    carve_out_or_tsa: bool


# --- Step 4: Investor -----------------------------------------------------------


class Investor(SectionBase):
    firm_name: str | None = Field(default=None, min_length=1, max_length=255)
    investor_type: InvestorType | None = None
    deal_lead_name: str | None = Field(default=None, min_length=1, max_length=255)
    deal_lead_email: EmailStr | None = None
    check_size: str | None = None
    enterprise_value: str | None = None
    existing_portfolio_overlap: str | None = None
    investor_tech_capability: InvestorTechCapability | None = None


class InvestorRequired(Investor):
    firm_name: str = Field(min_length=1, max_length=255)
    investor_type: InvestorType
    deal_lead_name: str = Field(min_length=1, max_length=255)
    deal_lead_email: EmailStr


# --- Step 5: Target Company ------------------------------------------------------


class TargetCompany(SectionBase):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    website: str | None = None
    sector: Sector | None = None
    line_of_business: str | None = Field(default=None, min_length=30)
    business_model: BusinessModel | None = None
    revenue_model: list[RevenueModel] | None = None
    digital_maturity: DigitalMaturity | None = None
    headcount: int | None = Field(default=None, ge=0)
    revenue_stage: RevenueStage | None = None
    hq_location: str | None = Field(default=None, min_length=1)
    geographies: list[str] | None = None
    customer_concentration: CustomerConcentration | None = None
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    ma_history: str | None = None


class TargetCompanyRequired(TargetCompany):
    company_name: str = Field(min_length=1, max_length=255)
    sector: Sector
    line_of_business: str = Field(min_length=30)
    business_model: BusinessModel
    revenue_model: list[RevenueModel] = Field(min_length=1)
    digital_maturity: DigitalMaturity
    headcount: int = Field(ge=0)
    revenue_stage: RevenueStage
    hq_location: str = Field(min_length=1)


# --- Step 6: Technology Profile ---------------------------------------------------


class TechnologyProfile(SectionBase):
    tech_is_product: TechIsProduct | None = None
    build_vs_buy: BuildVsBuy | None = None
    core_systems: list[CoreSystem] | None = None
    hosting_model: HostingModel | None = None
    cloud_providers: list[CloudProvider] | None = None
    known_tech_stack: str | None = None
    engineering_headcount: int | None = Field(default=None, ge=0)
    engineering_share_pct: float | None = Field(default=None, ge=0, le=100)
    outsourcing_reliance: OutsourcingReliance | None = None
    ai_ml_dependence: AiMlDependence | None = None
    data_sensitivity: list[DataSensitivity] | None = None
    compliance_regimes: list[ComplianceRegime] | None = None
    known_incidents: str | None = None


class TechnologyProfileRequired(TechnologyProfile):
    tech_is_product: TechIsProduct
    build_vs_buy: BuildVsBuy
    hosting_model: HostingModel
    ai_ml_dependence: AiMlDependence
    data_sensitivity: list[DataSensitivity] = Field(min_length=1)


# --- Step 7: Diligence Objectives & Logistics -------------------------------------


class DiligenceObjectives(SectionBase):
    dd_objectives: list[DdObjective] | None = None
    access_level: AccessLevel | None = None
    code_access: CodeAccess | None = None
    deliverable_format: list[DeliverableFormat] | None = None
    timeline_weeks: int | None = Field(default=None, ge=1)
    bid_date: date | None = None
    ic_date: date | None = None
    budget_band: BudgetBand | None = None
    clean_team_constraints: str | None = None
    dd_type_preference: DdTypePreference | None = None
    dd_type_override_reason: str | None = None


class DiligenceObjectivesRequired(DiligenceObjectives):
    dd_objectives: list[DdObjective] = Field(min_length=1)
    access_level: AccessLevel
    code_access: CodeAccess
    deliverable_format: list[DeliverableFormat] = Field(min_length=1)
    timeline_weeks: int = Field(ge=1)
    dd_type_preference: DdTypePreference
    dd_type_override_reason: str | None = Field(default=None, validate_default=True)

    @field_validator("dd_type_override_reason", mode="after")
    @classmethod
    def _validate_override_reason(cls, v: str | None, info: ValidationInfo) -> str | None:
        preference = info.data.get("dd_type_preference")
        if preference is not None and preference != DdTypePreference.let_platform_decide.value and not v:
            raise ValueError("dd_type_override_reason is required when dd_type_preference overrides the default")
        return v


SECTION_DRAFT_MODELS: dict[str, type[SectionBase]] = {
    "context": DealContext,
    "rationale": Rationale,
    "structure": DealStructure,
    "investor": Investor,
    "target": TargetCompany,
    "technology": TechnologyProfile,
    "objectives": DiligenceObjectives,
}

SECTION_REQUIRED_MODELS: dict[str, type[SectionBase]] = {
    "context": DealContextRequired,
    "rationale": RationaleRequired,
    "structure": DealStructureRequired,
    "investor": InvestorRequired,
    "target": TargetCompanyRequired,
    "technology": TechnologyProfileRequired,
    "objectives": DiligenceObjectivesRequired,
}

SECTION_JSON_COLUMNS: dict[str, str] = {
    "context": "context_json",
    "rationale": "rationale_json",
    "structure": "structure_json",
    "investor": "investor_json",
    "target": "target_json",
    "technology": "technology_json",
    "objectives": "objectives_json",
}


class IntakeFull(BaseModel):
    """Full intake, assembled from all seven sections. Used by the (Phase 2) ScopeGenerator."""

    context: DealContextRequired
    rationale: RationaleRequired
    structure: DealStructureRequired
    investor: InvestorRequired
    target: TargetCompanyRequired
    technology: TechnologyProfileRequired
    objectives: DiligenceObjectivesRequired


class IntakeDraft(BaseModel):
    """Whatever has been saved so far — every section optional."""

    context: DealContext | None = None
    rationale: Rationale | None = None
    structure: DealStructure | None = None
    investor: Investor | None = None
    target: TargetCompany | None = None
    technology: TechnologyProfile | None = None
    objectives: DiligenceObjectives | None = None
