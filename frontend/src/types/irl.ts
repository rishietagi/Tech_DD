// Mirrors backend/app/schemas/irl.py. If they drift, that is a bug (CLAUDE.md §7).

/** Where a question came from. "scope" questions trace to a KPMG scope row's evidence
 *  list; "llm" questions were added by the model to cover a function the technology
 *  scope does not reach; "manual" questions were written by the analyst. */
export type QuestionSource = "scope" | "llm" | "manual";

/** What a request asks for. A document wants an artefact; a question wants an
 *  explanation only management can give. Only a document can be "received", only a
 *  question can be "answered" — the tracking control adapts accordingly. */
export type RequestKind = "document" | "question";

export interface IrlQuestion {
  id: string;
  /** The scope-of-work heading this request traces to. The list groups by this, so the
   *  IRL follows the same areas the deck opened. Empty for additions. */
  scope_area: string;
  /** Who owns the answer — what makes the workbook routable. */
  function: string;
  question: string;
  kind: RequestKind;
  /** For sourced questions: the DD_master page the area of investigation came from. */
  citation?: string;
  source: QuestionSource;
  source_row_id?: string | null;
  source_row_title?: string | null;
  seed_text?: string | null;
  /** True once an analyst has reworded it; the engine's text is kept alongside. */
  edited_by_human?: boolean;
  original_question?: string | null;
}

/** What an uploaded response workbook actually changed. Reported rather than assumed:
 *  an import that matched nothing looks identical to one that worked. */
export interface ImportResponsesResult {
  matched: number;
  updated: number;
  skipped_blank: number;
  unmatched_rows: string[];
  total_rows: number;
  note: string;
}

export interface IrlFunctionGroup {
  name: string;
  question_ids: string[];
}

export interface IrlPayload {
  schema_version: 1;
  generator: string;
  prompt_version?: string | null;
  company_name?: string | null;
  source_scope_version?: number | null;
  used_research: boolean;
  intro: string;
  questions: IrlQuestion[];
  functions: IrlFunctionGroup[];
  generated_at: string;
}

/** What the deal team observes about the document behind one request.
 *
 *  Rendered inside the IRL from 2026-09-02 so the analyst works one screen. Storage stays
 *  split — a response is what the client wrote, tracking is what the team observed — and
 *  none of this reaches the client workbook. */
export interface IrlTracking {
  status: "not_received" | "received_partially" | "received_completely";
  document_type: string;
  remarks: string;
  priority: "critical" | "high" | "medium" | "low";
  priority_reason: string;
  set_by_human: boolean;
  updated_at?: string | null;

  /** Files the scan inferred the status from. */
  matched_files: string[];
  /** What to go back and ask when what arrived is not enough. */
  follow_up_questions: string[];
  /** Why the scan called the status what it did. */
  scan_reasoning: string;
  scanned_at?: string | null;
}

export interface IrlRead {
  id: string;
  engagement_id: string;
  version: number;
  generator: string;
  source_scope_version: number | null;
  payload: IrlPayload;
  /** question_id -> response text. Joined from the response table, not the payload. */
  responses: Record<string, string>;
  /** question_id -> what the deal team observes. Joined from the document-status table. */
  tracking: Record<string, IrlTracking>;
  created_at: string;
}

export interface IrlVersionSummary {
  version: number;
  generator: string;
  created_at: string;
}
