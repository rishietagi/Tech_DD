import { ClassificationHeader } from "@/components/engagement/classification-header";
import { ScopeRowCard } from "@/components/engagement/scope-row-card";
import type { ScopeOfWorkPayloadV2 } from "@/types/engagement";

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-10">
      <h2 className="mb-1 font-display text-lg font-semibold text-text">{title}</h2>
      {subtitle && <p className="mb-3 font-sans text-[13px] text-muted">{subtitle}</p>}
      <div className={subtitle ? "" : "mt-3"}>{children}</div>
    </section>
  );
}

export function ScopeDocumentV2({ scope }: { scope: ScopeOfWorkPayloadV2 }) {
  const { classification, cost_plan, team_shape } = scope;
  const productRows = scope.rows.filter((row) => row.deck === "product");
  const enterpriseRows = scope.rows.filter((row) => row.deck === "enterprise");
  const isBlended = productRows.length > 0 && enterpriseRows.length > 0;

  return (
    <article>
      <header className="mb-8">
        <div className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
          {scope.deck_subtitle}
        </div>
        <h1 className="font-display text-3xl font-semibold text-text">{scope.deck_title}</h1>
      </header>

      <ClassificationHeader classification={classification} generator={scope.generator} />

      <Section title="Engagement">
        <p className="max-w-[72ch] font-sans text-[15px] leading-[1.65] text-text">
          {scope.engagement_summary}
        </p>
      </Section>

      <Section title="Objectives">
        <ul className="max-w-[72ch] list-disc space-y-1.5 pl-5 font-sans text-[14.5px] leading-[1.6] text-text">
          {scope.objectives.map((objective) => (
            <li key={objective}>{objective}</li>
          ))}
        </ul>
      </Section>

      <Section title="Scope of work" subtitle={`${scope.rows.length} areas in scope for this engagement.`}>
        {isBlended ? (
          <>
            <h3 className="mt-2 mb-1 font-sans text-[11px] font-semibold tracking-[0.06em] text-muted-2 uppercase">
              Product due diligence
            </h3>
            <div className="mb-6">
              {productRows.map((row) => (
                <ScopeRowCard key={row.id} row={row} />
              ))}
            </div>
            <h3 className="mt-2 mb-1 font-sans text-[11px] font-semibold tracking-[0.06em] text-muted-2 uppercase">
              Enterprise IT due diligence
            </h3>
            <div>
              {enterpriseRows.map((row) => (
                <ScopeRowCard key={row.id} row={row} />
              ))}
            </div>
          </>
        ) : (
          scope.rows.map((row) => <ScopeRowCard key={row.id} row={row} />)
        )}
      </Section>

      {scope.sequencing.length > 0 && (
        <Section title="Sequencing" subtitle="A broad pass identifies the areas of focus; the deep dive works on those.">
          <ol className="space-y-3">
            {scope.sequencing.map((phase) => (
              <li key={phase.name} className="rounded-xl border border-line bg-paper-2 px-4 py-3">
                <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-display text-[15px] font-semibold text-text">{phase.name}</span>
                  <span className="font-sans text-[12.5px] font-medium text-kpmg-blue">{phase.weeks}</span>
                </div>
                <p className="font-sans text-[13.5px] leading-[1.55] text-muted">{phase.focus}</p>
                {phase.output && (
                  <p className="mt-1.5 font-sans text-[13px] leading-[1.5] text-steel">
                    <span className="font-semibold">Output:</span> {phase.output}
                  </p>
                )}
                {phase.row_ids.length > 0 && (
                  <p className="mt-1 font-sans text-[12px] text-muted-2">
                    {phase.row_ids.length} area{phase.row_ids.length === 1 ? "" : "s"}
                  </p>
                )}
              </li>
            ))}
          </ol>
        </Section>
      )}

      <Section title="Cost estimation">
        <p className="mb-3 max-w-[72ch] font-sans text-[14px] leading-[1.6] text-text">{cost_plan.approach}</p>
        {cost_plan.lines.length > 0 && (
          <ul className="mb-4 space-y-2">
            {cost_plan.lines.map((line) => (
              <li key={line.label} className="font-sans text-[14px] text-text">
                <span className="mr-2 rounded-full border border-line-strong px-2 py-0.5 font-sans text-[11px] font-medium text-muted uppercase">
                  {line.category === "one_time" ? "one-time" : "recurring"}
                </span>
                {line.label}
                <span className="ml-1 text-muted"> — {line.basis}</span>
              </li>
            ))}
          </ul>
        )}
        <h3 className="mb-1.5 font-sans text-[11px] font-semibold text-muted-2 uppercase">
          Assumptions register
        </h3>
        <ul className="list-disc space-y-1 pl-5 font-sans text-[13.5px] text-muted">
          {cost_plan.assumptions_register.map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
      </Section>

      <Section title="Team">
        <ul className="space-y-1 font-sans text-[14px] text-text">
          {team_shape.core_team.map((member) => (
            <li key={member}>{member}</li>
          ))}
        </ul>
        {team_shape.specialists.length > 0 && (
          <>
            <h3 className="mt-3 mb-1.5 font-sans text-[11px] font-semibold text-muted-2 uppercase">
              Specialists required
            </h3>
            <ul className="space-y-1 font-sans text-[14px] text-text">
              {team_shape.specialists.map((specialist) => (
                <li key={specialist}>{specialist}</li>
              ))}
            </ul>
          </>
        )}
        {team_shape.note && <p className="mt-2 font-sans text-[13.5px] text-muted">{team_shape.note}</p>}
      </Section>

      {scope.notes.length > 0 && (
        <Section title="Notes" subtitle="Points the reference methodology attaches to engagements like this one.">
          <ul className="space-y-3">
            {scope.notes
              .filter((note) => note.text)
              .map((note) => (
                <li key={note.code} className="rounded-xl border border-line bg-paper-2 px-4 py-3">
                  <p className="mb-1 font-sans text-[13px] font-semibold text-text">{note.label}</p>
                  <p className="font-sans text-[13.5px] leading-[1.55] text-muted">{note.text}</p>
                  {note.citation && (
                    <p className="mt-1 font-sans text-[12px] text-muted-2 italic">{note.citation}</p>
                  )}
                </li>
              ))}
          </ul>
        </Section>
      )}

      {scope.diligence_risks.length > 0 && (
        <Section title="Risks to the diligence itself">
          <ul className="max-w-[72ch] list-disc space-y-1.5 pl-5 font-sans text-[14px] leading-[1.6] text-text">
            {scope.diligence_risks.map((risk) => (
              <li key={risk}>{risk}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Exclusions" subtitle="A scope that does not say what it excludes is not a scope.">
        <ul className="space-y-2.5">
          {scope.exclusions.map((exclusion) => (
            <li key={exclusion.subject} className="max-w-[72ch] font-sans text-[14px] leading-[1.6]">
              <span className="font-medium text-text">{exclusion.subject}</span>
              <span className="text-muted"> — {exclusion.reason}</span>
              {exclusion.rule_code && (
                <span className="ml-1 font-sans text-[12px] text-muted-2">({exclusion.rule_code})</span>
              )}
            </li>
          ))}
        </ul>
      </Section>

      <Section
        title="Provenance"
        subtitle="Every rule that shaped this scope, so a reviewer can interrogate any part of it."
      >
        <ul className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
          {scope.provenance.map((rule) => (
            <li key={rule.code} className="font-sans text-[12.5px] text-muted">
              <span className="mr-1.5 font-medium text-kpmg-blue">{rule.code}</span>
              {rule.label}
              {rule.provenance === "extended" && (
                <span className="ml-1.5 text-muted-2 italic">extended practice</span>
              )}
              {rule.citation && <span className="ml-1.5 text-muted-2 italic">· {rule.citation}</span>}
            </li>
          ))}
        </ul>
      </Section>

      <footer className="mt-10 border-t border-line pt-4 font-sans text-[12px] text-muted-2">
        Library v{scope.library_version} · rules v{scope.rules_version}
        {scope.prompt_version && <> · prompt v{scope.prompt_version}</>} · generated by {scope.generator}
      </footer>
    </article>
  );
}
