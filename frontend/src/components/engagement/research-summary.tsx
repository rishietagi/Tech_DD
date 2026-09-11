import type {
  BriefSection,
  BusinessBrief,
  ResearchFinding,
  ResearchPayload,
  ResearchSource,
} from "@/types/research";
import { BRIEF_LABELS, BRIEF_ORDER, RESEARCH_CATEGORY_LABELS } from "@/types/research";

/** The disclaimer leads. It is the first thing a reader sees, not a footnote, because
 *  the failure mode of AI research is confident, well-formatted, plausible wrongness. */
function Disclaimer({ text }: { text: string }) {
  return (
    <div
      role="note"
      className="mb-8 rounded-xl border border-redline/40 bg-redline-tint px-4 py-3"
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
function SourceLink({ source, showId = true }: { source: ResearchSource; showId?: boolean }) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      title={source.title}
      className="font-sans text-[12.5px] text-steel underline underline-offset-2 hover:text-kpmg-blue"
    >
      {showId && <span className="font-mono text-[10.5px] text-muted-2">{source.id} </span>}
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
    <p className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
      <span className="font-mono text-[9.5px] tracking-wide text-muted-2 uppercase">
        Sources
      </span>
      {cited.map((source) => (
        <SourceLink key={source.id} source={source} />
      ))}
    </p>
  );
}

/** One section of the business brief.
 *
 *  The executive summary renders larger and un-boxed — it is the section a partner reads
 *  on its own, and boxing it would make it one card among seven rather than the lead. */
function BriefBlock({
  label,
  section,
  sources,
  lead = false,
  analysis = false,
}: {
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

  if (lead) {
    return (
      <section className="mb-8">
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
      </section>
    );
  }

  return (
    <section
      className={`rounded-xl border px-5 py-4 ${
        analysis
          ? "border-steel/40 bg-steel-tint"
          : "border-line-strong bg-paper-2"
      }`}
    >
      <h3 className="mb-2 font-mono text-[10px] font-semibold tracking-[0.1em] text-muted uppercase">
        {label}
        {analysis && (
          <span className="ml-2 rounded-full border border-steel/50 bg-paper px-2 py-0.5 text-[9px] tracking-normal text-steel normal-case">
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
    </section>
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
        label={BRIEF_LABELS[lead]}
        section={brief[lead]}
        sources={sources}
        lead
      />

      {present.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {present.map((key) => (
            <div
              key={key}
              // The diligence implications close the brief and span the full width —
              // it is the bridge to the rest of the product, not one fact among several.
              className={key === "implications_for_diligence" ? "lg:col-span-2" : ""}
            >
              <BriefBlock
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
  return (
    <li className="border-t border-line py-4 first:border-t-0">
      <div className="mb-1 flex flex-wrap items-baseline gap-2">
        <h4 className="font-sans text-[14.5px] font-semibold text-text">{finding.topic}</h4>
        <span className="rounded-full bg-paper-3 px-2 py-0.5 font-sans text-[10.5px] font-medium text-muted uppercase">
          {RESEARCH_CATEGORY_LABELS[finding.category] ?? finding.category}
        </span>
      </div>
      <p className="max-w-[72ch] font-sans text-[14px] leading-[1.6] text-text">
        {finding.detail}
      </p>
      <Citations ids={finding.source_ids} sources={sources} />
    </li>
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

      {brief ? (
        <BusinessBriefView brief={brief} sources={sources} />
      ) : (
        // Runs stored before the brief existed, and runs where the record was too thin
        // to support one. The short summary is still worth showing.
        <section className="mb-8">
          <h2 className="mb-3 font-display text-lg font-semibold text-text">Summary</h2>
          <p className="max-w-[72ch] font-sans text-[15px] leading-[1.65] text-text">
            {research.summary}
          </p>
        </section>
      )}

      {research.findings.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-1 font-display text-lg font-semibold text-text">
            The record
          </h2>
          <p className="mb-3 max-w-[72ch] font-sans text-[13px] text-muted">
            Dated, specific points from the sources — the facts a deal team would cite.
            Check each one before relying on it.
          </p>
          <ul className="rounded-xl border border-line bg-paper-2 px-4">
            {research.findings.map((finding) => (
              <Finding key={finding.topic} finding={finding} sources={sources} />
            ))}
          </ul>
        </section>
      )}

      {research.sources.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 font-display text-lg font-semibold text-text">
            Sources ({research.sources.length})
          </h2>
          <ol className="space-y-1.5">
            {research.sources.map((source) => (
              <li key={source.id} className="font-sans text-[13.5px]">
                <span className="mr-2 font-mono text-[11px] text-muted-2">{source.id}</span>
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
        Researched {new Date(research.researched_at).toLocaleString()} · generated by{" "}
        {research.generator}
      </footer>
    </article>
  );
}
