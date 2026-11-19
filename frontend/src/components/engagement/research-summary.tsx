import type {
  BriefSection,
  BriefSectionKey,
  BusinessBrief,
  ResearchCategory,
  ResearchFinding,
  ResearchPayload,
  ResearchSource,
} from "@/types/research";
import {
  BRIEF_LABELS,
  BRIEF_ORDER,
  RESEARCH_CATEGORY_LABELS,
} from "@/types/research";

/** The disclaimer leads. It is the first thing a reader sees, not a footnote, because
 *  the failure mode of AI research is confident, well-formatted, plausible wrongness. */
function Disclaimer({ text }: { text: string }) {
  return (
    <div
      role="note"
      className="mb-6 rounded-xl border border-redline/40 bg-redline-tint px-4 py-3"
    >
      <p className="font-sans text-[13px] leading-[1.55] text-text">
        <span className="font-semibold">AI-generated research.</span>{" "}
        {text.replace(/^AI-generated research\s*—\s*/i, "")}
      </p>
    </div>
  );
}

/** One source link.
 *
 *  The id is shown beside the title because Gemini's grounding metadata gives only the
 *  domain as a title — five claims citing five different pages on rsgroup.com would
 *  otherwise render as five identical links, and a reader could not tell which was which
 *  or find it in the list at the foot of the page. */
function SourceLink({
  source,
  showId = true,
}: {
  source: ResearchSource;
  showId?: boolean;
}) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      title={source.title}
      // `break-all` + `min-w-0`: a grounding-metadata title is a bare domain, which is a
      // single unbreakable token. Without this it pushes the page sideways at phone width.
      className="max-w-full font-sans text-[12.5px] break-all text-steel underline underline-offset-2 hover:text-kpmg-blue"
    >
      {showId && (
        <span className="font-mono text-[10.5px] text-muted-2">
          {source.id}{" "}
        </span>
      )}
      {source.title}
    </a>
  );
}

/** The sources behind one claim, rendered small and beneath it.
 *
 *  Deliberately not superscript numerals: a diligence reader checks sources by clicking
 *  them, and a numeral they have to match against a list at the bottom is friction that
 *  stops them looking. */
function Citations({
  ids,
  sources,
}: {
  ids: string[];
  sources: Map<string, ResearchSource>;
}) {
  const cited = ids
    .map((id) => sources.get(id))
    .filter((s): s is ResearchSource => Boolean(s));
  if (cited.length === 0) return null;

  return (
    <p className="mt-2 flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">
      <span className="font-mono text-[9.5px] tracking-wide text-muted-2 uppercase">
        Sources
      </span>
      {cited.map((source) => (
        <SourceLink key={source.id} source={source} />
      ))}
    </p>
  );
}

/** A section with no citation behind it, marked as such.
 *
 *  Every section is supposed to be sourced. Where one is not, saying so on the card is
 *  more honest than rendering it identically to a cited one — and it matters most on the
 *  technology profile, which is the section a model is most able to invent plausibly. */
function Uncited() {
  return (
    <p className="mt-2 font-sans text-[11.5px] text-muted-2 italic">
      No source attached to this section — treat as unverified.
    </p>
  );
}

/** A small glyph per section, so the eye can find a card without reading its heading.
 *
 *  Inline SVG rather than an icon dependency: five shapes do not justify a package, and
 *  the CDN allowlist does not cover one anyway. `currentColor` so they inherit theme. */
function SectionIcon({ section }: { section: BriefSectionKey }) {
  const common = {
    width: 13,
    height: 13,
    viewBox: "0 0 16 16",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.6,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  switch (section) {
    case "what_they_do": // stacked boxes — operations
      return (
        <svg {...common}>
          <rect x="2" y="9" width="5" height="5" />
          <rect x="9" y="9" width="5" height="5" />
          <rect x="5.5" y="2" width="5" height="5" />
        </svg>
      );
    case "how_they_make_money": // rising bars — revenue
      return (
        <svg {...common}>
          <path d="M2 14V9M6.5 14V5M11 14V7M15 14V2.5" />
        </svg>
      );
    case "customers_and_markets": // people
      return (
        <svg {...common}>
          <circle cx="6" cy="5.5" r="2.5" />
          <path d="M1.5 14c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4" />
          <path d="M11 3.2a2.5 2.5 0 010 4.6M12.5 13.8c0-1.8-.6-3-1.6-3.7" />
        </svg>
      );
    case "sector_context": // globe
      return (
        <svg {...common}>
          <circle cx="8" cy="8" r="6" />
          <path d="M2 8h12M8 2c1.8 2 2.7 4 2.7 6S9.8 14 8 14 5.3 12 5.3 8 6.2 2 8 2z" />
        </svg>
      );
    case "competitive_position": // crossed flags / position marker
      return (
        <svg {...common}>
          <path d="M4 14V2.5l8 2.5-8 2.5" />
        </svg>
      );
    case "technology_profile": // chip
      return (
        <svg {...common}>
          <rect x="4.5" y="4.5" width="7" height="7" rx="1" />
          <path d="M7 2v2.5M9 2v2.5M7 11.5V14M9 11.5V14M2 7h2.5M2 9h2.5M11.5 7H14M11.5 9H14" />
        </svg>
      );
    default:
      return null;
  }
}

/** One section of the business brief.
 *
 *  The executive summary renders larger and un-boxed — it is the section a partner reads
 *  on its own, and boxing it would make it one card among several rather than the lead. */
function BriefBlock({
  sectionKey,
  label,
  section,
  sources,
  lead = false,
  analysis = false,
}: {
  sectionKey: BriefSectionKey;
  label: string;
  section: BriefSection;
  sources: Map<string, ResearchSource>;
  lead?: boolean;
  analysis?: boolean;
}) {
  if (!section.text.trim()) return null;

  // Paragraph breaks survive: the executive summary is asked for as 2-3 paragraphs and
  // collapsing them into one block would lose the structure the prompt requested.
  const paragraphs = section.text.split(/\n{2,}/).filter((p) => p.trim());
  const cited = section.source_ids.some((id) => sources.has(id));

  if (lead) {
    return (
      <section id={`brief-${sectionKey}`} className="mb-8 scroll-mt-6">
        <h3 className="mb-2 font-mono text-[10px] font-semibold tracking-[0.1em] text-kpmg-blue uppercase">
          {label}
        </h3>
        <div className="space-y-3">
          {paragraphs.map((paragraph) => (
            <p
              key={paragraph.slice(0, 40)}
              className="max-w-[76ch] font-sans text-[15.5px] leading-[1.7] text-text"
            >
              {paragraph}
            </p>
          ))}
        </div>
        <Citations ids={section.source_ids} sources={sources} />
        {!cited && <Uncited />}
      </section>
    );
  }

  return (
    <section
      id={`brief-${sectionKey}`}
      className={`h-full scroll-mt-6 rounded-xl border px-5 py-4 ${
        analysis
          ? "border-steel/40 bg-steel-tint"
          : "border-line-strong bg-paper-2"
      }`}
    >
      <h3 className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[10px] font-semibold tracking-[0.1em] text-muted uppercase">
        <span className={analysis ? "text-steel" : "text-muted-2"}>
          <SectionIcon section={sectionKey} />
        </span>
        {label}
        {analysis && (
          <span className="rounded-full border border-steel/50 bg-paper px-2 py-0.5 text-[9px] tracking-normal text-steel normal-case">
            Our analysis, not a sourced fact
          </span>
        )}
      </h3>
      <div className="space-y-2.5">
        {paragraphs.map((paragraph) => (
          <p
            key={paragraph.slice(0, 40)}
            className="font-sans text-[14px] leading-[1.65] text-text"
          >
            {paragraph}
          </p>
        ))}
      </div>
      <Citations ids={section.source_ids} sources={sources} />
      {!cited && !analysis && <Uncited />}
    </section>
  );
}

/** A jump rail across the top of the brief.
 *
 *  The brief runs long on a well-sourced target. A reader who wants the technology or
 *  the customers should not have to scroll past four cards to find out whether the
 *  section exists at all — and which sections are absent is itself information. */
function BriefNav({ present }: { present: BriefSectionKey[] }) {
  if (present.length < 2) return null;
  return (
    <nav
      aria-label="Jump to a section of the brief"
      className="mb-5 flex flex-wrap items-center gap-1.5"
    >
      {present.map((key) => (
        <a
          key={key}
          href={`#brief-${key}`}
          className="rounded-full border border-line-strong bg-paper px-2.5 py-1 font-sans text-[11.5px] text-muted transition-colors hover:border-kpmg-blue hover:text-kpmg-blue"
        >
          {BRIEF_LABELS[key]}
        </a>
      ))}
    </nav>
  );
}

function BusinessBriefView({
  brief,
  sources,
}: {
  brief: BusinessBrief;
  sources: Map<string, ResearchSource>;
}) {
  const [lead, ...rest] = BRIEF_ORDER;
  // Only sections the sources actually supported. An omitted section is the model
  // declining to invent one, which is the behaviour the prompt asks for.
  const present = rest.filter((key) => brief[key]?.text?.trim());

  return (
    <div className="mb-10">
      <BriefBlock
        sectionKey={lead}
        label={BRIEF_LABELS[lead]}
        section={brief[lead]}
        sources={sources}
        lead
      />

      <BriefNav present={present} />

      {present.length > 0 && (
        <div className="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-2">
          {present.map((key) => (
            <div
              key={key}
              // Two sections span the full width. The diligence implications close the
              // brief and are the bridge to the rest of the product; the technology
              // profile is the section a tech DD reader came for, and it lists systems
              // that wrap badly in a half-width card.
              className={
                key === "implications_for_diligence" ||
                key === "technology_profile"
                  ? "lg:col-span-2"
                  : ""
              }
            >
              <BriefBlock
                sectionKey={key}
                label={BRIEF_LABELS[key]}
                section={brief[key]}
                sources={sources}
                analysis={key === "implications_for_diligence"}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Finding({
  finding,
  sources,
}: {
  finding: ResearchFinding;
  sources: Map<string, ResearchSource>;
}) {
  const cited = finding.source_ids.some((id) => sources.has(id));
  return (
    <li className="border-t border-line py-3.5 first:border-t-0">
      <div className="mb-1 flex flex-wrap items-baseline gap-2">
        <h4 className="font-sans text-[14.5px] font-semibold text-text">
          {finding.topic}
        </h4>
        {!cited && (
          <span className="rounded-full border border-line-strong px-2 py-0.5 font-sans text-[10px] text-muted-2">
            uncited
          </span>
        )}
      </div>
      <p className="max-w-[72ch] font-sans text-[14px] leading-[1.6] text-text">
        {finding.detail}
      </p>
      <Citations ids={finding.source_ids} sources={sources} />
    </li>
  );
}

/** The record, grouped by category rather than run together.
 *
 *  Previously one flat list with a category pill on each row, which meant a reader
 *  scanning for the technology facts read every funding fact on the way. Grouping puts
 *  the count in the heading, so "Technology (0)" is visible as an absence — which on a
 *  tech diligence is worth knowing before the data room opens.
 *
 *  Order follows the prompt's own priority: overview, financial, technology, incidents,
 *  regulatory, market, people, then anything else. The list is exhaustive over
 *  ResearchCategory, so a new category added to the union is a compile error here rather
 *  than a group that silently fails to render. */
const CATEGORY_ORDER: ResearchCategory[] = [
  "overview",
  "financial",
  "technology",
  "incident",
  "regulatory",
  "market",
  "people",
  "other",
];

function TheRecord({
  findings,
  sources,
}: {
  findings: ResearchFinding[];
  sources: Map<string, ResearchSource>;
}) {
  const groups = new Map<ResearchCategory, ResearchFinding[]>();
  for (const finding of findings) {
    const list = groups.get(finding.category);
    if (list) list.push(finding);
    else groups.set(finding.category, [finding]);
  }

  const ordered = CATEGORY_ORDER.filter((c) => groups.has(c));

  return (
    <section className="mb-8">
      <h2 className="mb-1 font-display text-lg font-semibold text-text">
        The record
      </h2>
      <p className="mb-4 max-w-[72ch] font-sans text-[13px] text-muted">
        Dated, specific points from the sources — the facts a deal team would
        cite. Check each one before relying on it.
      </p>

      <div className="space-y-4">
        {ordered.map((category) => {
          const rows = groups.get(category) ?? [];
          return (
            <div
              key={category}
              className="rounded-xl border border-line bg-paper-2 px-4 py-2"
            >
              <h3 className="flex items-baseline gap-2 border-b border-line py-2 font-mono text-[10px] font-semibold tracking-[0.1em] text-muted uppercase">
                {RESEARCH_CATEGORY_LABELS[category]}
                <span className="font-sans text-[11px] tracking-normal text-muted-2 normal-case">
                  {rows.length}
                </span>
              </h3>
              <ul>
                {rows.map((finding) => (
                  <Finding
                    key={finding.topic}
                    finding={finding}
                    sources={sources}
                  />
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/** A strip of counts above the brief.
 *
 *  Answers "how much did this run actually find?" before the reader commits to reading
 *  it — a nine-source run and a two-source run deserve different levels of trust, and
 *  that was previously only discoverable by scrolling to the foot of the page. */
function RunStats({
  research,
  brief,
}: {
  research: ResearchPayload;
  brief: BusinessBrief | null;
}) {
  const sectionsPresent = brief
    ? BRIEF_ORDER.filter((key) => brief[key]?.text?.trim()).length
    : 0;
  const stats: Array<{ label: string; value: string; muted?: boolean }> = [
    { label: "Sources", value: String(research.sources.length) },
    { label: "Findings", value: String(research.findings.length) },
    {
      label: "Brief sections",
      value: brief ? `${sectionsPresent} of ${BRIEF_ORDER.length}` : "—",
      muted: !brief,
    },
  ];

  return (
    <dl className="mb-6 grid grid-cols-3 gap-3">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl border border-line-strong bg-paper-2 px-4 py-3"
        >
          <dt className="font-mono text-[9.5px] font-semibold tracking-[0.1em] text-muted-2 uppercase">
            {stat.label}
          </dt>
          <dd
            className={`mt-1 font-display text-[22px] leading-none ${
              stat.muted ? "text-muted-2" : "text-text"
            }`}
          >
            {stat.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function ResearchSummary({ research }: { research: ResearchPayload }) {
  // Findings cite sources by id; resolving here means a dangling id renders nothing
  // rather than an empty link.
  const sources = new Map(research.sources.map((s) => [s.id, s]));
  const brief = research.business_brief ?? null;

  return (
    <article>
      <Disclaimer text={research.disclaimer} />
      <RunStats research={research} brief={brief} />

      {brief ? (
        <BusinessBriefView brief={brief} sources={sources} />
      ) : (
        // Runs stored before the brief existed, and runs where the record was too thin
        // to support one. The short summary is still worth showing.
        <section className="mb-8">
          <h2 className="mb-3 font-display text-lg font-semibold text-text">
            Summary
          </h2>
          <p className="max-w-[72ch] font-sans text-[15px] leading-[1.65] text-text">
            {research.summary}
          </p>
        </section>
      )}

      {research.findings.length > 0 && (
        <TheRecord findings={research.findings} sources={sources} />
      )}

      {research.sources.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 font-display text-lg font-semibold text-text">
            Sources ({research.sources.length})
          </h2>
          <ol className="space-y-1.5">
            {research.sources.map((source) => (
              <li
                key={source.id}
                className="font-sans text-[13.5px] break-words"
              >
                <span className="mr-2 font-mono text-[11px] text-muted-2">
                  {source.id}
                </span>
                <SourceLink source={source} showId={false} />
                {source.publisher && (
                  <span className="ml-2 font-sans text-[12.5px] text-muted-2">
                    {source.publisher}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}

      <footer className="border-t border-line pt-4 font-sans text-[12px] text-muted-2">
        Researched {new Date(research.researched_at).toLocaleString()} ·
        generated by {research.generator}
      </footer>
    </article>
  );
}
