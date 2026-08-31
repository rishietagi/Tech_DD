import type { IntakeDraft } from "./intake";

export type EngagementStatus = "draft" | "filed" | "scoped" | "archived";

export interface EngagementDenorm {
  company_name: string | null;
  sector: string | null;
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

// --- v1: the Phase 1 placeholder shape, retained so old scope rows still render ---

export interface Workstream {
  name: string;
  summary: string;
  objectives: string[];
  key_questions: string[];
  evidence_requests: string[];
}

export interface ScopeOfWorkPayloadV1 {
  schema_version: 1;
  dd_type: string | null;
  dd_mix: number | null;
  is_placeholder: boolean;
  placeholder_notice: string | null;
  workstreams: Workstream[];
}

// --- v2: the KPMG deck. Mirrors backend/app/schemas/scope.py ---

export type DdType = "enterprise" | "product" | "blended";
export type Confidence = "high" | "medium" | "low";
export type SourceProvenance = "sourced" | "extended";

export interface Signal {
  code: string;
  label: string;
  effect: string;
  source_field: string | null;
  source_value: string | null;
  detail: Record<string, unknown>;
  citation: string | null;
  provenance: SourceProvenance;
}

export interface Classification {
  dd_type: DdType;
  dd_mix: number;
  confidence: Confidence;
  computed_dd_type: DdType;
  computed_dd_mix: number;
  override_applied: boolean;
  override_source: string | null;
  signals: Signal[];
  unknown_count: number;
  confidence_reasons: string[];
}

export interface ScopeLine {
  text: string;
  source_provenance: SourceProvenance;
}

export interface ScopedRow {
  id: string;
  sn: number;
  deck: "product" | "enterprise";
  title: string;
  lines: ScopeLine[];
  tier: number;
  tier_name: string;
  tier_reason: string;
  adjustments: string[];
  evidence_requests: string[];
  triggered_by: string[];
  workstreams: string[];
  dd_master_ref: string | null;
  out_of_scope_note: string | null;
  edited_by_human: boolean;
  original_tier: number | null;
  original_title: string | null;
  override_reason: string | null;
}

export interface SequencePhase {
  name: string;
  weeks: string;
  focus: string;
  /** What this phase hands to the next one. Absent on the closing phase. */
  output?: string | null;
  row_ids: string[];
}

export interface CostLine {
  category: "one_time" | "recurring";
  label: string;
  basis: string;
}

export interface CostPlan {
  approach: string;
  lines: CostLine[];
  assumptions_register: string[];
  required: boolean;
}

export interface TeamShape {
  core_team: string[];
  specialists: string[];
  note: string | null;
}

export interface Exclusion {
  subject: string;
  reason: string;
  rule_code: string | null;
}

export interface FiredRule {
  code: string;
  label: string;
  effect: string;
  detail: Record<string, unknown>;
  citation: string | null;
  provenance: SourceProvenance;
}

export interface ScopeNote {
  code: string;
  label: string;
  text: string | null;
  citation: string | null;
  provenance: SourceProvenance;
}

export interface ScopeOfWorkPayloadV2 {
  schema_version: 2;
  is_placeholder: boolean;
  generator: string;
  library_version: string;
  rules_version: string;
  prompt_version: string | null;
  deck_title: string;
  deck_subtitle: string;
  classification: Classification;
  engagement_summary: string;
  objectives: string[];
  rows: ScopedRow[];
  sequencing: SequencePhase[];
  cost_plan: CostPlan;
  team_shape: TeamShape;
  diligence_risks: string[];
  exclusions: Exclusion[];
  provenance: FiredRule[];
  notes: ScopeNote[];
}

export type ScopeOfWorkPayload = ScopeOfWorkPayloadV1 | ScopeOfWorkPayloadV2;

export function isV2Payload(payload: ScopeOfWorkPayload): payload is ScopeOfWorkPayloadV2 {
  return payload.schema_version === 2;
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

export interface ScopePreview {
  classification: Classification;
  row_count: number;
  deck: string;
  is_complete: boolean;
}

export interface LibraryRow {
  id: string;
  sn: number;
  deck: string;
  title: string;
  lines: string[];
  workstreams: string[];
  base_tier: number;
  always_in_scope: boolean;
  dd_master_ref: string | null;
}

export interface WorkstreamLibrary {
  library_version: string;
  source_document: string;
  source_owner: string;
  decks: Record<string, LibraryRow[]>;
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
