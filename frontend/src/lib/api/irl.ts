import { API_BASE_URL, ApiError, apiClient } from "@/lib/api/client";
import type { ImportResponsesResult, IrlRead, IrlVersionSummary } from "@/types/irl";

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

  /** Add a request the generated list did not anticipate. */
  addQuestion: (
    engagementId: string,
    body: { question: string; function: string; scope_area?: string },
  ) => apiClient.post<IrlRead>(`/engagements/${engagementId}/irl/questions`, body),

  /** Reword a request, or move it to a different function or scope area. */
  updateQuestion: (
    engagementId: string,
    questionId: string,
    body: { question?: string; function?: string; scope_area?: string },
  ) => apiClient.patch<IrlRead>(`/engagements/${engagementId}/irl/questions/${questionId}`, body),

  /** Remove a request. Its response and document status go with it. */
  deleteQuestion: (engagementId: string, questionId: string) =>
    apiClient.delete<IrlRead>(`/engagements/${engagementId}/irl/questions/${questionId}`),

  /** Upload a completed workbook and scrape its Response column.
   *
   *  Not routed through `apiClient`, which serialises JSON — a multipart body must set
   *  its own boundary, so the browser has to build the request. */
  importResponses: async (engagementId: string, file: File): Promise<ImportResponsesResult> => {
    const form = new FormData();
    form.append("file", file);

    const response = await fetch(
      `${API_BASE_URL}/engagements/${engagementId}/irl/import`,
      { method: "POST", body: form },
    );
    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail ?? {
        code: "unknown_error",
        message: "The upload could not be processed",
        field_errors: [],
      };
      throw new ApiError(response.status, detail);
    }
    return data as ImportResponsesResult;
  },
};
