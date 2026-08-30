"""One Pydantic schema per intake section (docs/phases/PHASE1_PLAN.md §3).

Each section schema has every field Optional so `PATCH .../intake/{section}` can
save a partial draft. `POST /submit` re-validates the same data against the
`*Required` companion. Only `sector` and `line_of_business` on Target Company are
actually mandatory to file — every other field across every step is optional, so an
engagement can be submitted with a mostly-empty intake.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.reference.enums import (
    AccessLevel,
    AiMlDependence,
    BudgetBand,
    BuildVsBuy,
    BusinessModel,
    CloudProvider,
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
    OutsourcingReliance,
    PostCloseIntent,
    ProcessType,
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
    investor_firm_name: str | None = None


class DealContextRequired(DealContext):
    pass


# --- Step 2: Rationale ---------------------------------------------------------


class Rationale(SectionBase):
    rationale_narrative: str | None = Field(default=None, min_length=40)
    value_creation_levers: list[ValueCreationLever] | None = None
    deal_breakers: str | None = None
    focus_areas: str | None = None


class RationaleRequired(Rationale):
    pass


# --- Step 3: Deal Structure -----------------------------------------------------


class DealStructure(SectionBase):
    investment_type: InvestmentType | None = None
    stake: Stake | None = None
    stake_percent: float | None = Field(default=None, ge=0, le=100)
    post_close_intent: PostCloseIntent | None = None
    hold_period_years: HoldPeriod | None = None


class DealStructureRequired(DealStructure):
    pass


# --- Step 4: Target Company ------------------------------------------------------


class TargetCompany(SectionBase):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    website: str | None = None
    sector: Sector | None = None
    line_of_business: str | None = Field(default=None, min_length=30)
    business_model: BusinessModel | None = None
    digital_maturity: DigitalMaturity | None = None
    headcount: int | None = Field(default=None, ge=0)
    revenue_stage: RevenueStage | None = None
    company_revenue: str | None = None
    hq_location: str | None = Field(default=None, min_length=1)
    office_locations: str | None = None
    geographies: list[str] | None = None
    customer_concentration: CustomerConcentration | None = None
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    ma_history: str | None = None


class TargetCompanyRequired(TargetCompany):
    sector: Sector
    line_of_business: str = Field(min_length=30)


# --- Step 5: Technology Profile ---------------------------------------------------


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
    pass


# --- Step 6: Diligence Objectives & Logistics -------------------------------------


class DiligenceObjectives(SectionBase):
    dd_objectives: list[DdObjective] | None = None
    access_level: AccessLevel | None = None
    deliverable_format: list[DeliverableFormat] | None = None
    timeline_weeks: int | None = Field(default=None, ge=1)
    bid_date: date | None = None
    ic_date: date | None = None
    budget_band: BudgetBand | None = None
    dd_type_preference: DdTypePreference | None = None


class DiligenceObjectivesRequired(DiligenceObjectives):
    pass


SECTION_DRAFT_MODELS: dict[str, type[SectionBase]] = {
    "context": DealContext,
    "rationale": Rationale,
    "structure": DealStructure,
    "target": TargetCompany,
    "technology": TechnologyProfile,
    "objectives": DiligenceObjectives,
}

SECTION_REQUIRED_MODELS: dict[str, type[SectionBase]] = {
    "context": DealContextRequired,
    "rationale": RationaleRequired,
    "structure": DealStructureRequired,
    "target": TargetCompanyRequired,
    "technology": TechnologyProfileRequired,
    "objectives": DiligenceObjectivesRequired,
}

SECTION_JSON_COLUMNS: dict[str, str] = {
    "context": "context_json",
    "rationale": "rationale_json",
    "structure": "structure_json",
    "target": "target_json",
    "technology": "technology_json",
    "objectives": "objectives_json",
}


class IntakeFull(BaseModel):
    """Full intake, assembled from all six sections. Used by the (Phase 2) ScopeGenerator."""

    context: DealContextRequired
    rationale: RationaleRequired
    structure: DealStructureRequired
    target: TargetCompanyRequired
    technology: TechnologyProfileRequired
    objectives: DiligenceObjectivesRequired


class IntakeDraft(BaseModel):
    """Whatever has been saved so far — every section optional."""

    context: DealContext | None = None
    rationale: Rationale | None = None
    structure: DealStructure | None = None
    target: TargetCompany | None = None
    technology: TechnologyProfile | None = None
    objectives: DiligenceObjectives | None = None
