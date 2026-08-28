// Mirrors backend/app/schemas/intake.py. If they drift, that is a bug (CLAUDE.md §7).

export interface DealContext {
  deal_name?: string;
  context_narrative?: string;
  deal_stage?: string;
  process_type?: string;
  source_of_deal?: string;
}

export interface Rationale {
  rationale_narrative?: string;
  value_creation_levers?: string[];
  deal_breakers?: string;
  known_concerns?: string;
}

export interface DealStructure {
  investment_type?: "strategic" | "financial";
  stake?: "majority" | "minority";
  stake_percent?: number;
  post_close_intent?: string;
  carve_out_or_tsa?: boolean;
  hold_period_years?: string;
}

export interface Investor {
  firm_name?: string;
  investor_type?: string;
  deal_lead_name?: string;
  deal_lead_email?: string;
  check_size?: string;
  enterprise_value?: string;
  existing_portfolio_overlap?: string;
  investor_tech_capability?: string;
}

export interface TargetCompany {
  company_name?: string;
  website?: string;
  sector?: string;
  line_of_business?: string;
  business_model?: string;
  revenue_model?: string[];
  digital_maturity?: string;
  headcount?: number;
  revenue_stage?: string;
  hq_location?: string;
  geographies?: string[];
  customer_concentration?: string;
  founded_year?: number;
  ma_history?: string;
}

export interface TechnologyProfile {
  tech_is_product?: string;
  build_vs_buy?: string;
  core_systems?: string[];
  hosting_model?: string;
  cloud_providers?: string[];
  known_tech_stack?: string;
  engineering_headcount?: number;
  engineering_share_pct?: number;
  outsourcing_reliance?: string;
  ai_ml_dependence?: string;
  data_sensitivity?: string[];
  compliance_regimes?: string[];
  known_incidents?: string;
}

export interface DiligenceObjectives {
  dd_objectives?: string[];
  access_level?: string;
  code_access?: string;
  deliverable_format?: string[];
  timeline_weeks?: number;
  bid_date?: string;
  ic_date?: string;
  budget_band?: string;
  clean_team_constraints?: string;
  dd_type_preference?: string;
  dd_type_override_reason?: string;
}

export interface IntakeDraft {
  context: DealContext | null;
  rationale: Rationale | null;
  structure: DealStructure | null;
  investor: Investor | null;
  target: TargetCompany | null;
  technology: TechnologyProfile | null;
  objectives: DiligenceObjectives | null;
}

export const INTAKE_STEPS = [
  "context",
  "rationale",
  "structure",
  "investor",
  "target",
  "technology",
  "objectives",
] as const;

export type IntakeStep = (typeof INTAKE_STEPS)[number];

export const INTAKE_STEP_LABELS: Record<IntakeStep, string> = {
  context: "Deal Context",
  rationale: "Rationale",
  structure: "Deal Structure",
  investor: "Investor",
  target: "Target Company",
  technology: "Technology Profile",
  objectives: "Objectives & Logistics",
};

export type IntakeSectionPayload =
  | DealContext
  | Rationale
  | DealStructure
  | Investor
  | TargetCompany
  | TechnologyProfile
  | DiligenceObjectives;
