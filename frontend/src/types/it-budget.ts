/**
 * IT budget review — the budgeting process, never a cost model.
 * Mirrors backend/app/schemas/it_budget.py.
 */
import type { Gap, Severity } from "@/types/estate";

export type LineKind = "run" | "change";

export interface BudgetLine {
  id: string;
  name: string;
  kind: LineKind;
  budget: (number | null)[];
  actual: (number | null)[];
}

export interface BudgetAnswer {
  value: string;
  remarks: string;
}

export interface ItBudgetInputs {
  currency: string;
  unit: string;
  years: string[];
  lines: BudgetLine[];
  answers: Record<string, BudgetAnswer>;
  notes: string;
}

export interface LineYear {
  year: string;
  budget: number | null;
  actual: number | null;
  variance: number | null;
  variance_pct: number | null;
  outside_tolerance: boolean;
  yoy_pct: number | null;
  yoy_flag: boolean;
}

export interface LineReview {
  id: string;
  name: string;
  kind: LineKind;
  years: LineYear[];
}

export interface YearTotal {
  year: string;
  budget: number | null;
  actual: number | null;
  variance_pct: number | null;
  run_share_pct: number | null;
  change_share_pct: number | null;
}

export interface BudgetFinding {
  severity: Severity;
  source: "variance" | "movement" | "missing" | "process";
  text: string;
  question_id: string | null;
}

export interface ItBudgetReview {
  lines: LineReview[];
  totals: YearTotal[];
  findings: BudgetFinding[];
  /** The findings grouped into the report's themes (Phase 8). */
  gaps: Gap[];
  tolerance_pct: number;
  movement_pct: number;
  answered: number;
  question_count: number;
  coverage_note: string;
}

export interface FinancialsImportResult {
  sheet: string;
  filled: number;
  updated: number;
  years_added: number;
  lines_added: number;
  warnings: string[];
  note: string;
}

export interface ItBudgetQuestion {
  id: string;
  text: string;
  options: string[];
}

export interface ItBudgetRead {
  engagement_id: string;
  inputs: ItBudgetInputs;
  questions: ItBudgetQuestion[];
  review: ItBudgetReview;
  saved: boolean;
  updated_at: string | null;
}
