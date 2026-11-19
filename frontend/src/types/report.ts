/** The final report. Mirrors backend/app/schemas/report.py. */

export type RiskLevel = "High" | "Medium" | "Low" | "Not assessed";
export const RISK_LEVELS: RiskLevel[] = [
  "High",
  "Medium",
  "Low",
  "Not assessed",
];
export type BlockKind = "paragraph" | "bullets" | "table" | "diagram" | "image";

export interface LandscapeItem {
  name: string;
  detail?: string;
  hosts?: string[];
}

export interface LandscapeModel {
  kind: "landscape";
  erp: { name: string; functions: string[] } | null;
  app_groups: { label: string; items: LandscapeItem[] }[];
  infra_groups: { label: string; items: LandscapeItem[] }[];
  backup: string[];
  empty: boolean;
}

export interface Block {
  id: string;
  kind: BlockKind;
  title: string;
  text: string;
  items: string[];
  columns: string[];
  rows: string[][];
  diagram: LandscapeModel | null;
  asset_id: string | null;
  include: boolean;
}

export interface ReportSection {
  id: string;
  title: string;
  panel: string;
  blocks: Block[];
  include: boolean;
}

/** One finding of the executive summary — a row of the Gaps & Risks table (Phase 8). */
export interface ExecutiveFinding {
  key: string;
  headline: string;
  bullets: string[];
  implication: string;
  impact: string[];
  risk: RiskLevel;
  actions: string[];
  investment: string;
  source: string;
  include: boolean;
}

/** A diligence area and its findings. */
export interface ExecutiveRow {
  area_id: string;
  sn: number;
  title: string;
  findings: ExecutiveFinding[];
  risk: RiskLevel;
  note: string;
  include: boolean;
}

export interface ReportPayload {
  schema_version: 2;
  generator: string;
  skill_versions: Record<string, string>;
  generated_at: string;
  dd_type: string;
  dd_mix: number | null;
  target_name: string;
  investor_name: string;
  cover: {
    codename: string;
    title: string;
    subtitle: string;
    date_label: string;
  };
  context: {
    objective: string;
    approach: string;
    outcome: string;
    key_areas: string[];
    cutoff: string;
  };
  glossary: { term: string; expansion: string }[];
  in_scope: {
    area_id: string;
    title: string;
    considerations: string[];
    include: boolean;
  }[];
  limitations: {
    area_id: string;
    title: string;
    items: string[];
    include: boolean;
  }[];
  executive_title: string;
  executive: ExecutiveRow[];
  supporting: ReportSection[];
  appendix: ReportSection[];
  source_line: string;
  edited_keys: string[];
}

export interface ReportRead {
  id: string;
  engagement_id: string;
  version: number;
  generator: string;
  payload: ReportPayload;
  created_at: string;
}

export interface ReportAsset {
  id: string;
  title: string;
  caption: string;
  mime: string;
  created_at: string;
}

export type EditValue =
  | string
  | string[]
  | boolean
  | string[][]
  | { term: string; expansion: string }[];

// ------------------------------------------------------------------ intelligence

export interface SkillStatus {
  name: string;
  description: string;
  version: string;
  mode: string;
  deterministic_fallback: string;
  inputs: string[];
  outputs: string[];
  may_change: string[];
  must_not_change: string[];
  house_rules: string[];
  used_by: string[];
  status: "deterministic" | "llm";
  reason: string;
  body: string;
}

export interface IntelligenceStatus {
  mode: "off" | "auto";
  key_present: boolean;
  model: string;
  active: boolean;
  skills: SkillStatus[];
}
