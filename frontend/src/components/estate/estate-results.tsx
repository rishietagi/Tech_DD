"use client";

import { BandBadge } from "@/components/engagement/band-badge";
import type {
  ApplicationResult,
  ApplicationsScorePayload,
  DataTechScorePayload,
  EstateScorePayload,
} from "@/types/estate";

const DISPOSITION_CLASSES: Record<string, string> = {
  Invest: "border-status-received bg-status-received-tint text-status-received",
  Retain: "border-steel bg-steel-tint text-steel",
  Modernise: "border-priority-high bg-priority-high-tint text-priority-high",
  Replace:
    "border-priority-critical bg-priority-critical-tint text-priority-critical",
  Consolidate:
    "border-priority-medium bg-priority-medium-tint text-priority-medium",
  "Not assessed": "border-line-strong bg-paper-2 text-muted-2",
};

export function DispositionBadge({ disposition }: { disposition: string }) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full border px-2.5 py-0.5 font-sans text-[11px] font-semibold uppercase ${
        DISPOSITION_CLASSES[disposition] ?? DISPOSITION_CLASSES["Not assessed"]
      }`}
    >
      {disposition}
    </span>
  );
}

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

/** Headline, written summary and pointers — the same for both assessments. */
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
              <BandBadge band={payload.band} title={payload.band_meaning} />
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

function healthFlags(
  app: ApplicationResult,
): { text: string; tone: "bad" | "warn" }[] {
  const flags: { text: string; tone: "bad" | "warn" }[] = [];
  if (app.debt_band === "High")
    flags.push({ text: `Debt ${app.debt}`, tone: "bad" });
  else if (app.debt_band === "Medium")
    flags.push({ text: `Debt ${app.debt}`, tone: "warn" });
  if (app.spof_status === "SPOF") flags.push({ text: "SPOF", tone: "bad" });
  else if (app.spof_status === "Check")
    flags.push({ text: "DR to confirm", tone: "warn" });
  if (app.scalability_status === "At risk")
    flags.push({ text: "Peak risk", tone: "bad" });
  else if (app.scalability_status === "Watch")
    flags.push({ text: "Peak watch", tone: "warn" });
  return flags;
}

export function ApplicationResults({
  payload,
}: {
  payload: ApplicationsScorePayload;
}) {
  const { counts } = payload;
  const order = [
    "Invest",
    "Retain",
    "Modernise",
    "Replace",
    "Consolidate",
    "Not assessed",
  ];
  return (
    <section className="mb-10">
      <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-5">
        <Stat
          label="Applications"
          value={String(counts.applications)}
          sub={`${counts.assessed} with a disposition`}
        />
        <Stat
          label="AI level"
          value={payload.ai_index !== null ? payload.ai_index.toFixed(0) : "—"}
          sub="criticality-weighted, of 100"
        />
        <Stat label="High technical debt" value={String(counts.high_debt)} />
        <Stat label="Single points of failure" value={String(counts.spof)} />
        <Stat label="At risk at peak" value={String(counts.scalability_risk)} />
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        {order
          .filter((d) => counts.by_disposition[d])
          .map((d) => (
            <span key={d} className="inline-flex items-center gap-2">
              <DispositionBadge disposition={d} />
              <span className="font-mono text-[12px] text-text">
                {counts.by_disposition[d]}
              </span>
            </span>
          ))}
      </div>

      <div className="overflow-x-auto rounded-2xl border border-line-strong">
        <table className="w-full min-w-[1000px] border-collapse font-sans text-[13px]">
          <thead>
            <tr className="bg-paper-2 text-left">
              {[
                "Application",
                "Disposition",
                "Business fit",
                "Technical fit",
                "Automation",
                "AI",
                "Technical health",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-2.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted"
                >
                  {h}
                </th>
              ))}
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
                <td className="max-w-[340px] px-4 py-3">
                  <DispositionBadge disposition={app.disposition} />
                  <p className="mt-1.5 text-[12px] leading-[1.5] text-muted">
                    {app.disposition_statement}
                  </p>
                </td>
                <td className="px-4 py-3 font-mono text-[12.5px]">
                  {app.business_fit?.toFixed(1) ?? "—"}
                </td>
                <td className="px-4 py-3 font-mono text-[12.5px]">
                  {app.technical_fit?.toFixed(1) ?? "—"}
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
                  <div className="flex flex-wrap gap-1.5">
                    {healthFlags(app).map((f) => (
                      <span
                        key={f.text}
                        className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                          f.tone === "bad"
                            ? "bg-priority-critical-tint text-priority-critical"
                            : "bg-priority-high-tint text-priority-high"
                        }`}
                      >
                        {f.text}
                      </span>
                    ))}
                    {healthFlags(app).length === 0 && (
                      <span className="text-[12px] text-muted-2">No flags</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
      <div>
        <p className="mb-2 font-mono text-[10.5px] uppercase tracking-wide text-muted">
          Sections
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {payload.sections.map((s) => (
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
            Platforms
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
              <p className="font-sans text-[12.5px] leading-[1.45] text-text">
                <span className="mr-1.5 font-mono text-[11px] text-muted">
                  {c.id}
                </span>
                {c.text}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
