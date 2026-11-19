"use client";

import { BandBadge } from "@/components/engagement/band-badge";
import type {
  ApplicationsScorePayload,
  DataTechScorePayload,
  EstateScorePayload,
  SectionScore,
  StrategyProjectsScorePayload,
  TeamGovernanceScorePayload,
} from "@/types/estate";

function Meter({ value, max = 5 }: { value: number | null; max?: number }) {
  if (value === null)
    return <span className="font-mono text-[11px] text-muted-2">—</span>;
  return (
    <span
      className="inline-flex items-center gap-1.5"
      title={`${value} of ${max}`}
    >
      <span className="flex gap-[2px]" aria-hidden>
        {Array.from({ length: max }, (_, i) => (
          <span
            key={i}
            className={`h-3 w-[6px] rounded-[1px] ${i < value ? "bg-ink" : "bg-line"}`}
          />
        ))}
      </span>
      <span className="font-mono text-[11.5px] text-text">{value}</span>
    </span>
  );
}

function Stat({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-line-strong px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-wide text-muted">
        {label}
      </p>
      <p className="font-serif text-[26px] leading-tight text-ink">{value}</p>
      {sub && <p className="font-sans text-[11.5px] text-muted-2">{sub}</p>}
    </div>
  );
}

/** Headline, written summary and pointers — the same for every assessment. */
export function ScoreHeader({
  payload,
  version,
  indexLabel,
}: {
  payload: EstateScorePayload;
  version: number;
  indexLabel: string;
}) {
  return (
    <section className="mb-8 grid gap-6 rounded-2xl border border-line-strong bg-paper p-6 lg:grid-cols-[260px_minmax(0,1fr)]">
      <div>
        <p className="font-mono text-[10.5px] uppercase tracking-wide text-muted">
          {indexLabel}
        </p>
        {payload.index !== null && payload.band ? (
          <>
            <p className="font-serif text-[52px] leading-none text-ink">
              {payload.index.toFixed(0)}
              <span className="text-[20px] text-muted-2">/100</span>
            </p>
            <div className="mt-2">
              <BandBadge
                band={payload.band}
                title={payload.band_meaning}
                label={payload.band_label}
              />
            </div>
            <p className="mt-3 font-sans text-[12.5px] leading-[1.5] text-muted">
              {payload.band_meaning}
            </p>
          </>
        ) : (
          <p className="mt-2 font-sans text-[14px] text-muted">
            Not enough evidence for an index yet.
          </p>
        )}
        <p className="mt-4 font-mono text-[10.5px] uppercase text-muted-2">
          Version {version} ·{" "}
          {payload.generator === "llm"
            ? "summary written by the model"
            : "rules summary"}
        </p>
      </div>
      <div>
        <p className="mb-1.5 font-mono text-[10.5px] uppercase tracking-wide text-muted">
          Executive summary
        </p>
        <p className="font-sans text-[15px] leading-[1.65] text-text">
          {payload.executive_summary}
        </p>
        {payload.pointers.length > 0 && (
          <>
            <p className="mt-5 mb-1.5 font-mono text-[10.5px] uppercase tracking-wide text-muted">
              Pointers
            </p>
            <ul className="list-disc space-y-1 pl-5 font-sans text-[13.5px] leading-[1.55] text-text">
              {payload.pointers.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </>
        )}
        {payload.coverage_note && (
          <p className="mt-4 rounded-lg bg-paper-2 px-3.5 py-2.5 font-sans text-[12.5px] text-muted">
            {payload.coverage_note}
          </p>
        )}
      </div>
    </section>
  );
}

const BAD_FLAGS = new Set([
  "End of life",
  "Key person",
  "Weak recovery",
  "Fails at peak",
  "Over budget",
  "Late",
  "Off track",
  "Spend ahead of delivery",
]);

function Flags({ flags }: { flags: string[] }) {
  if (flags.length === 0)
    return <span className="text-[12px] text-muted-2">None</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {flags.map((flag) => (
        <span
          key={flag}
          className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
            BAD_FLAGS.has(flag)
              ? "bg-priority-critical-tint text-priority-critical"
              : "bg-priority-high-tint text-priority-high"
          }`}
        >
          {flag}
        </span>
      ))}
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted">
      {children}
    </th>
  );
}

/** Section scores as a row of small cards — shared by every questionnaire. */
function SectionCards({ sections }: { sections: SectionScore[] }) {
  if (sections.length === 0) return null;
  return (
    <div>
      <p className="mb-2 font-mono text-[10.5px] uppercase tracking-wide text-muted">
        Sections
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {sections.map((s) => (
          <div
            key={s.key}
            className="rounded-xl border border-line-strong px-4 py-3"
          >
            <p className="font-mono text-[10px] uppercase tracking-wide text-muted">
              {s.label} · weight {s.weight}
            </p>
            <p className="font-serif text-[26px] leading-tight text-ink">
              {s.score !== null ? s.score.toFixed(0) : "—"}
            </p>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-paper-3">
              <div
                className="h-full rounded-full bg-ink"
                style={{ width: `${s.score ?? 0}%` }}
              />
            </div>
            <p className="mt-1 font-sans text-[11.5px] text-muted-2">
              {s.score === null
                ? "No evidence — excluded"
                : `${s.evidence} with evidence`}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Applications: criticality, automation and AI per application, and the facts that raised
 * an observation. No fit score and no disposition — a due diligence asks what the landscape
 * means for the deal, not what to do with each system (Phase 8).
 */
export function ApplicationResults({
  payload,
}: {
  payload: ApplicationsScorePayload;
}) {
  const { counts } = payload;
  return (
    <section className="mb-10 space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Stat
          label="Applications"
          value={String(counts.applications)}
          sub={`${counts.assessed} with a criticality`}
        />
        <Stat label="Business-critical" value={String(counts.critical)} />
        <Stat
          label="End of support ≤ 24 months"
          value={String(counts.end_of_life)}
        />
        <Stat
          label="Critical and manual"
          value={String(counts.manual_critical)}
        />
        <Stat
          label="AI level"
          value={payload.ai_index !== null ? payload.ai_index.toFixed(0) : "—"}
          sub="criticality-weighted, of 100"
        />
      </div>
      <SectionCards sections={payload.portfolio} />
      <div className="overflow-x-auto rounded-2xl border border-line-strong">
        <table className="w-full min-w-[860px] border-collapse font-sans text-[13px]">
          <thead>
            <tr className="bg-paper-2 text-left">
              <Th>Application</Th>
              <Th>Criticality</Th>
              <Th>Automation</Th>
              <Th>AI</Th>
              <Th>From the inventory</Th>
            </tr>
          </thead>
          <tbody>
            {payload.applications.map((app) => (
              <tr key={app.item_id} className="border-t border-line align-top">
                <td className="px-4 py-3">
                  <div className="font-medium text-text">
                    <span className="mr-2 font-mono text-[11.5px] text-muted">
                      {app.ref}
                    </span>
                    {app.name}
                  </div>
                  {app.category && (
                    <div className="text-[12px] text-muted-2">
                      {app.category}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <Meter value={app.criticality} />
                </td>
                <td className="px-4 py-3">
                  <Meter value={app.automation} />
                  {app.automation_label && (
                    <div className="mt-0.5 text-[11.5px] text-muted">
                      {app.automation_label}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <Meter value={app.ai} />
                  {app.ai_label && (
                    <div className="mt-0.5 text-[11.5px] text-muted">
                      {app.ai_label}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <Flags flags={app.flags} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function money(value: number | null): string {
  return value === null ? "—" : value.toLocaleString("en-GB");
}

/** Team & governance: the people facts counted, and the maturity of each section. */
export function TeamGovernanceResults({
  payload,
}: {
  payload: TeamGovernanceScorePayload;
}) {
  const { people } = payload;
  return (
    <section className="mb-10 space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat
          label="IT roles"
          value={String(people.headcount)}
          sub={`${people.in_house} in-house`}
        />
        <Stat
          label="Outsourced or shared"
          value={
            people.outsourced_share_pct !== null
              ? `${people.outsourced_share_pct.toFixed(0)}%`
              : "—"
          }
          sub={`${people.outsourced} outsourced · ${people.contractor} contractor · ${people.parent_shared} parent`}
        />
        <Stat
          label="Only one person can do it"
          value={String(people.sole_holders.length)}
        />
        <Stat
          label="Critical apps, one supporter"
          value={String(people.single_person_critical_apps.length)}
        />
      </div>
      {(people.single_person_critical_apps.length > 0 ||
        people.sole_holders.length > 0) && (
        <div className="rounded-2xl border border-line-strong px-5 py-4 font-sans text-[13px] text-text">
          {people.single_person_critical_apps.length > 0 && (
            <p>
              <span className="font-semibold">Supported by one person: </span>
              {people.single_person_critical_apps.join(", ")}
            </p>
          )}
          {people.sole_holders.length > 0 && (
            <p className="mt-1">
              <span className="font-semibold">
                Roles only one person holds:{" "}
              </span>
              {people.sole_holders.join(", ")}
            </p>
          )}
        </div>
      )}
      <SectionCards sections={payload.sections} />
    </section>
  );
}

/** Strategy & projects: the portfolio on the target's own figures, and the reconciliation. */
export function StrategyProjectsResults({
  payload,
}: {
  payload: StrategyProjectsScorePayload;
}) {
  const { portfolio } = payload;
  return (
    <section className="mb-10 space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat
          label="Projects"
          value={String(portfolio.projects)}
          sub={`${portfolio.open} in flight · ${portfolio.planned} planned`}
        />
        <Stat
          label="Remaining commitment"
          value={money(portfolio.remaining_commitment)}
          sub="allocated, not yet spent"
        />
        <Stat
          label={`Change budget ${portfolio.change_budget_year}`.trim()}
          value={money(portfolio.change_budget)}
          sub={
            portfolio.unfunded
              ? `roadmap short by ${money(portfolio.unfunded)}`
              : portfolio.change_budget === null
                ? "not entered on the IT budget tab"
                : "covers the roadmap"
          }
        />
        <Stat
          label="Over budget · late"
          value={`${portfolio.over_budget} · ${portfolio.late}`}
          sub={`${portfolio.stop_candidates} ${portfolio.stop_candidates === 1 ? "candidate" : "candidates"} to stop`}
        />
      </div>
      <SectionCards sections={payload.sections} />
      {payload.projects.length > 0 && (
        <div className="overflow-x-auto rounded-2xl border border-line-strong">
          <table className="w-full min-w-[900px] border-collapse font-sans text-[13px]">
            <thead>
              <tr className="bg-paper-2 text-left">
                <Th>Project</Th>
                <Th>Status</Th>
                <Th>Allocated</Th>
                <Th>Used</Th>
                <Th>Complete</Th>
                <Th>Deal relevance</Th>
                <Th>Observations</Th>
              </tr>
            </thead>
            <tbody>
              {payload.projects.map((pr) => (
                <tr key={pr.item_id} className="border-t border-line align-top">
                  <td className="px-4 py-3 font-medium text-text">
                    <span className="mr-2 font-mono text-[11.5px] text-muted">
                      {pr.ref}
                    </span>
                    {pr.name}
                  </td>
                  <td className="px-4 py-3 text-muted">{pr.status || "—"}</td>
                  <td className="px-4 py-3 font-mono text-[12.5px]">
                    {money(pr.allocated)}
                  </td>
                  <td className="px-4 py-3 font-mono text-[12.5px]">
                    {money(pr.used)}
                    {pr.spend_pct !== null && (
                      <span className="ml-1 text-muted-2">
                        ({pr.spend_pct.toFixed(0)}%)
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-[12.5px]">
                    {pr.pct_complete !== null
                      ? `${pr.pct_complete.toFixed(0)}%`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-muted">{pr.triage || "—"}</td>
                  <td className="px-4 py-3">
                    <Flags flags={pr.flags} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

const CHECK_CLASSES: Record<string, string> = {
  pass: "bg-status-received-tint text-status-received",
  partial: "bg-priority-high-tint text-priority-high",
  fail: "bg-priority-critical-tint text-priority-critical",
  unknown: "bg-priority-low-tint text-priority-low",
  unanswered: "bg-paper-2 text-muted-2",
};

export function DataTechResults({
  payload,
}: {
  payload: DataTechScorePayload;
}) {
  return (
    <section className="mb-10 space-y-8">
      <SectionCards sections={payload.sections} />

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <p className="mb-2 font-mono text-[10.5px] uppercase tracking-wide text-muted">
            Data domains
          </p>
          <ul className="divide-y divide-line rounded-2xl border border-line-strong">
            {payload.domains.length === 0 && (
              <li className="px-4 py-3 font-sans text-[13px] text-muted-2">
                None inventoried.
              </li>
            )}
            {payload.domains.map((d) => (
              <li
                key={d.item_id}
                className="flex items-center justify-between gap-3 px-4 py-3"
              >
                <div>
                  <p className="font-sans text-[13.5px] font-medium text-text">
                    <span className="mr-2 font-mono text-[11.5px] text-muted">
                      {d.ref}
                    </span>
                    {d.name}
                  </p>
                  <p className="font-sans text-[11.5px] text-muted-2">
                    {[d.sensitivity, d.owner_named ? "owner named" : "no owner"]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
                <span className="font-mono text-[14px] text-text">
                  {d.score ?? "—"}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 font-mono text-[10.5px] uppercase tracking-wide text-muted">
            Infrastructure platforms
          </p>
          <ul className="divide-y divide-line rounded-2xl border border-line-strong">
            {payload.platforms.length === 0 && (
              <li className="px-4 py-3 font-sans text-[13px] text-muted-2">
                None inventoried.
              </li>
            )}
            {payload.platforms.map((p) => (
              <li
                key={p.item_id}
                className="flex items-center justify-between gap-3 px-4 py-3"
              >
                <div>
                  <p className="font-sans text-[13.5px] font-medium text-text">
                    <span className="mr-2 font-mono text-[11.5px] text-muted">
                      {p.ref}
                    </span>
                    {p.name}
                  </p>
                  <p className="font-sans text-[11.5px] text-muted-2">
                    {[
                      p.category,
                      p.lifecycle,
                      p.hosted_apps.length
                        ? `hosts ${p.hosted_apps.join(", ")}`
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
                <span className="font-mono text-[14px] text-text">
                  {p.score ?? "—"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div>
        <p className="mb-2 font-mono text-[10.5px] uppercase tracking-wide text-muted">
          Estate checks
        </p>
        <div className="grid gap-2 md:grid-cols-2">
          {payload.checks.map((c) => (
            <div
              key={c.id}
              className="flex items-start gap-3 rounded-xl border border-line px-3.5 py-2.5"
            >
              <span
                className={`mt-0.5 w-[78px] flex-none rounded-full px-2 py-0.5 text-center font-sans text-[10.5px] font-semibold uppercase ${CHECK_CLASSES[c.status]}`}
              >
                {c.status === "unanswered" ? "—" : c.status}
              </span>
              <div className="font-sans text-[12.5px] leading-[1.45] text-text">
                <p>
                  <span className="mr-1.5 font-mono text-[11px] text-muted">
                    {c.id}
                  </span>
                  {c.text}
                </p>
                {c.source === "inventory" && (
                  <p className="mt-0.5 text-[11.5px] text-priority-critical">
                    Defaulted from the cyber tools inventory — not yet answered
                  </p>
                )}
                {c.evidence.map((line) => (
                  <p key={line} className="mt-0.5 text-[11.5px] text-muted-2">
                    {line}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
