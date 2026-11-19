"use client";

import { BandBadge } from "@/components/engagement/band-badge";
import {
  AiIndexExplain,
  AppFlagsExplain,
  ApplicationsIndexExplain,
  AutomationLevelExplain,
  ChecksExplain,
  CriticalManualExplain,
  CriticalityExplain,
  DataTechIndexExplain,
  DomainScoreExplain,
  KeyPersonExplain,
  OutsourcedExplain,
  PlatformScoreExplain,
  ProjectFlagsExplain,
  ReconciliationExplain,
  SectionsExplain,
  StrategyIndexExplain,
  TeamIndexExplain,
  TriageExplain,
} from "@/components/engagement/explain";
import { InfoTip } from "@/components/ui/info-tip";
import { ScoreRing, scoreFill } from "@/components/ui/score-ring";
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
            className={`h-3 w-[6px] rounded-[2px] ${i < value ? scoreFill((value / max) * 100) : "bg-paper-3"}`}
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
  info,
  alert = false,
}: {
  label: string;
  value: string;
  sub?: string;
  info?: React.ReactNode;
  /** Draws the card in the attention colour when the number is a problem. */
  alert?: boolean;
}) {
  return (
    <div
      className={`card relative overflow-hidden px-4 py-3.5 before:absolute before:inset-y-0 before:left-0 before:w-[3px] ${
        alert ? "before:bg-priority-critical" : "before:bg-kpmg-blue-light"
      }`}
    >
      <p className="flex items-center font-sans text-[10.5px] font-semibold tracking-[0.06em] text-muted uppercase">
        {label}
        {info}
      </p>
      <p
        className={`mt-0.5 font-display text-[28px] leading-tight font-semibold tabular-nums ${
          alert ? "text-priority-critical" : "text-ink"
        }`}
      >
        {value}
      </p>
      {sub && <p className="font-sans text-[11.5px] text-muted-2">{sub}</p>}
    </div>
  );
}

function Tip({
  label,
  title,
  children,
}: {
  label: string;
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <InfoTip label={label} title={title}>
      {children}
    </InfoTip>
  );
}

const INDEX_EXPLAIN: Record<EstateScorePayload["domain"], React.ReactNode> = {
  applications: <ApplicationsIndexExplain />,
  data_tech: <DataTechIndexExplain />,
  team_governance: <TeamIndexExplain />,
  strategy_projects: <StrategyIndexExplain />,
};

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
    <section className="card mb-8 grid overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]">
      <div className="border-b border-line bg-gradient-to-br from-kpmg-blue-tint-strong via-kpmg-blue-tint to-paper p-6 lg:border-r lg:border-b-0">
        <p className="flex items-center font-sans text-[11px] font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
          {indexLabel}
          <Tip label={indexLabel.toLowerCase()}>
            {INDEX_EXPLAIN[payload.domain]}
          </Tip>
        </p>
        {payload.index !== null && payload.band ? (
          <>
            <div className="mt-4 flex items-center gap-4">
              <ScoreRing
                value={payload.index}
                label={`${indexLabel} ${payload.index.toFixed(0)} of 100`}
              />
              <BandBadge
                band={payload.band}
                title={payload.band_meaning}
                label={payload.band_label}
              />
            </div>
            <p className="mt-4 font-sans text-[12.5px] leading-[1.5] text-muted">
              {payload.band_meaning}
            </p>
          </>
        ) : (
          <p className="mt-2 font-sans text-[14px] text-muted">
            Not enough evidence for an index yet.
          </p>
        )}
        <p className="mt-4 font-sans text-[11px] text-muted-2">
          Version {version} ·{" "}
          {payload.generator === "llm"
            ? "summary written by the model"
            : "rules summary"}
        </p>
      </div>
      <div className="p-6">
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

function Th({
  children,
  info,
}: {
  children: React.ReactNode;
  info?: React.ReactNode;
}) {
  return (
    <th className="px-4 py-2.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted">
      <span className="inline-flex items-center">
        {children}
        {info}
      </span>
    </th>
  );
}

/** Section scores as a row of small cards — shared by every questionnaire. */
function SectionCards({ sections }: { sections: SectionScore[] }) {
  if (sections.length === 0) return null;
  return (
    <div>
      <p className="mb-2 flex items-center font-mono text-[10.5px] uppercase tracking-wide text-muted">
        Sections
        <Tip label="section scores">
          <SectionsExplain />
        </Tip>
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {sections.map((s) => (
          <div key={s.key} className="card px-4 py-3.5">
            <p className="font-sans text-[10.5px] font-semibold tracking-[0.04em] text-muted uppercase">
              {s.label}
            </p>
            <p className="mt-0.5 flex items-baseline justify-between gap-2">
              <span className="font-display text-[26px] leading-tight font-semibold text-ink tabular-nums">
                {s.score !== null ? s.score.toFixed(0) : "—"}
              </span>
              <span className="rounded-full bg-paper-2 px-2 py-0.5 font-sans text-[10.5px] text-muted">
                weight {s.weight}
              </span>
            </p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-paper-3">
              <div
                className={`h-full origin-left animate-grow-x rounded-full ${scoreFill(s.score)}`}
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
        <Stat
          label="Business-critical"
          value={String(counts.critical)}
          sub="criticality 4 or 5"
          info={
            <Tip label="criticality" title="Criticality">
              <CriticalityExplain />
            </Tip>
          }
        />
        <Stat
          label="End of support ≤ 24 months"
          value={String(counts.end_of_life)}
          alert={counts.end_of_life > 0}
        />
        <Stat
          label="Critical and manual"
          value={String(counts.manual_critical)}
          alert={counts.manual_critical > 0}
          info={
            <Tip label="critical and manual" title="Critical and manual">
              <CriticalManualExplain />
            </Tip>
          }
        />
        <Stat
          label="AI level"
          value={payload.ai_index !== null ? payload.ai_index.toFixed(0) : "—"}
          sub="criticality-weighted, of 100"
          info={
            <Tip label="the AI level">
              <AiIndexExplain />
            </Tip>
          }
        />
      </div>
      <SectionCards sections={payload.portfolio} />
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse font-sans text-[13px]">
          <thead>
            <tr className="bg-paper-2 text-left">
              <Th>Application</Th>
              <Th
                info={
                  <Tip label="criticality" title="Criticality">
                    <CriticalityExplain />
                  </Tip>
                }
              >
                Criticality
              </Th>
              <Th
                info={
                  <Tip label="automation level" title="Automation level">
                    <AutomationLevelExplain />
                  </Tip>
                }
              >
                Automation
              </Th>
              <Th>AI</Th>
              <Th
                info={
                  <Tip label="inventory flags" title="What raises each flag">
                    <AppFlagsExplain />
                  </Tip>
                }
              >
                From the inventory
              </Th>
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
          info={
            <Tip
              label="the outsourced share"
              title="Outsourced or shared share"
            >
              <OutsourcedExplain />
            </Tip>
          }
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
          alert={people.sole_holders.length > 0}
          info={
            <Tip label="key-person dependency" title="Key-person dependency">
              <KeyPersonExplain />
            </Tip>
          }
        />
        <Stat
          label="Critical apps, one supporter"
          value={String(people.single_person_critical_apps.length)}
          alert={people.single_person_critical_apps.length > 0}
          info={
            <Tip label="key-person dependency" title="Key-person dependency">
              <KeyPersonExplain />
            </Tip>
          }
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
          info={
            <Tip
              label="the roadmap reconciliation"
              title="Roadmap against the change budget"
            >
              <ReconciliationExplain />
            </Tip>
          }
          label="Remaining commitment"
          value={money(portfolio.remaining_commitment)}
          sub="allocated, not yet spent"
        />
        <Stat
          alert={Boolean(portfolio.unfunded)}
          info={
            <Tip
              label="the roadmap reconciliation"
              title="Roadmap against the change budget"
            >
              <ReconciliationExplain />
            </Tip>
          }
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
          alert={portfolio.over_budget + portfolio.late > 0}
          info={
            <Tip label="project flags" title="What raises each project flag">
              <ProjectFlagsExplain />
            </Tip>
          }
          label="Over budget · late"
          value={`${portfolio.over_budget} · ${portfolio.late}`}
          sub={`${portfolio.stop_candidates} ${portfolio.stop_candidates === 1 ? "candidate" : "candidates"} to stop`}
        />
      </div>
      <SectionCards sections={payload.sections} />
      {payload.projects.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[900px] border-collapse font-sans text-[13px]">
            <thead>
              <tr className="bg-paper-2 text-left">
                <Th>Project</Th>
                <Th>Status</Th>
                <Th>Allocated</Th>
                <Th>Used</Th>
                <Th>Complete</Th>
                <Th
                  info={
                    <Tip label="deal relevance" title="Deal relevance (triage)">
                      <TriageExplain />
                    </Tip>
                  }
                >
                  Deal relevance
                </Th>
                <Th
                  info={
                    <Tip
                      label="project flags"
                      title="What raises each project flag"
                    >
                      <ProjectFlagsExplain />
                    </Tip>
                  }
                >
                  Observations
                </Th>
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

/** A 0-100 score as a short bar and a number, coloured on the band scale. */
function ScorePill({ value }: { value: number | null }) {
  return (
    <span className="inline-flex flex-none items-center gap-2">
      <span className="h-1.5 w-12 overflow-hidden rounded-full bg-paper-3">
        <span
          className={`block h-full rounded-full ${scoreFill(value)}`}
          style={{ width: `${value ?? 0}%` }}
        />
      </span>
      <span className="w-7 text-right font-display text-[14px] font-semibold text-text tabular-nums">
        {value ?? "—"}
      </span>
    </span>
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
          <p className="mb-2 flex items-center font-mono text-[10.5px] uppercase tracking-wide text-muted">
            Data domains
            <Tip label="a data-domain score" title="Data-domain score">
              <DomainScoreExplain />
            </Tip>
          </p>
          <ul className="card divide-y divide-line">
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
                <ScorePill value={d.score} />
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 flex items-center font-mono text-[10.5px] uppercase tracking-wide text-muted">
            Infrastructure platforms
            <Tip label="a platform score" title="Platform score">
              <PlatformScoreExplain />
            </Tip>
          </p>
          <ul className="card divide-y divide-line">
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
                <ScorePill value={p.score} />
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div>
        <p className="mb-2 flex items-center font-mono text-[10.5px] uppercase tracking-wide text-muted">
          Estate checks
          <Tip label="the estate checks" title="How the checks score">
            <ChecksExplain />
          </Tip>
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
