import { apiClient } from "@/lib/api/client";
import type {
  EngagementListResponse,
  EngagementRead,
  EnumsResponse,
  ScopeOfWorkRead,
  ScopeOfWorkVersionSummary,
  ScopePreview,
  WorkstreamLibrary,
} from "@/types/engagement";
import type { IntakeSectionPayload, IntakeStep } from "@/types/intake";

export const engagementsApi = {
  create: (dealName: string) => apiClient.post<EngagementRead>("/engagements", { deal_name: dealName }),

  get: (id: string) => apiClient.get<EngagementRead>(`/engagements/${id}`),

  list: (params?: { q?: string; status_filter?: string; dd_type?: string; limit?: number; offset?: number }) =>
    apiClient.get<EngagementListResponse>("/engagements", params),

  update: (id: string, payload: { deal_name?: string; current_step?: string }) =>
    apiClient.patch<EngagementRead>(`/engagements/${id}`, payload),

  archive: (id: string) => apiClient.delete<void>(`/engagements/${id}`),

  patchSection: (id: string, section: IntakeStep, payload: IntakeSectionPayload) =>
    apiClient.patch<EngagementRead>(`/engagements/${id}/intake/${section}`, payload),

  submit: (id: string) => apiClient.post<EngagementRead>(`/engagements/${id}/submit`),
};

export const scopeApi = {
  generate: (engagementId: string, generator?: "rules" | "llm") =>
    apiClient.post<ScopeOfWorkRead>(`/engagements/${engagementId}/scope`, generator ? { generator } : {}),

  getLatest: (engagementId: string) => apiClient.get<ScopeOfWorkRead>(`/engagements/${engagementId}/scope`),

  getVersion: (engagementId: string, version: number) =>
    apiClient.get<ScopeOfWorkRead>(`/engagements/${engagementId}/scope/${version}`),

  listVersions: (engagementId: string) =>
    apiClient.get<ScopeOfWorkVersionSummary[]>(`/engagements/${engagementId}/scope/versions`),

  /** Classification from a draft intake. Safe to call while the user is still typing. */
  preview: (engagementId: string) =>
    apiClient.post<ScopePreview>(`/engagements/${engagementId}/scope/preview`),

  overrideRow: (
    engagementId: string,
    version: number,
    rowId: string,
    payload: { tier?: number; title?: string; reason?: string },
  ) => apiClient.patch<ScopeOfWorkRead>(`/engagements/${engagementId}/scope/${version}/rows/${rowId}`, payload),
};

export const metaApi = {
  enums: () => apiClient.get<{ enums: EnumsResponse }>("/meta/enums"),
  workstreams: () => apiClient.get<WorkstreamLibrary>("/meta/workstreams"),
};
