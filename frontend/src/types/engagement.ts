import type { IntakeDraft } from "./intake";

export type EngagementStatus = "draft" | "filed" | "scoped" | "archived";

export interface EngagementDenorm {
  company_name: string | null;
  sector: string | null;
  investor_firm: string | null;
  investment_type: string | null;
  stake: string | null;
  digital_maturity: string | null;
  dd_type: string | null;
  dd_mix: number | null;
}

export interface EngagementSummary {
  id: string;
  deal_name: string;
  status: EngagementStatus;
  current_step: string;
  created_at: string;
  updated_at: string;
  filed_at: string | null;
  denorm: EngagementDenorm | null;
}

export interface EngagementRead extends EngagementSummary {
  intake: IntakeDraft;
}

export interface EngagementListResponse {
  items: EngagementSummary[];
  total: number;
}

export interface Workstream {
  name: string;
  summary: string;
  objectives: string[];
  key_questions: string[];
  evidence_requests: string[];
}

export interface ScopeOfWorkPayload {
  dd_type: string | null;
  dd_mix: number | null;
  is_placeholder: boolean;
  placeholder_notice: string | null;
  workstreams: Workstream[];
}

export interface ScopeOfWorkRead {
  id: string;
  engagement_id: string;
  version: number;
  generator: string;
  dd_type: string | null;
  dd_mix: number | null;
  payload: ScopeOfWorkPayload;
  created_at: string;
}

export interface ScopeOfWorkVersionSummary {
  version: number;
  generator: string;
  created_at: string;
}

export interface EnumOption {
  value: string;
  label: string;
}

export type EnumsResponse = Record<string, EnumOption[]>;
