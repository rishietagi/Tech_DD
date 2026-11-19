"use client";

import { useState } from "react";

import {
  ImpactExplain,
  SeverityExplain,
  ThemesExplain,
} from "@/components/engagement/explain";
import { InfoTip } from "@/components/ui/info-tip";
import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import { IMPACT_LABELS } from "@/types/estate";
import type { Gap, GapEdit, Severity } from "@/types/estate";

const DOT: Record<Severity, string> = {
  High: "bg-priority-critical",
  Medium: "bg-priority-high",
  Low: "bg-muted-2",
};

/** Severity as a word with a small dot — colour carries meaning, never decoration. */
export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-sans text-[12px] font-semibold text-text">
      <span className={`h-2 w-2 rounded-full ${DOT[severity]}`} aria-hidden />
      {severity}
    </span>
  );
}

const LABEL = "mb-1 block font-sans text-[12px] font-medium text-muted";

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
    <div className="mt-4 space-y-3 rounded-lg border border-line bg-paper-2 p-4">
      <div className="grid gap-3 sm:grid-cols-[160px_minmax(0,1fr)]">
        <label className="block">
          <span className={LABEL}>Severity</span>
          <Select
            value={severity}
            onChange={(e) => setSeverity(e.target.value as Severity)}
            className="py-2 text-[13px]"
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
            className="py-2 text-[14px]"
          />
        </label>
      </div>
      <label className="block">
        <span className={LABEL}>Evidence — one point per line</span>
        <TextArea
          rows={3}
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
          className="rounded-full px-4 py-2 font-sans text-[13px] text-muted hover:text-text"
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
          className="rounded-full bg-ink px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink hover:bg-ink-2 disabled:opacity-50"
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
    <li className="px-5 py-4">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <SeverityBadge severity={gap.severity} />
        <span className="font-mono text-[11.5px] text-muted-2">
          {gap.display_id}
        </span>
        <span className="font-sans text-[12px] text-muted-2">{areaLabel}</span>
        {gap.edited && (
          <span className="font-sans text-[11.5px] text-steel">Edited</span>
        )}
        <span className="ml-auto flex gap-3">
          {!editing && (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="font-sans text-[12.5px] font-medium text-ink hover:underline"
            >
              Edit
            </button>
          )}
          {gap.edited && !editing && (
            <button
              type="button"
              onClick={() => void onRevert(gap.key)}
              className="font-sans text-[12.5px] text-muted hover:text-text"
            >
              Revert
            </button>
          )}
        </span>
      </div>
      <h4 className="mt-1.5 font-sans text-[15px] leading-snug font-semibold text-text">
        {gap.headline}
      </h4>
      <ul className="mt-1.5 list-disc space-y-0.5 pl-5 font-sans text-[13.5px] leading-[1.5] text-text">
        {gap.evidence.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <p className="mt-2 font-sans text-[13.5px] leading-[1.5] text-muted">
        <span className="font-medium text-text">Action: </span>
        {gap.action}
      </p>

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="mt-2 font-sans text-[12.5px] text-muted hover:text-text"
      >
        {open ? "Less" : "More"} ▸
      </button>
      {open && (
        <div className="mt-2 space-y-2 border-l-2 border-line pl-4 font-sans text-[13px] leading-[1.55] text-muted">
          <p>
            <span className="font-medium text-text">Why it matters: </span>
            {gap.implication}
          </p>
          {gap.impact.length > 0 && (
            <p className="flex flex-wrap items-center gap-x-1">
              <span className="font-medium text-text">Deal impact: </span>
              {gap.impact
                .map((lens) => IMPACT_LABELS[lens] ?? lens)
                .join(" · ")}
              <InfoTip label="the deal impact" title="Deal impact">
                <ImpactExplain />
              </InfoTip>
            </p>
          )}
          {gap.observations.length > 0 && (
            <div>
              <p className="font-medium text-text">What raised it</p>
              <ul className="mt-0.5 list-disc space-y-0.5 pl-5">
                {gap.observations.map((o) => (
                  <li key={`${o.source}-${o.text}`}>{o.text}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

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

/** Diligence-area labels for each finding (reference/report/report.yaml). */
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
 * The findings register, the same on every Assess tab: a heading with a severity filter
 * and an optional action (the export), then one row per finding. Every row is editable,
 * and the edit is what the export and the report carry.
 */
export function GapRegister({
  gaps,
  onEdit,
  onRevert,
  actions,
  empty = "No findings raised on what has been answered so far.",
}: {
  gaps: Gap[];
  onEdit: (key: string, edit: GapEdit) => Promise<void>;
  onRevert: (key: string) => Promise<void>;
  actions?: React.ReactNode;
  empty?: string;
}) {
  const [severity, setSeverity] = useState<Severity | "all">("all");
  const shown = gaps.filter(
    (g) => severity === "all" || g.severity === severity,
  );
  const counts = { High: 0, Medium: 0, Low: 0 } as Record<Severity, number>;
  for (const g of gaps) counts[g.severity] += 1;

  const filter = (value: Severity | "all", label: string, n: number) => (
    <button
      key={value}
      type="button"
      onClick={() => setSeverity(value)}
      aria-pressed={severity === value}
      className={`rounded-full px-3 py-1 font-sans text-[12.5px] transition-colors ${
        severity === value
          ? "bg-ink text-paper-on-ink"
          : "text-muted hover:text-text"
      }`}
    >
      {label} <span className="tabular-nums opacity-70">{n}</span>
    </button>
  );

  return (
    <section aria-label="Findings" className="mb-12">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 className="flex items-center font-display text-[20px] font-semibold text-ink">
          Findings
          <InfoTip label="findings" title="How findings are made">
            <ThemesExplain />
            <SeverityExplain />
          </InfoTip>
        </h3>
        <div className="flex flex-wrap items-center gap-2">
          {gaps.length > 0 && (
            <div
              className="flex gap-0.5"
              role="group"
              aria-label="Filter by severity"
            >
              {filter("all", "All", gaps.length)}
              {(["High", "Medium", "Low"] as Severity[]).map((s) =>
                filter(s, s, counts[s]),
              )}
            </div>
          )}
          {actions}
        </div>
      </div>

      {gaps.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line-strong px-5 py-6 font-sans text-[13.5px] text-muted">
          {empty}
        </p>
      ) : shown.length === 0 ? (
        <p className="font-sans text-[13.5px] text-muted">
          No findings at this severity.
        </p>
      ) : (
        <ul className="divide-y divide-line rounded-xl border border-line bg-paper">
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
