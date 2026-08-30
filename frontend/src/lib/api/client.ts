export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface FieldError {
  field: string;
  message: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  field_errors: FieldError[];
}

export class ApiError extends Error {
  code: string;
  fieldErrors: FieldError[];
  status: number;

  constructor(status: number, detail: ApiErrorDetail) {
    super(detail.message);
    this.name = "ApiError";
    this.status = status;
    this.code = detail.code;
    this.fieldErrors = detail.field_errors;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  searchParams?: Record<string, string | number | undefined>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (options.searchParams) {
    for (const [key, value] of Object.entries(options.searchParams)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const response = await fetch(url.toString(), {
    method: options.method ?? "GET",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json();

  if (!response.ok) {
    const detail: ApiErrorDetail = data.detail ?? {
      code: "unknown_error",
      message: "An unknown error occurred",
      field_errors: [],
    };
    throw new ApiError(response.status, detail);
  }

  return data as T;
}

export const apiClient = {
  get: <T>(path: string, searchParams?: RequestOptions["searchParams"]) =>
    request<T>(path, { method: "GET", searchParams }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
