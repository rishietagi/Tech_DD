import { ClassificationHeader } from "@/components/engagement/classification-header";
import {
  type RowEdit,
  ScopeRowCard,
} from "@/components/engagement/scope-row-card";
import { EditableList, EditableText } from "@/components/ui/editable";
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
      <h2 className="mb-1 font-display text-lg font-semibold text-text">
        {title}
      </h2>
      {subtitle && (
        <p className="mb-3 font-sans text-[13px] text-muted">{subtitle}</p>
      )}
      <div className={subtitle ? "" : "mt-3"}>{children}</div>
    </section>
  );
}

export type DocumentEdit = {
  engagement_summary?: string;
  objectives?: string[];
  diligence_risks?: string[];
  delivery?: Record<string, string>;
};

const DELIVERY: { key: string; label: string }[] = [
  { key: "sequencing", label: "Sequencing" },
  { key: "timeline", label: "Timeline" },
  { key: "cost", label: "Cost estimation" },
  { key: "team", label: "Team" },
];

export function ScopeDocumentV2({
  scope,
  onEditRow,
  onEditDocument,
}: {
  scope: ScopeOfWorkPayloadV2;
  onEditRow?: (rowId: string, patch: RowEdit) => Promise<void>;
  onEditDocument?: (patch: DocumentEdit) => Promise<void>;
}) {
  const edits = scope.human_edits ?? {};
  const delivery = scope.delivery ?? {};
  const { classification } = scope;
  const productRows = scope.rows.filter((row) => row.deck === "product");
  const enterpriseRows = scope.rows.filter((row) => row.deck === "enterprise");
  const isBlended = productRows.length > 0 && enterpriseRows.length > 0;

  return (
    <article>
      <header className="mb-8">
        <div className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
          {scope.deck_subtitle}
        </div>
        <h1 className="font-display text-3xl font-semibold text-text">
          {scope.deck_title}
        </h1>
      </header>

      <ClassificationHeader
        classification={classification}
        generator={scope.generator}
      />

      <Section title="Engagement">
        {onEditDocument ? (
          <EditableText
            value={scope.engagement_summary}
            label="engagement summary"
            rows={5}
            edited={"engagement_summary" in edits}
            onSave={(engagement_summary) =>
              onEditDocument({ engagement_summary })
            }
          >
            <p className="max-w-[72ch] font-sans text-[15px] leading-[1.65] text-text">
              {scope.engagement_summary}
            </p>
          </EditableText>
        ) : (
          <p className="max-w-[72ch] font-sans text-[15px] leading-[1.65] text-text">
            {scope.engagement_summary}
          </p>
        )}
      </Section>

      <Section title="Objectives">
        <EditableList
          items={scope.objectives}
          label="objectives"
          edited={"objectives" in edits}
          onSave={async (objectives) => onEditDocument?.({ objectives })}
        >
          <ul className="max-w-[72ch] list-disc space-y-1.5 pl-5 font-sans text-[14.5px] leading-[1.6] text-text">
            {scope.objectives.map((objective) => (
              <li key={objective}>{objective}</li>
            ))}
          </ul>
        </EditableList>
      </Section>

      <Section
        title="Scope of work"
        subtitle={`${scope.rows.length} areas in scope for this engagement.`}
      >
        {isBlended ? (
          <>
            <h3 className="mt-2 mb-1 font-sans text-[11px] font-semibold tracking-[0.06em] text-muted-2 uppercase">
              Product due diligence
            </h3>
            <div className="mb-6">
              {productRows.map((row) => (
                <ScopeRowCard key={row.id} row={row} onEdit={onEditRow} />
              ))}
            </div>
            <h3 className="mt-2 mb-1 font-sans text-[11px] font-semibold tracking-[0.06em] text-muted-2 uppercase">
              Enterprise IT due diligence
            </h3>
            <div>
              {enterpriseRows.map((row) => (
                <ScopeRowCard key={row.id} row={row} onEdit={onEditRow} />
              ))}
            </div>
          </>
        ) : (
          scope.rows.map((row) => (
            <ScopeRowCard key={row.id} row={row} onEdit={onEditRow} />
          ))
        )}
      </Section>

      {/* Sequencing, cost estimation and team shape are judgement calls the
          engagement team makes against the specific deal, so the document shows them as
          XXX rather than asserting them (Rishi, 2026-09-02). The underlying values are
          still computed and still carried in the payload and the Markdown export; only
          the client-facing surfaces stop presenting them as settled. The section is kept
          rather than dropped so the reader can see what remains to be completed. */}
      <Section
        title="Delivery approach"
        subtitle="To be confirmed by the engagement team."
      >
        {/* XXX until the engagement team completes it; what is typed here is what the
            deck exports (editable before export since 2026-11-18). */}
        <dl className="max-w-[72ch] divide-y divide-line rounded-xl border border-line-strong">
          {DELIVERY.map(({ key, label }) => (
            <div
              key={key}
              className="grid grid-cols-[160px_minmax(0,1fr)] items-baseline gap-4 px-4 py-3"
            >
              <dt className="font-sans text-[14px] text-text">{label}</dt>
              <dd>
                <EditableText
                  value={delivery[key] ?? ""}
                  label={label}
                  rows={2}
                  onSave={async (value) =>
                    onEditDocument?.({ delivery: { [key]: value } })
                  }
                >
                  <span
                    className={
                      delivery[key]
                        ? "font-sans text-[14px] text-text"
                        : "font-mono text-[13px] tracking-wide text-muted-2"
                    }
                  >
                    {delivery[key] || "XXX"}
                  </span>
                </EditableText>
              </dd>
            </div>
          ))}
        </dl>
      </Section>

      {scope.notes.length > 0 && (
        <Section
          title="Notes"
          subtitle="Points the reference methodology attaches to engagements like this one."
        >
          <ul className="space-y-3">
            {scope.notes
              .filter((note) => note.text)
              .map((note) => (
                <li
                  key={note.code}
                  className="rounded-xl border border-line bg-paper-2 px-4 py-3"
                >
                  <p className="mb-1 font-sans text-[13px] font-semibold text-text">
                    {note.label}
                  </p>
                  <p className="font-sans text-[13.5px] leading-[1.55] text-muted">
                    {note.text}
                  </p>
                  {note.citation && (
                    <p className="mt-1 font-sans text-[12px] text-muted-2 italic">
                      {note.citation}
                    </p>
                  )}
                </li>
              ))}
          </ul>
        </Section>
      )}

      {scope.diligence_risks.length > 0 && (
        <Section title="Risks to the diligence itself">
          <EditableList
            items={scope.diligence_risks}
            label="diligence risks"
            edited={"diligence_risks" in edits}
            onSave={async (diligence_risks) =>
              onEditDocument?.({ diligence_risks })
            }
          >
            <ul className="max-w-[72ch] list-disc space-y-1.5 pl-5 font-sans text-[14px] leading-[1.6] text-text">
              {scope.diligence_risks.map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>
          </EditableList>
        </Section>
      )}

      <Section
        title="Exclusions"
        subtitle="A scope that does not say what it excludes is not a scope."
      >
        <ul className="space-y-2.5">
          {scope.exclusions.map((exclusion) => (
            <li
              key={exclusion.subject}
              className="max-w-[72ch] font-sans text-[14px] leading-[1.6]"
            >
              <span className="font-medium text-text">{exclusion.subject}</span>
              <span className="text-muted"> — {exclusion.reason}</span>
              {exclusion.rule_code && (
                <span className="ml-1 font-sans text-[12px] text-muted-2">
                  ({exclusion.rule_code})
                </span>
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
              <span className="mr-1.5 font-medium text-kpmg-blue">
                {rule.code}
              </span>
              {rule.label}
              {rule.provenance === "extended" && (
                <span className="ml-1.5 text-muted-2 italic">
                  extended practice
                </span>
              )}
              {rule.citation && (
                <span className="ml-1.5 text-muted-2 italic">
                  · {rule.citation}
                </span>
              )}
            </li>
          ))}
        </ul>
      </Section>

      <footer className="mt-10 border-t border-line pt-4 font-sans text-[12px] text-muted-2">
        Library v{scope.library_version} · rules v{scope.rules_version}
        {scope.prompt_version && <> · prompt v{scope.prompt_version}</>} ·
        generated by {scope.generator}
      </footer>
    </article>
  );
}
