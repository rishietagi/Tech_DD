import { API_BASE_URL, ApiError, apiClient } from "@/lib/api/client";
import type {
  EditValue,
  IntelligenceStatus,
  ReportAsset,
  ReportRead,
} from "@/types/report";

export const reportApi = {
  /** Build the report from every module; edits carry over. 409 `not_scoped` without a scope. */
  generate: (engagementId: string) =>
    apiClient.post<ReportRead>(`/engagements/${engagementId}/report`, {}),

  /** 404 `no_report` before the first generation. */
  get: (engagementId: string) =>
    apiClient.get<ReportRead>(`/engagements/${engagementId}/report`),

  edit: (engagementId: string, key: string, value: EditValue) =>
    apiClient.patch<ReportRead>(
      `/engagements/${engagementId}/report/elements/${encodeURIComponent(key)}`,
      { value },
    ),

  revert: (engagementId: string, key: string) =>
    apiClient.delete<ReportRead>(
      `/engagements/${engagementId}/report/elements/${encodeURIComponent(key)}`,
    ),

  exportUrl: (engagementId: string) =>
    `${API_BASE_URL}/engagements/${engagementId}/report/export.pptx`,

  assetUrl: (engagementId: string, assetId: string) =>
    `${API_BASE_URL}/engagements/${engagementId}/report/assets/${assetId}`,

  listAssets: (engagementId: string) =>
    apiClient.get<ReportAsset[]>(`/engagements/${engagementId}/report/assets`),

  uploadAsset: async (
    engagementId: string,
    file: File,
    title: string,
    caption: string,
  ): Promise<ReportAsset> => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", title);
    form.append("caption", caption);
    const response = await fetch(
      `${API_BASE_URL}/engagements/${engagementId}/report/assets`,
      {
        method: "POST",
        body: form,
      },
    );
    const data = await response.json();
    if (!response.ok) {
      throw new ApiError(
        response.status,
        data.detail ?? {
          code: "unknown_error",
          message: "Upload failed",
          field_errors: [],
        },
      );
    }
    return data as ReportAsset;
  },

  deleteAsset: (engagementId: string, assetId: string) =>
    apiClient.delete<void>(
      `/engagements/${engagementId}/report/assets/${assetId}`,
    ),
};

export const intelligenceApi = {
  status: () => apiClient.get<IntelligenceStatus>("/meta/intelligence"),
};
