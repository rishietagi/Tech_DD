"use client";

import { useState } from "react";

import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import { IMPACT_LABELS } from "@/types/estate";
import type { Gap, GapEdit, Severity } from "@/types/estate";
import {
  ImpactExplain,
  SeverityExplain,
} from "@/components/engagement/explain";
import { InfoTip } from "@/components/ui/info-tip";

const SEVERITY_CLASSES: Record<Severity, string> = {
  High: "border-priority-critical bg-priority-critical-tint text-priority-critical",
  Medium: "border-priority-high bg-priority-high-tint text-priority-high",
  Low: "border-priority-low bg-priority-low-tint text-priority-low",
};

const EDGE: Record<Severity, string> = {
  High: "border-l-priority-critical",
  Medium: "border-l-priority-high",
  Low: "border-l-priority-low",
};

const COUNT_EDGE: Record<Severity, string> = {
  High: "border-t-priority-critical",
  Medium: "border-t-priority-high",
  Low: "border-t-priority-low",
};

const COUNT_TEXT: Record<Severity, string> = {
  High: "text-priority-critical",
  Medium: "text-priority-high",
  Low: "text-priority-low",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-0.5 font-sans text-[11px] font-semibold uppercase ${SEVERITY_CLASSES[severity]}`}
    >
      {severity}
    </span>
  );
}

const LABEL =
  "mb-1 block font-mono text-[10px] uppercase tracking-wide text-muted";

function GapEditor({
  gap,
  onSave,
  onCancel,
}: {
  gap: Gap;
  onSave: (edit: GapEdit) => Promise<void>;
  onCancel: () => void;
}) {
  const [severity, setSeverity] = useState<Severity>(gap.severity);
  const [headline, setHeadline] = useState(gap.headline);
  const [evidence, setEvidence] = useState(gap.evidence.join("\n"));
  const [action, setAction] = useState(gap.action);
  const [busy, setBusy] = useState(false);

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-line-strong bg-paper-2 p-4">
      <label className="block">
        <span className={LABEL}>Severity</span>
        <Select
          value={severity}
          onChange={(e) => setSeverity(e.target.value as Severity)}
          className="max-w-[200px] py-2 text-[13px]"
          options={["High", "Medium", "Low"].map((s) => ({
            value: s,
            label: s,
          }))}
        />
      </label>
      <label className="block">
        <span className={LABEL}>Finding</span>
        <TextInput
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          className="text-[14px]"
        />
      </label>
      <label className="block">
        <span className={LABEL}>Evidence — one point per line</span>
        <TextArea
          rows={4}
          className="!min-h-0 text-[14px]"
          value={evidence}
          onChange={(e) => setEvidence(e.target.value)}
        />
      </label>
      <label className="block">
        <span className={LABEL}>Recommended action</span>
        <TextArea
          rows={2}
          className="!min-h-0 text-[14px]"
          value={action}
          onChange={(e) => setAction(e.target.value)}
        />
      </label>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-full px-4 py-2 font-sans text-[12.5px] text-muted hover:text-text"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await onSave({
                severity,
                headline,
                evidence: evidence.split("\n").filter((l) => l.trim()),
                action,
              });
            } finally {
              setBusy(false);
            }
          }}
          className="rounded-full bg-ink px-4 py-2 font-sans text-[12.5px] font-medium text-paper-on-ink hover:bg-ink-2 disabled:opacity-50"
        >
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}

function GapRow({
  gap,
  areaLabel,
  onEdit,
  onRevert,
}: {
  gap: Gap;
  areaLabel: string;
  onEdit: (key: string, edit: GapEdit) => Promise<void>;
  onRevert: (key: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [open, setOpen] = useState(false);

  return (
    <li
      className={`card border-l-4 px-5 py-4 transition-shadow hover:shadow-raised ${EDGE[gap.severity]}`}
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div>
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span className="font-mono text-[11px] font-semibold text-muted">
              {gap.display_id}
            </span>
            <SeverityBadge severity={gap.severity} />
            <span className="rounded-full bg-paper-2 px-2.5 py-0.5 font-sans text-[11px] text-muted">
              {areaLabel}
            </span>
            {gap.edited && (
              <span className="font-mono text-[10px] uppercase tracking-wide text-steel">
                Edited
              </span>
            )}
          </div>
          <h4 className="font-sans text-[15px] font-semibold leading-snug text-text">
            {gap.headline}
          </h4>
          <ul className="mt-1.5 list-disc space-y-1 pl-5 font-sans text-[13.5px] leading-[1.5] text-text">
            {gap.evidence.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <p className="mt-2 font-sans text-[13px] italic leading-[1.5] text-muted">
            {gap.implication}
          </p>
          {gap.observations.length > 0 && (
            <button
              type="button"
              onClick={() => setOpen((o) => !o)}
              className="mt-2 font-sans text-[12px] text-steel underline-offset-2 hover:underline"
              aria-expanded={open}
            >
              {open ? "Hide" : "Show"} what raised it ({gap.observations.length}
              )
            </button>
          )}
          {open && (
            <ul className="mt-2 space-y-1 font-sans text-[12.5px] text-muted">
              {gap.observations.map((o) => (
                <li key={`${o.source}-${o.text}`} className="flex gap-2">
                  <span className="shrink-0 font-mono text-[10.5px] uppercase text-muted-2">
                    {o.severity} · {o.source.replace(":", " ")}
                  </span>
                  <span>{o.text}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="border-line lg:border-l lg:pl-5">
          <p className="mb-1 font-mono text-[10px] uppercase tracking-wide text-muted">
            Recommended action
          </p>
          <p className="font-sans text-[13.5px] leading-[1.55] text-text">
            {gap.action}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            {gap.impact.map((lens) => (
              <span
                key={lens}
                className="rounded-full bg-steel-tint px-2.5 py-0.5 font-sans text-[11px] text-steel"
              >
                {IMPACT_LABELS[lens] ?? lens}
              </span>
            ))}
            {gap.impact.length > 0 && (
              <InfoTip label="the deal-impact lens" title="Deal-impact lens">
                <ImpactExplain />
              </InfoTip>
            )}
          </div>
          <div className="mt-3 flex gap-3">
            {!editing && (
              <button
                type="button"
                onClick={() => setEditing(true)}
                className="font-sans text-[12px] font-medium text-steel hover:underline"
              >
                Edit
              </button>
            )}
            {gap.edited && !editing && (
              <button
                type="button"
                onClick={() => void onRevert(gap.key)}
                className="font-sans text-[12px] text-muted hover:text-text"
              >
                Revert to generated
              </button>
            )}
          </div>
        </div>
      </div>
      {editing && (
        <GapEditor
          gap={gap}
          onCancel={() => setEditing(false)}
          onSave={async (edit) => {
            await onEdit(gap.key, edit);
            setEditing(false);
          }}
        />
      )}
    </li>
  );
}

/** Diligence-area labels for the badge on each finding (reference/report/report.yaml). */
const AREA_LABELS: Record<string, string> = {
  process_enablement: "Business process enablement",
  applications: "IT applications",
  infrastructure: "IT infrastructure",
  cyber: "Cyber security",
  data: "Data governance",
  organisation: "IT organisation",
  governance: "IT governance",
  strategy: "IT strategy",
  pmo: "Project delivery",
  budget: "IT budgeting",
  contracts: "IT contracts",
  engineering: "Engineering practice",
  ai: "AI",
};

/**
 * The register: one row per finding — a theme with its evidence, implication, deal
 * impact and action (Phase 8). The single observations that raised it sit underneath.
 */
export function GapRegister({
  gaps,
  onEdit,
  onRevert,
}: {
  gaps: Gap[];
  onEdit: (key: string, edit: GapEdit) => Promise<void>;
  onRevert: (key: string) => Promise<void>;
}) {
  const [severity, setSeverity] = useState<Severity | "all">("all");
  const shown = gaps.filter(
    (g) => severity === "all" || g.severity === severity,
  );
  const counts = { High: 0, Medium: 0, Low: 0 } as Record<Severity, number>;
  for (const g of gaps) counts[g.severity] += 1;

  return (
    <section aria-label="Findings">
      <p className="mb-2 flex items-center font-mono text-[10.5px] uppercase tracking-wide text-muted">
        By severity — click to filter
        <InfoTip label="severity" title="How severity is set">
          <SeverityExplain />
          <p>
            A theme takes the highest severity of the observations behind it.
            You can change it; the rules version is kept beside yours.
          </p>
        </InfoTip>
      </p>
      <div className="mb-4 grid grid-cols-3 gap-3">
        {(["High", "Medium", "Low"] as Severity[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSeverity(severity === s ? "all" : s)}
            aria-pressed={severity === s}
            className={`card border-t-[3px] px-4 py-3 text-left transition-all hover:-translate-y-px hover:shadow-raised ${COUNT_EDGE[s]} ${
              severity === s ? "ring-2 ring-kpmg-blue/30" : ""
            }`}
          >
            <p className="font-sans text-[10.5px] font-semibold tracking-[0.06em] text-muted uppercase">
              {s} severity
            </p>
            <p
              className={`font-display text-[28px] leading-tight font-semibold tabular-nums ${COUNT_TEXT[s]}`}
            >
              {counts[s]}
            </p>
          </button>
        ))}
      </div>

      {gaps.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line-strong bg-paper-2 px-6 py-8 text-center font-sans text-[13.5px] text-muted">
          No findings raised. Either the estate is sound or too little has been
          answered to tell — the coverage note above says which.
        </div>
      ) : shown.length === 0 ? (
        <p className="font-sans text-[13.5px] text-muted">
          No findings at this severity.
        </p>
      ) : (
        <ul className="space-y-3">
          {shown.map((gap) => (
            <GapRow
              key={gap.key}
              gap={gap}
              areaLabel={AREA_LABELS[gap.area] ?? gap.area}
              onEdit={onEdit}
              onRevert={onRevert}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
