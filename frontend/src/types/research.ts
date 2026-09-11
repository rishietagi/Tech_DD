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

export interface BriefSection {
  text: string;
  source_ids: string[];
}

/** The deep business understanding. Every section optional — a thin public record
 *  produces a thin brief, and the UI omits what the sources could not support. */
export interface BusinessBrief {
  executive_summary: BriefSection;
  what_they_do: BriefSection;
  how_they_make_money: BriefSection;
  customers_and_markets: BriefSection;
  sector_context: BriefSection;
  competitive_position: BriefSection;
  implications_for_diligence: BriefSection;
}

export type BriefSectionKey = keyof BusinessBrief;

/** Rendered in this order. The executive summary leads; the diligence implications
 *  close, because they are the bridge to the rest of the product. */
export const BRIEF_ORDER: BriefSectionKey[] = [
  "executive_summary",
  "what_they_do",
  "how_they_make_money",
  "customers_and_markets",
  "sector_context",
  "competitive_position",
  "implications_for_diligence",
];

export const BRIEF_LABELS: Record<BriefSectionKey, string> = {
  executive_summary: "Executive summary",
  what_they_do: "What they do",
  how_they_make_money: "How they make money",
  customers_and_markets: "Customers and markets",
  sector_context: "The sector",
  competitive_position: "Competitive position",
  implications_for_diligence: "What this means for the diligence",
};

export interface ResearchPayload {
  schema_version: 1;
  generator: string;
  prompt_version?: string | null;
  company_name?: string | null;
  summary: string;
  /** Null for runs stored before 2026-09-11, and when the sources supported nothing. */
  business_brief?: BusinessBrief | null;
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
