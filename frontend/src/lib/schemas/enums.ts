// Value lists mirroring backend/app/reference/enums.py. Labels come from
// /meta/enums at runtime for rendering; these arrays exist so zod can validate
// the same closed sets without a network round-trip.

export const DEAL_STAGE = ["Exclusivity", "Bid situation", "Exploratory"] as const;
export const PROCESS_TYPE = ["Broad auction", "Limited process", "Bilateral", "Proprietary"] as const;

export const VALUE_CREATION_LEVER = [
  "Organic growth",
  "Product expansion",
  "Buy-and-build",
  "Cost takeout",
  "Margin expansion",
  "Geographic expansion",
  "Digital or AI transformation",
  "Multiple arbitrage",
] as const;

export const INVESTMENT_TYPE = ["strategic", "financial"] as const;
export const STAKE = ["majority", "minority"] as const;

export const POST_CLOSE_INTENT = [
  "Standalone",
  "Integrate into existing platform",
  "Carve-out from parent",
  "Merge with portfolio company",
  "Undecided",
] as const;

export const HOLD_PERIOD = ["<3", "3-5", "5-7", "7+", "Evergreen"] as const;

export const SECTOR = [
  "SaaS",
  "Fintech",
  "Healthtech",
  "Logistics",
  "Industrials",
  "Edtech",
  "Proptech",
  "Insurtech",
  "Media",
  "Retail",
  "Energy",
  "Public sector",
  "Other",
] as const;

export const BUSINESS_MODEL = [
  "B2B SaaS",
  "B2B2C",
  "Marketplace",
  "D2C ecommerce",
  "Transaction or payments",
  "Hardware + software",
  "Services-led",
  "Hybrid",
] as const;

export const DIGITAL_MATURITY = ["Digital native", "Digitally enabled", "Traditional"] as const;
export const REVENUE_STAGE = ["Pre-revenue", "Early revenue", "Growth", "Scale", "Mature"] as const;

export const CUSTOMER_CONCENTRATION = [
  "Low — diversified base",
  "Moderate — some concentration",
  "High — few customers dominate revenue",
] as const;

export const BUILD_VS_BUY = [
  "Predominantly in-house build",
  "Balanced build and buy",
  "Predominantly COTS/packaged (ERP, CRM, etc.)",
] as const;

export const CORE_SYSTEM = [
  "SAP",
  "Oracle",
  "Microsoft Dynamics",
  "Salesforce",
  "NetSuite",
  "Workday",
  "ServiceNow",
  "Custom in-house",
  "Other",
] as const;

export const HOSTING_MODEL = ["Public cloud", "Hybrid", "Predominantly on-premise", "Colocation", "Unknown"] as const;
export const CLOUD_PROVIDER = ["AWS", "Azure", "GCP", "Other", "None"] as const;
export const OUTSOURCING_RELIANCE = ["None", "Some contractors", "Heavily outsourced"] as const;

export const AI_ML_DEPENDENCE = [
  "None",
  "Experimental",
  "Embedded in the product",
  "Core to the value proposition",
] as const;

export const DATA_SENSITIVITY = [
  "None",
  "Personal data (PII)",
  "Health data (PHI)",
  "Payment data (PCI)",
  "Financial data",
  "Government or defence",
] as const;

export const COMPLIANCE_REGIME = [
  "SOC 2",
  "ISO 27001",
  "HIPAA",
  "PCI-DSS",
  "GDPR",
  "India DPDP",
  "FedRAMP",
  "Other",
  "None known",
] as const;

export const DD_OBJECTIVE = [
  "Validate scalability",
  "Quantify tech debt",
  "Assess security & compliance",
  "Size IT cost & run-rate",
  "Assess team & key-person risk",
  "Test product roadmap credibility",
  "Assess integration or separation effort",
  "Evaluate AI capability",
  "Confirm IP ownership",
] as const;

export const ACCESS_LEVEL = [
  "Full (data room and management sessions)",
  "Data room + management sessions",
  "Data room only",
  "Limited or public information",
] as const;

export const DELIVERABLE_FORMAT = ["Red-flag memo", "Full diligence report", "IC paper input"] as const;

export const BUDGET_BAND = [
  "Under $25k",
  "$25k-$75k",
  "$75k-$150k",
  "$150k-$300k",
  "Over $300k",
] as const;

export const DD_TYPE_PREFERENCE = [
  "Let the platform decide",
  "Product Tech DD",
  "Enterprise IT DD",
  "Blended",
] as const;
