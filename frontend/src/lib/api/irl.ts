import { apiClient } from "@/lib/api/client";
import type { IrlRead, IrlVersionSummary } from "@/types/irl";

export const irlApi = {
  /** Builds a request list from the latest scope. 409 `not_scoped` if none exists. */
  generate: (engagementId: string, generator?: "rules" | "llm") =>
    apiClient.post<IrlRead>(`/engagements/${engagementId}/irl`, generator ? { generator } : {}),

  getLatest: (engagementId: string) => apiClient.get<IrlRead>(`/engagements/${engagementId}/irl`),

  listVersions: (engagementId: string) =>
    apiClient.get<IrlVersionSummary[]>(`/engagements/${engagementId}/irl/versions`),

  /** Saves one answer on the latest version. An empty string clears it. */
  saveResponse: (engagementId: string, questionId: string, responseText: string) =>
    apiClient.patch<IrlRead>(`/engagements/${engagementId}/irl/responses/${questionId}`, {
      response_text: responseText,
    }),
};
