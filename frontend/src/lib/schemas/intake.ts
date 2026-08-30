import { z } from "zod";

import {
  ACCESS_LEVEL,
  AI_ML_DEPENDENCE,
  BUDGET_BAND,
  BUILD_VS_BUY,
  BUSINESS_MODEL,
  CLOUD_PROVIDER,
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
  OUTSOURCING_RELIANCE,
  POST_CLOSE_INTENT,
  PROCESS_TYPE,
  REVENUE_STAGE,
  SECTOR,
  STAKE,
  TECH_IS_PRODUCT,
  VALUE_CREATION_LEVER,
} from "./enums";

// One zod schema per intake step (initial_plan.md §3), mirroring
// backend/app/schemas/intake.py. If they drift, that is a bug (CLAUDE.md §7).
// Every field is optional except target.sector and target.line_of_business.

export const dealContextSchema = z.object({
  deal_name: z.string().max(255).optional(),
  context_narrative: z.string().optional(),
  deal_stage: z.enum(DEAL_STAGE).optional(),
  process_type: z.enum(PROCESS_TYPE).optional(),
  source_of_deal: z.string().optional(),
  investor_firm_name: z.string().optional(),
});
export type DealContextValues = z.infer<typeof dealContextSchema>;

export const rationaleSchema = z.object({
  rationale_narrative: z.string().optional(),
  value_creation_levers: z.array(z.enum(VALUE_CREATION_LEVER)).optional(),
  deal_breakers: z.string().optional(),
  focus_areas: z.string().optional(),
});
export type RationaleValues = z.infer<typeof rationaleSchema>;

export const dealStructureSchema = z.object({
  investment_type: z.enum(INVESTMENT_TYPE).optional(),
  stake: z.enum(STAKE).optional(),
  stake_percent: z.number().min(0).max(100).optional(),
  post_close_intent: z.enum(POST_CLOSE_INTENT).optional(),
  hold_period_years: z.enum(HOLD_PERIOD).optional(),
});
export type DealStructureValues = z.infer<typeof dealStructureSchema>;

export const targetCompanySchema = z.object({
  company_name: z.string().max(255).optional(),
  website: z.string().optional(),
  sector: z.enum(SECTOR),
  line_of_business: z.string().min(30, "At least 30 characters"),
  business_model: z.enum(BUSINESS_MODEL).optional(),
  digital_maturity: z.enum(DIGITAL_MATURITY).optional(),
  headcount: z.number().min(0).optional(),
  revenue_stage: z.enum(REVENUE_STAGE).optional(),
  company_revenue: z.string().optional(),
  hq_location: z.string().optional(),
  office_locations: z.string().optional(),
  geographies: z.array(z.string()).optional(),
  customer_concentration: z.enum(CUSTOMER_CONCENTRATION).optional(),
  founded_year: z.number().min(1800).max(2100).optional(),
  ma_history: z.string().optional(),
});
export type TargetCompanyValues = z.infer<typeof targetCompanySchema>;

export const technologyProfileSchema = z.object({
  tech_is_product: z.enum(TECH_IS_PRODUCT).optional(),
  build_vs_buy: z.enum(BUILD_VS_BUY).optional(),
  core_systems: z.array(z.enum(CORE_SYSTEM)).optional(),
  hosting_model: z.enum(HOSTING_MODEL).optional(),
  cloud_providers: z.array(z.enum(CLOUD_PROVIDER)).optional(),
  known_tech_stack: z.string().optional(),
  engineering_headcount: z.number().min(0).optional(),
  engineering_share_pct: z.number().min(0).max(100).optional(),
  outsourcing_reliance: z.enum(OUTSOURCING_RELIANCE).optional(),
  ai_ml_dependence: z.enum(AI_ML_DEPENDENCE).optional(),
  data_sensitivity: z.array(z.enum(DATA_SENSITIVITY)).optional(),
  compliance_regimes: z.array(z.enum(COMPLIANCE_REGIME)).optional(),
  known_incidents: z.string().optional(),
});
export type TechnologyProfileValues = z.infer<typeof technologyProfileSchema>;

export const diligenceObjectivesSchema = z.object({
  dd_objectives: z.array(z.enum(DD_OBJECTIVE)).optional(),
  access_level: z.enum(ACCESS_LEVEL).optional(),
  deliverable_format: z.array(z.enum(DELIVERABLE_FORMAT)).optional(),
  timeline_weeks: z.number().min(1).optional(),
  bid_date: z.string().optional(),
  ic_date: z.string().optional(),
  budget_band: z.enum(BUDGET_BAND).optional(),
  dd_type_preference: z.enum(DD_TYPE_PREFERENCE).optional(),
});
export type DiligenceObjectivesValues = z.infer<typeof diligenceObjectivesSchema>;

export const intakeSchema = z.object({
  context: dealContextSchema,
  rationale: rationaleSchema,
  structure: dealStructureSchema,
  target: targetCompanySchema,
  technology: technologyProfileSchema,
  objectives: diligenceObjectivesSchema,
});
export type IntakeValues = z.infer<typeof intakeSchema>;

export const SECTION_SCHEMAS = {
  context: dealContextSchema,
  rationale: rationaleSchema,
  structure: dealStructureSchema,
  target: targetCompanySchema,
  technology: technologyProfileSchema,
  objectives: diligenceObjectivesSchema,
} as const;
