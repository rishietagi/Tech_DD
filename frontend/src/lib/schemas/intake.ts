import { z } from "zod";

import {
  ACCESS_LEVEL,
  AI_ML_DEPENDENCE,
  BUDGET_BAND,
  BUILD_VS_BUY,
  BUSINESS_MODEL,
  CLOUD_PROVIDER,
  CODE_ACCESS,
  COMPLIANCE_REGIME,
  CORE_SYSTEM,
  CUSTOMER_CONCENTRATION,
  DATA_SENSITIVITY,
  DD_OBJECTIVE,
  DD_TYPE_PREFERENCE,
  DEAL_STAGE,
  DELIVERABLE_FORMAT,
  DIGITAL_MATURITY,
  HOLD_PERIOD,
  HOSTING_MODEL,
  INVESTMENT_TYPE,
  INVESTOR_TECH_CAPABILITY,
  INVESTOR_TYPE,
  OUTSOURCING_RELIANCE,
  POST_CLOSE_INTENT,
  PROCESS_TYPE,
  REVENUE_MODEL,
  REVENUE_STAGE,
  SECTOR,
  STAKE,
  TECH_IS_PRODUCT,
  VALUE_CREATION_LEVER,
} from "./enums";

// One zod schema per intake step (initial_plan.md §3), mirroring
// backend/app/schemas/intake.py. If they drift, that is a bug (CLAUDE.md §7).

export const dealContextSchema = z.object({
  deal_name: z.string().min(1, "Required").max(255),
  context_narrative: z.string().min(40, "At least 40 characters"),
  deal_stage: z.enum(DEAL_STAGE),
  process_type: z.enum(PROCESS_TYPE),
  source_of_deal: z.string().optional(),
});
export type DealContextValues = z.infer<typeof dealContextSchema>;

export const rationaleSchema = z.object({
  rationale_narrative: z.string().min(40, "At least 40 characters"),
  value_creation_levers: z.array(z.enum(VALUE_CREATION_LEVER)).min(1, "Select at least one"),
  deal_breakers: z.string().optional(),
  known_concerns: z.string().optional(),
});
export type RationaleValues = z.infer<typeof rationaleSchema>;

export const dealStructureSchema = z.object({
  investment_type: z.enum(INVESTMENT_TYPE),
  stake: z.enum(STAKE),
  stake_percent: z.number().min(0).max(100).optional(),
  post_close_intent: z.enum(POST_CLOSE_INTENT),
  carve_out_or_tsa: z.boolean(),
  hold_period_years: z.enum(HOLD_PERIOD).optional(),
});
export type DealStructureValues = z.infer<typeof dealStructureSchema>;

export const investorSchema = z.object({
  firm_name: z.string().min(1, "Required").max(255),
  investor_type: z.enum(INVESTOR_TYPE),
  deal_lead_name: z.string().min(1, "Required").max(255),
  deal_lead_email: z.string().email("Enter a valid email"),
  check_size: z.string().optional(),
  enterprise_value: z.string().optional(),
  existing_portfolio_overlap: z.string().optional(),
  investor_tech_capability: z.enum(INVESTOR_TECH_CAPABILITY).optional(),
});
export type InvestorValues = z.infer<typeof investorSchema>;

export const targetCompanySchema = z.object({
  company_name: z.string().min(1, "Required").max(255),
  website: z.string().optional(),
  sector: z.enum(SECTOR),
  line_of_business: z.string().min(30, "At least 30 characters"),
  business_model: z.enum(BUSINESS_MODEL),
  revenue_model: z.array(z.enum(REVENUE_MODEL)).min(1, "Select at least one"),
  digital_maturity: z.enum(DIGITAL_MATURITY),
  headcount: z.number().min(0),
  revenue_stage: z.enum(REVENUE_STAGE),
  hq_location: z.string().min(1, "Required"),
  geographies: z.array(z.string()).optional(),
  customer_concentration: z.enum(CUSTOMER_CONCENTRATION).optional(),
  founded_year: z.number().min(1800).max(2100).optional(),
  ma_history: z.string().optional(),
});
export type TargetCompanyValues = z.infer<typeof targetCompanySchema>;

export const technologyProfileSchema = z.object({
  tech_is_product: z.enum(TECH_IS_PRODUCT),
  build_vs_buy: z.enum(BUILD_VS_BUY),
  core_systems: z.array(z.enum(CORE_SYSTEM)).optional(),
  hosting_model: z.enum(HOSTING_MODEL),
  cloud_providers: z.array(z.enum(CLOUD_PROVIDER)).optional(),
  known_tech_stack: z.string().optional(),
  engineering_headcount: z.number().min(0).optional(),
  engineering_share_pct: z.number().min(0).max(100).optional(),
  outsourcing_reliance: z.enum(OUTSOURCING_RELIANCE).optional(),
  ai_ml_dependence: z.enum(AI_ML_DEPENDENCE),
  data_sensitivity: z.array(z.enum(DATA_SENSITIVITY)).min(1, "Select at least one"),
  compliance_regimes: z.array(z.enum(COMPLIANCE_REGIME)).optional(),
  known_incidents: z.string().optional(),
});
export type TechnologyProfileValues = z.infer<typeof technologyProfileSchema>;

export const diligenceObjectivesSchema = z
  .object({
    dd_objectives: z.array(z.enum(DD_OBJECTIVE)).min(1, "Select at least one"),
    access_level: z.enum(ACCESS_LEVEL),
    code_access: z.enum(CODE_ACCESS),
    deliverable_format: z.array(z.enum(DELIVERABLE_FORMAT)).min(1, "Select at least one"),
    timeline_weeks: z.number().min(1),
    bid_date: z.string().optional(),
    ic_date: z.string().optional(),
    budget_band: z.enum(BUDGET_BAND).optional(),
    clean_team_constraints: z.string().optional(),
    dd_type_preference: z.enum(DD_TYPE_PREFERENCE),
    dd_type_override_reason: z.string().optional(),
  })
  .refine(
    (data) => data.dd_type_preference === "Let the platform decide" || Boolean(data.dd_type_override_reason?.trim()),
    {
      message: "A reason is required when overriding the platform's recommendation",
      path: ["dd_type_override_reason"],
    },
  );
export type DiligenceObjectivesValues = z.infer<typeof diligenceObjectivesSchema>;

export const intakeSchema = z.object({
  context: dealContextSchema,
  rationale: rationaleSchema,
  structure: dealStructureSchema,
  investor: investorSchema,
  target: targetCompanySchema,
  technology: technologyProfileSchema,
  objectives: diligenceObjectivesSchema,
});
export type IntakeValues = z.infer<typeof intakeSchema>;

export const SECTION_SCHEMAS = {
  context: dealContextSchema,
  rationale: rationaleSchema,
  structure: dealStructureSchema,
  investor: investorSchema,
  target: targetCompanySchema,
  technology: technologyProfileSchema,
  objectives: diligenceObjectivesSchema,
} as const;
