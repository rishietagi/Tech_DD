// Mirrors backend/app/schemas/research.py. If they drift, that is a bug (CLAUDE.md §7).

export type ResearchCategory =
  | "overview"
  | "financial"
  | "technology"
  | "incident"
  | "regulatory"
  | "market"
  | "people"
  | "other";

export const RESEARCH_CATEGORY_LABELS: Record<ResearchCategory, string> = {
  overview: "Overview",
  financial: "Financial",
  technology: "Technology",
  incident: "Incidents",
  regulatory: "Regulatory",
  market: "Market",
  people: "People",
  other: "Other",
};

export interface ResearchSource {
  id: string;
  title: string;
  url: string;
  publisher?: string | null;
}

export interface ResearchFinding {
  topic: string;
  detail: string;
  category: ResearchCategory;
  source_ids: string[];
}

export interface ResearchPayload {
  schema_version: 1;
  generator: string;
  prompt_version?: string | null;
  company_name?: string | null;
  summary: string;
  findings: ResearchFinding[];
  sources: ResearchSource[];
  /** Stored on the payload so a re-read run always carries its warning. */
  disclaimer: string;
  researched_at: string;
}

export interface ResearchRead {
  id: string;
  engagement_id: string;
  version: number;
  generator: string;
  company_name: string | null;
  payload: ResearchPayload;
  created_at: string;
}
