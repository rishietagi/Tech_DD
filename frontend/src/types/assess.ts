/** Mirrors backend/app/schemas/assess.py. If these drift, that is a bug. */

export type AnswerType = "single_select" | "text";

export type Band = "manual" | "emerging" | "standardised" | "integrated" | "optimised";

export type PointerKind = "gap" | "strength" | "probe";

export interface NudgeCondition {
  equals?: string | null;
  in?: string[] | null;
  answered?: boolean | null;
}

export interface Nudge {
  id: string;
  when: NudgeCondition;
  ask: string;
}

export interface QuestionOption {
  label: string;
  score: number;
}

export interface Question {
  id: string;
  text: string;
  type: AnswerType;
  options: QuestionOption[];
  nudges: Nudge[];
  is_custom: boolean;
}

export interface ProcessStep {
  key: string;
  sn: number;
  title: string;
  weight: number;
  intent: string;
  questions: Question[];
}

export interface ProcessSummary {
  key: string;
  name: string;
  short_name: string;
  description: string;
  /** False for the processes that are named but have no questionnaire yet. */
  defined: boolean;
  question_count: number;
  answered_count: number;
  has_score: boolean;
  index: number | null;
  band: Band | null;
}

export interface ProcessListResponse {
  engagement_id: string;
  processes: ProcessSummary[];
}

export interface AnswerRead {
  question_id: string;
  value: string;
  /** What the consultant heard in the room, qualifying the option they picked. The
   *  option is the answer; the remark is the evidence behind it. */
  remarks: string;
  updated_at?: string | null;
}

export interface AssessmentRead {
  engagement_id: string;
  process_key: string;
  name: string;
  short_name: string;
  description: string;
  model_ref: string;
  questionnaire_version: string;
  steps: ProcessStep[];
  answers: Record<string, AnswerRead>;
  question_count: number;
  answered_count: number;
  latest_score_version: number | null;
}

export interface StepScore {
  key: string;
  sn: number;
  title: string;
  weight: number;
  /** Null when the step was not assessed — excluded from the index, never zeroed. */
  score: number | null;
  assessed: boolean;
  level_label: string;
  reason: string;
  answered: number;
  scoreable: number;
  /** What the rules produced, kept even where the model moved the score. */
  deterministic_score: number | null;
  refined: boolean;
  refinement_reason: string | null;
}

export interface ScorePointer {
  kind: PointerKind;
  text: string;
  step_key: string | null;
}

export interface AssessmentScorePayload {
  schema_version: number;
  process_key: string;
  process_name: string;
  questionnaire_version: string;
  model_ref: string;
  index: number;
  band: Band;
  band_label: string;
  band_meaning: string;
  deterministic_index: number;
  steps: StepScore[];
  questions_scored: number;
  questions_scoreable: number;
  steps_assessed: number;
  steps_total: number;
  coverage_note: string;
  executive_summary: string;
  pointers: ScorePointer[];
  shape_note: string | null;
  generator: string;
  generated_at: string;
  disclaimer: string;
}

export interface AssessmentScoreRead {
  id: string;
  engagement_id: string;
  process_key: string;
  version: number;
  generator: string;
  payload: AssessmentScorePayload;
  created_at: string;
  updated_at: string;
}

export const BAND_LABELS: Record<Band, string> = {
  manual: "Manual",
  emerging: "Emerging",
  standardised: "Standardised",
  integrated: "Integrated",
  optimised: "Optimised",
};

/**
 * Does this nudge's condition hold for the given answer?
 *
 * Evaluated on the client so a follow-up appears the moment the analyst picks an option,
 * without a round trip. The backend does not need the same logic: it scores from the
 * answers it holds, and a nudge answer is stored the same way whether or not its parent
 * still shows it.
 */
export function nudgeApplies(nudge: Nudge, answer: string | undefined): boolean {
  const value = (answer ?? "").trim();
  if (!value) return false;
  const { when } = nudge;
  if (when.answered) return true;
  if (when.equals != null) return value === when.equals;
  if (when.in != null) return when.in.includes(value);
  return false;
}
