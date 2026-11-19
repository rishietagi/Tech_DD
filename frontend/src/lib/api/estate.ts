import { API_BASE_URL, ApiError, apiClient } from "@/lib/api/client";
import type {
  EstateDomain,
  EstateRead,
  EstateScoreRead,
  EstateSummary,
  FieldValue,
  GapEdit,
  InventoryImportResult,
  InventoryItem,
  InventoryKind,
  InventoryRead,
} from "@/types/estate";
import type {
  FinancialsImportResult,
  ItBudgetInputs,
  ItBudgetRead,
} from "@/types/it-budget";

/** Multipart uploads build their own request — `apiClient` serialises JSON. */
async function upload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: form,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(
      response.status,
      data.detail ?? {
        code: "unknown_error",
        message: "The upload could not be processed",
        field_errors: [],
      },
    );
  }
  return data as T;
}

export const inventoryApi = {
  list: (engagementId: string) =>
    apiClient.get<InventoryRead>(`/engagements/${engagementId}/inventory`),

  create: (
    engagementId: string,
    kind: InventoryKind,
    fields: Record<string, FieldValue>,
  ) =>
    apiClient.post<InventoryItem>(`/engagements/${engagementId}/inventory`, {
      kind,
      fields,
    }),

  /** Partial — only the keys sent change. An empty string or list clears a field. */
  update: (
    engagementId: string,
    itemId: string,
    fields: Record<string, FieldValue>,
  ) =>
    apiClient.patch<InventoryItem>(
      `/engagements/${engagementId}/inventory/${itemId}`,
      { fields },
    ),

  remove: (engagementId: string, itemId: string) =>
    apiClient.delete<void>(`/engagements/${engagementId}/inventory/${itemId}`),

  templateUrl: (engagementId: string, kind: InventoryKind) =>
    `${API_BASE_URL}/engagements/${engagementId}/inventory/${kind}/template.xlsx`,

  importTemplate: (engagementId: string, kind: InventoryKind, file: File) =>
    upload<InventoryImportResult>(
      `/engagements/${engagementId}/inventory/${kind}/import`,
      file,
    ),
};

export const estateApi = {
  summary: (engagementId: string) =>
    apiClient.get<EstateSummary>(`/engagements/${engagementId}/estate/summary`),

  get: (engagementId: string, domain: EstateDomain) =>
    apiClient.get<EstateRead>(`/engagements/${engagementId}/estate/${domain}`),

  /** Omitting a field leaves it alone, so saving a remark never wipes the level. */
  saveAnswer: (
    engagementId: string,
    domain: EstateDomain,
    body: {
      subject_id: string;
      question_id: string;
      value?: string;
      remarks?: string;
    },
  ) =>
    apiClient.patch<EstateRead>(
      `/engagements/${engagementId}/estate/${domain}/answers`,
      body,
    ),

  score: (engagementId: string, domain: EstateDomain) =>
    apiClient.post<EstateScoreRead>(
      `/engagements/${engagementId}/estate/${domain}/score`,
      {},
    ),

  /** 404 `no_score` before the first run. */
  getScore: (engagementId: string, domain: EstateDomain) =>
    apiClient.get<EstateScoreRead>(
      `/engagements/${engagementId}/estate/${domain}/score`,
    ),

  editGap: (
    engagementId: string,
    domain: EstateDomain,
    gapKey: string,
    body: GapEdit,
  ) =>
    apiClient.patch<EstateScoreRead>(
      `/engagements/${engagementId}/estate/${domain}/gaps/${encodeURIComponent(gapKey)}`,
      body,
    ),

  revertGap: (engagementId: string, domain: EstateDomain, gapKey: string) =>
    apiClient.delete<EstateScoreRead>(
      `/engagements/${engagementId}/estate/${domain}/gaps/${encodeURIComponent(gapKey)}`,
    ),
};

export const itBudgetApi = {
  templateUrl: (engagementId: string) =>
    `${API_BASE_URL}/engagements/${engagementId}/it-budget/template.xlsx`,
  importFinancials: (engagementId: string, file: File) =>
    upload<FinancialsImportResult>(
      `/engagements/${engagementId}/it-budget/import`,
      file,
    ),
  get: (engagementId: string) =>
    apiClient.get<ItBudgetRead>(`/engagements/${engagementId}/it-budget`),
  save: (engagementId: string, inputs: ItBudgetInputs) =>
    apiClient.put<ItBudgetRead>(
      `/engagements/${engagementId}/it-budget`,
      inputs,
    ),
  editGap: (engagementId: string, gapKey: string, body: GapEdit) =>
    apiClient.patch<ItBudgetRead>(
      `/engagements/${engagementId}/it-budget/gaps/${encodeURIComponent(gapKey)}`,
      body,
    ),
  revertGap: (engagementId: string, gapKey: string) =>
    apiClient.delete<ItBudgetRead>(
      `/engagements/${engagementId}/it-budget/gaps/${encodeURIComponent(gapKey)}`,
    ),
};
