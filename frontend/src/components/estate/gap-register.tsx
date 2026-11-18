"use client";

import { useMemo, useState } from "react";

import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/text-area";
import type { Gap, GapEdit, Severity } from "@/types/estate";

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

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-0.5 font-sans text-[11px] font-semibold uppercase ${SEVERITY_CLASSES[severity]}`}
    >
      {severity}
    </span>
  );
}

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
  const [description, setDescription] = useState(gap.description);
  const [hypothesis, setHypothesis] = useState(gap.hypothesis);
  const [busy, setBusy] = useState(false);

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-line-strong bg-paper-2 p-4">
      <label className="block">
        <span className="mb-1 block font-mono text-[10px] uppercase tracking-wide text-muted">
          Severity
        </span>
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
        <span className="mb-1 block font-mono text-[10px] uppercase tracking-wide text-muted">
          Gap
        </span>
        <TextArea
          rows={3}
          className="!min-h-0 text-[14px]"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>
      <label className="block">
        <span className="mb-1 block font-mono text-[10px] uppercase tracking-wide text-muted">
          Target-state hypothesis
        </span>
        <TextArea
          rows={2}
          className="!min-h-0 text-[14px]"
          value={hypothesis}
          onChange={(e) => setHypothesis(e.target.value)}
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
              await onSave({ severity, description, hypothesis });
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
  onEdit,
  onRevert,
}: {
  gap: Gap;
  onEdit: (key: string, edit: GapEdit) => Promise<void>;
  onRevert: (key: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [open, setOpen] = useState(false);

  return (
    <li
      className={`rounded-2xl border border-line-strong border-l-4 bg-paper px-5 py-4 ${EDGE[gap.severity]}`}
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div>
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span className="font-mono text-[11px] font-semibold text-muted">
              {gap.display_id}
            </span>
            <SeverityBadge severity={gap.severity} />
            <span className="rounded-full bg-paper-2 px-2.5 py-0.5 font-sans text-[11px] text-muted">
              {gap.category}
            </span>
            {gap.scope === "portfolio" && (
              <span className="rounded-full bg-steel-tint px-2.5 py-0.5 font-sans text-[11px] text-steel">
                Portfolio
              </span>
            )}
            {gap.edited && (
              <span className="font-mono text-[10px] uppercase tracking-wide text-steel">
                Edited
              </span>
            )}
          </div>
          <h4 className="font-sans text-[15px] font-semibold leading-snug text-text">
            {gap.title}
          </h4>
          <p className="mt-1 font-sans text-[13.5px] leading-[1.55] text-text">
            {gap.description}
          </p>
          {gap.findings.length > 1 && (
            <button
              type="button"
              onClick={() => setOpen((o) => !o)}
              className="mt-2 font-sans text-[12px] text-steel underline-offset-2 hover:underline"
              aria-expanded={open}
            >
              {open ? "Hide" : "Show"} the {gap.findings.length} findings
            </button>
          )}
          {open && (
            <ul className="mt-2 list-disc space-y-0.5 pl-5 font-sans text-[12.5px] text-muted">
              {gap.findings.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          )}
        </div>
        <div className="border-line lg:border-l lg:pl-5">
          <p className="mb-1 font-mono text-[10px] uppercase tracking-wide text-muted">
            Target-state hypothesis
          </p>
          <p className="font-sans text-[13.5px] leading-[1.55] text-text">
            {gap.hypothesis}
          </p>
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

type ScopeFilter = "all" | "item" | "portfolio";

/** The gap register: one row per thing to fix, combining every finding about it. */
export function GapRegister({
  gaps,
  onEdit,
  onRevert,
}: {
  gaps: Gap[];
  onEdit: (key: string, edit: GapEdit) => Promise<void>;
  onRevert: (key: string) => Promise<void>;
}) {
  const [scope, setScope] = useState<ScopeFilter>("all");
  const [severity, setSeverity] = useState<Severity | "all">("all");
  const [category, setCategory] = useState("all");

  const categories = useMemo(
    () => Array.from(new Set(gaps.map((g) => g.category))).sort(),
    [gaps],
  );
  const shown = gaps.filter(
    (g) =>
      (scope === "all" || g.scope === scope) &&
      (severity === "all" || g.severity === severity) &&
      (category === "all" || g.category === category),
  );
  const counts = { High: 0, Medium: 0, Low: 0 } as Record<Severity, number>;
  for (const g of gaps) counts[g.severity] += 1;

  const chip = (active: boolean) =>
    `rounded-full border px-3 py-1.5 font-sans text-[12.5px] transition-colors ${
      active
        ? "border-ink bg-ink text-paper-on-ink"
        : "border-line-strong text-muted hover:text-text"
    }`;

  return (
    <section aria-label="Gap register">
      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
        {(["High", "Medium", "Low"] as Severity[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSeverity(severity === s ? "all" : s)}
            className={`rounded-xl border px-4 py-3 text-left transition-colors ${
              severity === s
                ? "border-ink bg-paper-2"
                : "border-line-strong hover:bg-paper-2"
            }`}
          >
            <p className="font-mono text-[10px] uppercase tracking-wide text-muted">
              {s} severity
            </p>
            <p className="font-serif text-[26px] leading-tight text-ink">
              {counts[s]}
            </p>
          </button>
        ))}
        <div className="rounded-xl border border-line-strong px-4 py-3">
          <p className="font-mono text-[10px] uppercase tracking-wide text-muted">
            Item gaps
          </p>
          <p className="font-serif text-[26px] leading-tight text-ink">
            {gaps.filter((g) => g.scope === "item").length}
          </p>
        </div>
        <div className="rounded-xl border border-line-strong px-4 py-3">
          <p className="font-mono text-[10px] uppercase tracking-wide text-muted">
            Portfolio gaps
          </p>
          <p className="font-serif text-[26px] leading-tight text-ink">
            {gaps.filter((g) => g.scope === "portfolio").length}
          </p>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {(["all", "item", "portfolio"] as ScopeFilter[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setScope(s)}
            className={chip(scope === s)}
          >
            {s === "all"
              ? "All"
              : s === "item"
                ? "Item gaps"
                : "Portfolio gaps"}
          </button>
        ))}
        <Select
          aria-label="Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="ml-1 max-w-[240px] py-1.5 text-[12.5px]"
          options={[
            { value: "all", label: "All categories" },
            ...categories.map((c) => ({ value: c, label: c })),
          ]}
        />
        <span className="ml-auto font-mono text-[11px] uppercase text-muted-2">
          {shown.length} of {gaps.length} gaps
        </span>
      </div>

      {gaps.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line-strong bg-paper-2 px-6 py-8 text-center font-sans text-[13.5px] text-muted">
          No gaps raised. Either the estate is sound or too little has been
          answered to tell — the coverage note above says which.
        </div>
      ) : shown.length === 0 ? (
        <p className="font-sans text-[13.5px] text-muted">
          No gaps match these filters.
        </p>
      ) : (
        <ul className="space-y-3">
          {shown.map((gap) => (
            <GapRow
              key={gap.key}
              gap={gap}
              onEdit={onEdit}
              onRevert={onRevert}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
