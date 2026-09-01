import { apiClient } from "@/lib/api/client";
import type { ResearchRead } from "@/types/research";

export const researchApi = {
  /** Runs a grounded web search over the target and stores the result.
   *  503 `research_unavailable` when no API key is configured;
   *  422 `research_rejected` when the answer could not be grounded in real sources. */
  run: (engagementId: string) =>
    apiClient.post<ResearchRead>(`/engagements/${engagementId}/research`, {}),

  getLatest: (engagementId: string) =>
    apiClient.get<ResearchRead>(`/engagements/${engagementId}/research`),
};
