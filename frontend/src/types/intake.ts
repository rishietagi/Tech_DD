// Mirrors backend/app/schemas/intake.py. If they drift, that is a bug (CLAUDE.md §7).

export interface DealContext {
  deal_name?: string;
  context_narrative?: string;
  deal_stage?: string;
  process_type?: string;
  source_of_deal?: string;
  investor_firm_name?: string;
}

export interface Rationale {
  rationale_narrative?: string;
  value_creation_levers?: string[];
  deal_breakers?: string;
  focus_areas?: string;
}

export interface DealStructure {
  investment_type?: "strategic" | "financial";
  stake?: "majority" | "minority";
  stake_percent?: number;
  post_close_intent?: string;
  hold_period_years?: string;
}

export interface TargetCompany {
  company_name?: string;
  website?: string;
  sector?: string;
  line_of_business?: string;
  business_model?: string;
  digital_maturity?: string;
  headcount?: number;
  revenue_stage?: string;
  company_revenue?: string;
  hq_location?: string;
  office_locations?: string;
  geographies?: string[];
  customer_concentration?: string;
  founded_year?: number;
  ma_history?: string;
}

export interface TechnologyProfile {
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
  deliverable_format?: string[];
  timeline_weeks?: number;
  bid_date?: string;
  ic_date?: string;
  budget_band?: string;
  dd_type_preference?: string;
}

export interface IntakeDraft {
  context: DealContext | null;
  rationale: Rationale | null;
  structure: DealStructure | null;
  target: TargetCompany | null;
  technology: TechnologyProfile | null;
  objectives: DiligenceObjectives | null;
}

export const INTAKE_STEPS = ["context", "rationale", "structure", "target", "technology", "objectives"] as const;

export type IntakeStep = (typeof INTAKE_STEPS)[number];

export const INTAKE_STEP_LABELS: Record<IntakeStep, string> = {
  context: "Deal Context",
  rationale: "Rationale",
  structure: "Deal Structure",
  target: "Target Company",
  technology: "Technology Profile",
  objectives: "Objectives & Logistics",
};

export type IntakeSectionPayload =
  | DealContext
  | Rationale
  | DealStructure
  | TargetCompany
  | TechnologyProfile
  | DiligenceObjectives;
