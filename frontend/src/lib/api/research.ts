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

  /** Write the research by hand (AI off), or correct the latest run. Omitted fields stay. */
  edit: (
    engagementId: string,
    body: {
      summary?: string;
      business_brief?: Record<string, string>;
      findings?: { topic: string; detail: string; category: string }[];
    },
  ) =>
    apiClient.put<ResearchRead>(`/engagements/${engagementId}/research`, body),
};
