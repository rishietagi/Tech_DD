"""Canonical enum values shared by models, schemas and /meta/enums.

Every enum the frontend needs to render a select/multiselect/toggle lives here so
option lists have one source of truth (docs/phases/PHASE1_PLAN.md §6).
"""

from enum import Enum


class EngagementStatus(str, Enum):
    draft = "draft"
    filed = "filed"
    scoped = "scoped"
    archived = "archived"


class DdType(str, Enum):
    enterprise = "enterprise"
    product = "product"
    blended = "blended"


class DealStage(str, Enum):
    exclusivity = "Exclusivity"
    bid_situation = "Bid situation"
    exploratory = "Exploratory"


class ProcessType(str, Enum):
    broad_auction = "Broad auction"
    limited_process = "Limited process"
    bilateral = "Bilateral"
    proprietary = "Proprietary"


class ValueCreationLever(str, Enum):
    organic_growth = "Organic growth"
    product_expansion = "Product expansion"
    buy_and_build = "Buy-and-build"
    cost_takeout = "Cost takeout"
    margin_expansion = "Margin expansion"
    geographic_expansion = "Geographic expansion"
    digital_or_ai_transformation = "Digital or AI transformation"
    multiple_arbitrage = "Multiple arbitrage"


class InvestmentType(str, Enum):
    strategic = "strategic"
    financial = "financial"


class Stake(str, Enum):
    majority = "majority"
    minority = "minority"


class PostCloseIntent(str, Enum):
    standalone = "Standalone"
    integrate_existing = "Integrate into existing platform"
    carve_out = "Carve-out from parent"
    merge_portfolio = "Merge with portfolio company"
    undecided = "Undecided"


class HoldPeriod(str, Enum):
    lt_3 = "<3"
    y_3_5 = "3-5"
    y_5_7 = "5-7"
    gt_7 = "7+"
    evergreen = "Evergreen"


class Sector(str, Enum):
    saas = "SaaS"
    fintech = "Fintech"
    healthtech = "Healthtech"
    logistics = "Logistics"
    industrials = "Industrials"
    edtech = "Edtech"
    proptech = "Proptech"
    insurtech = "Insurtech"
    media = "Media"
    retail = "Retail"
    energy = "Energy"
    public_sector = "Public sector"
    other = "Other"


class BusinessModel(str, Enum):
    b2b_saas = "B2B SaaS"
    b2b2c = "B2B2C"
    marketplace = "Marketplace"
    d2c_ecommerce = "D2C ecommerce"
    transaction_or_payments = "Transaction or payments"
    hardware_and_software = "Hardware + software"
    services_led = "Services-led"
    hybrid = "Hybrid"


class DigitalMaturity(str, Enum):
    digital_native = "Digital native"
    digitally_enabled = "Digitally enabled"
    traditional = "Traditional"


class RevenueStage(str, Enum):
    pre_revenue = "Pre-revenue"
    early_revenue = "Early revenue"
    growth = "Growth"
    scale = "Scale"
    mature = "Mature"


class CustomerConcentration(str, Enum):
    low = "Low — diversified base"
    moderate = "Moderate — some concentration"
    high = "High — few customers dominate revenue"


class BuildVsBuy(str, Enum):
    predominantly_build = "Predominantly in-house build"
    balanced = "Balanced build and buy"
    predominantly_cots = "Predominantly COTS/packaged (ERP, CRM, etc.)"


class CoreSystem(str, Enum):
    sap = "SAP"
    oracle = "Oracle"
    microsoft_dynamics = "Microsoft Dynamics"
    salesforce = "Salesforce"
    netsuite = "NetSuite"
    workday = "Workday"
    servicenow = "ServiceNow"
    custom_in_house = "Custom in-house"
    other = "Other"


class HostingModel(str, Enum):
    public_cloud = "Public cloud"
    hybrid = "Hybrid"
    predominantly_on_premise = "Predominantly on-premise"
    colocation = "Colocation"
    unknown = "Unknown"


class CloudProvider(str, Enum):
    aws = "AWS"
    azure = "Azure"
    gcp = "GCP"
    other = "Other"
    none = "None"


class OutsourcingReliance(str, Enum):
    none = "None"
    some_contractors = "Some contractors"
    heavily_outsourced = "Heavily outsourced"


class AiMlDependence(str, Enum):
    none = "None"
    experimental = "Experimental"
    embedded_in_product = "Embedded in the product"
    core_to_value_proposition = "Core to the value proposition"


class DataSensitivity(str, Enum):
    none = "None"
    pii = "Personal data (PII)"
    phi = "Health data (PHI)"
    pci = "Payment data (PCI)"
    financial = "Financial data"
    government_or_defence = "Government or defence"


class ComplianceRegime(str, Enum):
    soc2 = "SOC 2"
    iso27001 = "ISO 27001"
    hipaa = "HIPAA"
    pci_dss = "PCI-DSS"
    gdpr = "GDPR"
    india_dpdp = "India DPDP"
    fedramp = "FedRAMP"
    other = "Other"
    none_known = "None known"


class DdObjective(str, Enum):
    validate_scalability = "Validate scalability"
    quantify_tech_debt = "Quantify tech debt"
    assess_security_compliance = "Assess security & compliance"
    size_it_cost = "Size IT cost & run-rate"
    assess_team_key_person_risk = "Assess team & key-person risk"
    test_roadmap_credibility = "Test product roadmap credibility"
    assess_integration_separation = "Assess integration or separation effort"
    evaluate_ai_capability = "Evaluate AI capability"
    confirm_ip_ownership = "Confirm IP ownership"


class AccessLevel(str, Enum):
    full = "Full (data room and management sessions)"
    data_room_and_management = "Data room + management sessions"
    data_room_only = "Data room only"
    limited_or_public = "Limited or public information"


class DeliverableFormat(str, Enum):
    red_flag_memo = "Red-flag memo"
    full_diligence_report = "Full diligence report"
    ic_paper_input = "IC paper input"


class DdTypePreference(str, Enum):
    """Which KPMG scope deck the engagement should produce.

    User-declared, and it wins over the engine's computed mix (docs/reference/KPMG_SOW_LANGUAGE.md).
    The engine still computes its own view and surfaces disagreement.
    """

    let_platform_decide = "Let the platform decide"
    product = "Product Tech DD"
    enterprise = "Enterprise IT DD"
    blended = "Blended"
    # PLACEHOLDER (2026-08-31). Selectable and persisted, but the engine does not yet
    # act on it: there is no AI-heavy scope library, and `_PREFERENCE_TO_TYPE` in
    # scoring.py deliberately omits it, so an engagement declaring this classifies from
    # the computed mix exactly as "Let the platform decide" would. The scope content is
    # to be defined — see docs/PROJECT_LOG.md.
    ai_heavy = "AI-heavy Tech DD"


class BudgetBand(str, Enum):
    under_25k = "Under $25k"
    b_25k_75k = "$25k-$75k"
    b_75k_150k = "$75k-$150k"
    b_150k_300k = "$150k-$300k"
    over_300k = "Over $300k"
