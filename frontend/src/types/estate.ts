/**
 * Phase 6 — inventories, application and data & technology assessment.
 * Mirrors backend/app/schemas/estate.py; drift between the two is a bug.
 */
import type { Band } from "@/types/assess";

export type InventoryKind =
  "application" | "data_domain" | "platform" | "it_role" | "it_contract";
export type EstateDomain = "applications" | "data_tech";
export type FieldType =
  | "text"
  | "long_text"
  | "select"
  | "multi_select"
  | "date"
  | "process_list"
  | "app_refs";
export type Severity = "High" | "Medium" | "Low";

export const INVENTORY_KINDS: InventoryKind[] = [
  "application",
  "data_domain",
  "platform",
  "it_role",
  "it_contract",
];

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
  ref_prefix: string;
  source: string;
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
  latest_score_version: number | null;
}

// ------------------------------------------------------------------ score payloads

export interface GapSubject {
  kind: string;
  item_id: string;
  ref: string;
  name: string;
}

export interface Gap {
  key: string;
  display_id: string;
  scope: "item" | "portfolio";
  category: string;
  subject: GapSubject;
  title: string;
  findings: string[];
  description: string;
  hypothesis: string;
  severity: Severity;
  generated: {
    description: string;
    hypothesis: string;
    severity: Severity;
  } | null;
  edited: boolean;
}

export interface GapCounts {
  High: number;
  Medium: number;
  Low: number;
  item: number;
  portfolio: number;
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
  assessed: boolean;
  partial: boolean;
  criticality: number | null;
  business_fit: number | null;
  technical_fit: number | null;
  disposition: string;
  disposition_statement: string;
  consolidate_into: string | null;
  automation: number | null;
  automation_label: string;
  ai: number | null;
  ai_label: string;
  debt: number | null;
  debt_band: string | null;
  spof_status: "SPOF" | "Check" | "OK";
  spof: string[];
  spof_checks: string[];
  scalability_status: "At risk" | "Watch" | "OK";
  scalability: string[];
}

export interface ApplicationsScorePayload extends ScoreBase {
  domain: "applications";
  ai_index: number | null;
  counts: {
    applications: number;
    assessed: number;
    by_disposition: Record<string, number>;
    high_debt: number;
    spof: number;
    scalability_risk: number;
  };
  applications: ApplicationResult[];
}

export interface SectionScore {
  key: string;
  label: string;
  score: number | null;
  weight: number;
  evidence: number;
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
}

export interface DataTechScorePayload extends ScoreBase {
  domain: "data_tech";
  sections: SectionScore[];
  domains: DomainResult[];
  platforms: PlatformResult[];
  checks: CheckResult[];
}

export type EstateScorePayload =
  ApplicationsScorePayload | DataTechScorePayload;

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
  description?: string;
  hypothesis?: string;
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
