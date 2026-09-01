// Mirrors backend/app/schemas/checklist.py. If they drift, that is a bug (CLAUDE.md §7).

export type DocumentStatus = "not_received" | "received_partially" | "received_completely";
export type Priority = "critical" | "high" | "medium" | "low";

export const DOCUMENT_STATUSES: DocumentStatus[] = [
  "not_received",
  "received_partially",
  "received_completely",
];

export const STATUS_LABELS: Record<DocumentStatus, string> = {
  not_received: "Not yet received",
  received_partially: "Received partially",
  received_completely: "Received completely",
};

export const PRIORITIES: Priority[] = ["critical", "high", "medium", "low"];

export const PRIORITY_LABELS: Record<Priority, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

/** What each level means, shown in the legend so a colour is never unexplained. */
export const PRIORITY_MEANINGS: Record<Priority, string> = {
  critical: "Security, privacy or regulatory evidence",
  high: "Seeds an area the scope opened to deep dive",
  medium: "Seeds an area the scope assesses",
  low: "Supporting context",
};

export interface ChecklistItem {
  question_id: string;
  function: string;
  document_requested: string;
  document_type: string;
  status: DocumentStatus;
  notes: string;
  priority: Priority;
  priority_reason: string;
  source_row_id?: string | null;
  source_row_title?: string | null;
  matched_files: string[];
  set_by_human: boolean;
  updated_at?: string | null;
}

export interface ChecklistSummary {
  total: number;
  received_completely: number;
  received_partially: number;
  not_received: number;
  outstanding_critical: number;
  outstanding_high: number;
}

export interface ChecklistRead {
  engagement_id: string;
  irl_id: string;
  irl_version: number;
  company_name: string | null;
  items: ChecklistItem[];
  summary: ChecklistSummary;
  /** When the shared drive was last walked. Null until the scanner exists. */
  last_scanned_at: string | null;
}
