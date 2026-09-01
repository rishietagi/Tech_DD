import { apiClient } from "@/lib/api/client";
import type { ChecklistRead, DocumentStatus } from "@/types/checklist";

export const checklistApi = {
  /** The checklist for the latest request list. 404 `no_irl` if none has been built. */
  get: (engagementId: string) =>
    apiClient.get<ChecklistRead>(`/engagements/${engagementId}/checklist`),

  /** Returns the whole checklist so summary counts stay consistent with the change. */
  update: (
    engagementId: string,
    questionId: string,
    patch: { status?: DocumentStatus; document_type?: string; notes?: string },
  ) => apiClient.patch<ChecklistRead>(`/engagements/${engagementId}/checklist/${questionId}`, patch),

  /** Not connected yet — returns 501 `scan_not_implemented` until the shared-drive
   *  walk is wired at deployment. */
  scan: (engagementId: string) =>
    apiClient.post<ChecklistRead>(`/engagements/${engagementId}/checklist/scan`, {}),
};
