// Mirrors backend/app/schemas/irl.py. If they drift, that is a bug (CLAUDE.md §7).

/** Where a question came from. "scope" questions trace to a KPMG scope row's evidence
 *  list; "llm" questions were added by the model to cover a function the technology
 *  scope does not reach. */
export type QuestionSource = "scope" | "llm";

export interface IrlQuestion {
  id: string;
  function: string;
  question: string;
  source: QuestionSource;
  source_row_id?: string | null;
  source_row_title?: string | null;
  seed_text?: string | null;
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

export interface IrlRead {
  id: string;
  engagement_id: string;
  version: number;
  generator: string;
  source_scope_version: number | null;
  payload: IrlPayload;
  /** question_id -> response text. Joined from the response table, not the payload. */
  responses: Record<string, string>;
  created_at: string;
}

export interface IrlVersionSummary {
  version: number;
  generator: string;
  created_at: string;
}
