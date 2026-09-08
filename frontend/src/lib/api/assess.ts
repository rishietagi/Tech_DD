import { apiClient } from "@/lib/api/client";
import type {
  AssessmentRead,
  AssessmentScoreRead,
  ProcessListResponse,
} from "@/types/assess";

export const assessApi = {
  /** Every business process. The four undefined ones carry `defined: false`. */
  listProcesses: (engagementId: string) =>
    apiClient.get<ProcessListResponse>(`/engagements/${engagementId}/assess/processes`),

  /** Questionnaire plus recorded answers. 409 `process_not_defined` for a stub process. */
  get: (engagementId: string, processKey: string) =>
    apiClient.get<AssessmentRead>(`/engagements/${engagementId}/assess/${processKey}`),

  /** Save an option and/or its remarks. Returns the whole assessment so the progress
   *  count stays consistent.
   *
   *  Omitting a field leaves it alone — the option and the remark are edited by separate
   *  controls, so saving one must never wipe the other. */
  saveAnswer: (
    engagementId: string,
    processKey: string,
    questionId: string,
    body: { value?: string; remarks?: string },
  ) =>
    apiClient.patch<AssessmentRead>(
      `/engagements/${engagementId}/assess/${processKey}/answers/${questionId}`,
      body,
    ),

  addQuestion: (engagementId: string, processKey: string, stepKey: string, text: string) =>
    apiClient.post<AssessmentRead>(
      `/engagements/${engagementId}/assess/${processKey}/questions`,
      { step_key: stepKey, text },
    ),

  score: (engagementId: string, processKey: string) =>
    apiClient.post<AssessmentScoreRead>(
      `/engagements/${engagementId}/assess/${processKey}/score`,
      {},
    ),

  /** The latest stored score. 404 `no_score` if this process has not been scored. */
  getScore: (engagementId: string, processKey: string) =>
    apiClient.get<AssessmentScoreRead>(`/engagements/${engagementId}/assess/${processKey}/score`),
};
