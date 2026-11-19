/**
 * Phases 6 and 8 — inventories and the four estate assessments: applications, data &
 * infrastructure (`data_tech`), team & governance, strategy & projects.
 * Mirrors backend/app/schemas/estate.py; drift between the two is a bug.
 */
import type { Band } from "@/types/assess";

export type InventoryKind =
  | "application"
  | "data_domain"
  | "platform"
  | "it_role"
  | "it_contract"
  | "it_project"
  | "cyber_tool";
export type EstateDomain =
  "applications" | "data_tech" | "team_governance" | "strategy_projects";
export type FieldType =
  | "text"
  | "long_text"
  | "select"
  | "multi_select"
  | "date"
  | "number"
  | "process_list"
  | "app_refs";
export type Severity = "High" | "Medium" | "Low";

export const INVENTORY_KINDS: InventoryKind[] = [
  "application",
  "data_domain",
  "platform",
  "it_role",
  "it_contract",
  "it_project",
  "cyber_tool",
];

/** The deal-impact lens of a finding [DD_master §1.1]. */
export const IMPACT_LABELS: Record<string, string> = {
  one_off_investment: "One-off investment",
  run_cost: "Run-rate cost",
  plan_risk: "Risk to the plan",
  continuity: "Continuity risk",
  compliance: "Compliance exposure",
  integration: "Integration or separation",
};

export interface FieldDef {
  key: string;
  label: string;
  type: FieldType;
  required: boolean;
  options: string[];
  template_note: string;
}

export interface KindDef {
  label: string;
  sheet: string;
  sheet_aliases: string[];
  ref_prefix: string;
  source: string;
  seed_names: string[];
  fields: FieldDef[];
}

export interface ProcessRef {
  key: string;
  name: string;
  short_name: string;
}

/** A stored field value: a string, or a list for the multi-value types. */
export type FieldValue = string | string[];

export interface InventoryItem {
  id: string;
  kind: InventoryKind;
  ref: string;
  fields: Record<string, FieldValue>;
  created_at: string;
  updated_at: string;
}

export interface InventoryRead {
  engagement_id: string;
  definitions: Record<InventoryKind, KindDef>;
  processes: ProcessRef[];
  items: InventoryItem[];
}

export interface InventoryImportSummary {
  kind: InventoryKind;
  sheet: string;
  created: number;
  updated: number;
  unchanged: number;
  warnings: string[];
}

export interface InventoryImportResult {
  summaries: InventoryImportSummary[];
  note: string;
}

// ------------------------------------------------------------------ answering view

export interface AnswerOption {
  value: string;
  label: string;
}

export interface EstateQuestion {
  id: string;
  text: string;
  help: string;
  group: string;
  group_label: string;
  source: string;
  options: AnswerOption[];
}

export type SubjectKind = InventoryKind | "estate";

export interface EstateSubject {
  id: string;
  kind: SubjectKind;
  ref: string;
  name: string;
  subtitle: string;
  answered: number;
  question_count: number;
}

export interface EstateAnswer {
  value: string;
  remarks: string;
}

export interface EstateRead {
  engagement_id: string;
  domain: EstateDomain;
  subjects: EstateSubject[];
  questions: Partial<Record<SubjectKind, EstateQuestion[]>>;
  answers: Record<string, Record<string, EstateAnswer>>;
  /** question id → what the target's inventories say about it. Never an answer. */
  evidence: Record<string, string[]>;
  dd_type: string;
  ai_material: boolean;
  latest_score_version: number | null;
}

// ------------------------------------------------------------------ score payloads

export interface GapObservation {
  text: string;
  severity: Severity;
  subjects: string[];
  source: string;
}

/** One theme of a register: a strategic finding with its evidence (Phase 8). */
export interface Gap {
  key: string;
  display_id: string;
  theme: string;
  area: string;
  headline: string;
  evidence: string[];
  implication: string;
  impact: string[];
  action: string;
  severity: Severity;
  subjects: string[];
  observations: GapObservation[];
  generated: {
    headline: string;
    evidence: string[];
    action: string;
    severity: Severity;
  } | null;
  edited: boolean;
}

export interface GapCounts {
  High: number;
  Medium: number;
  Low: number;
}

export interface SectionScore {
  key: string;
  label: string;
  score: number | null;
  weight: number;
  evidence: number;
}

interface ScoreBase {
  schema_version: number;
  generator: string;
  generated_at: string;
  index: number | null;
  band: Band | null;
  band_label: string;
  band_meaning: string;
  gaps: Gap[];
  gap_counts: GapCounts;
  coverage_note: string;
  executive_summary: string;
  pointers: string[];
}

export interface ApplicationResult {
  item_id: string;
  ref: string;
  name: string;
  category: string;
  answered: number;
  question_count: number;
  criticality: number | null;
  automation: number | null;
  automation_label: string;
  ai: number | null;
  ai_label: string;
  lifecycle: string;
  flags: string[];
}

export interface ApplicationsScorePayload extends ScoreBase {
  domain: "applications";
  ai_index: number | null;
  counts: {
    applications: number;
    assessed: number;
    critical: number;
    end_of_life: number;
    manual_critical: number;
  };
  applications: ApplicationResult[];
  portfolio: SectionScore[];
}

export interface DomainResult {
  item_id: string;
  ref: string;
  name: string;
  sensitivity: string;
  holds_personal_data: boolean;
  owner_named: boolean;
  answered: number;
  question_count: number;
  score: number | null;
}

export interface PlatformResult {
  item_id: string;
  ref: string;
  name: string;
  category: string;
  lifecycle: string;
  answered: number;
  question_count: number;
  score: number | null;
  hosted_apps: string[];
}

export interface CheckResult {
  id: string;
  section: string;
  text: string;
  status: "pass" | "partial" | "fail" | "unknown" | "unanswered";
  source: "analyst" | "inventory" | "";
  evidence: string[];
}

export interface DataTechScorePayload extends ScoreBase {
  domain: "data_tech";
  sections: SectionScore[];
  domains: DomainResult[];
  platforms: PlatformResult[];
  checks: CheckResult[];
}

export interface PeopleSummary {
  headcount: number;
  in_house: number;
  outsourced: number;
  contractor: number;
  parent_shared: number;
  outsourced_share_pct: number | null;
  sole_holders: string[];
  single_person_critical_apps: string[];
  short_tenure_share_pct: number | null;
  has_leadership_role: boolean;
  by_function: Record<string, number>;
}

export interface TeamGovernanceScorePayload extends ScoreBase {
  domain: "team_governance";
  sections: SectionScore[];
  people: PeopleSummary;
  answered: number;
  question_count: number;
}

export interface ProjectResult {
  item_id: string;
  ref: string;
  name: string;
  status: string;
  allocated: number | null;
  used: number | null;
  remaining: number | null;
  pct_complete: number | null;
  spend_pct: number | null;
  planned_end: string;
  triage: string;
  confidence: string;
  flags: string[];
}

export interface PortfolioSummary {
  projects: number;
  open: number;
  planned: number;
  allocated_total: number | null;
  used_total: number | null;
  remaining_commitment: number | null;
  change_budget: number | null;
  change_budget_year: string;
  unfunded: number | null;
  over_budget: number;
  late: number;
  stop_candidates: number;
}

export interface StrategyProjectsScorePayload extends ScoreBase {
  domain: "strategy_projects";
  sections: SectionScore[];
  projects: ProjectResult[];
  portfolio: PortfolioSummary;
  answered: number;
  question_count: number;
}

export type EstateScorePayload =
  | ApplicationsScorePayload
  | DataTechScorePayload
  | TeamGovernanceScorePayload
  | StrategyProjectsScorePayload;

export interface EstateScoreRead {
  id: string;
  engagement_id: string;
  domain: EstateDomain;
  version: number;
  generator: string;
  payload: EstateScorePayload;
  created_at: string;
}

export interface EstateSummaryEntry {
  items: number;
  has_score: boolean;
  index: number | null;
  band: Band | null;
  gap_count: number;
}

export type EstateSummary = Record<EstateDomain, EstateSummaryEntry>;

export interface GapEdit {
  severity?: Severity;
  headline?: string;
  evidence?: string[];
  action?: string;
}

/** A stored value as one line of text, for tables. */
export function displayValue(
  value: FieldValue | undefined,
  processes?: ProcessRef[],
): string {
  if (value === undefined || value === null) return "";
  if (Array.isArray(value)) {
    if (processes) {
      const names = new Map(processes.map((p) => [p.key, p.short_name]));
      return value.map((v) => names.get(v) ?? v).join(", ");
    }
    return value.join(", ");
  }
  return value;
}
