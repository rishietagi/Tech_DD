"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";

import { SeverityBadge } from "@/components/estate/gap-register";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { TextArea } from "@/components/ui/text-area";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { itBudgetApi } from "@/lib/api/estate";
import type {
  BudgetLine,
  ItBudgetInputs,
  ItBudgetRead,
  LineKind,
} from "@/types/it-budget";
import { BudgetVarianceExplain } from "@/components/engagement/explain";
import { InfoTip } from "@/components/ui/info-tip";

const CELL =
  "w-full min-w-[84px] rounded-lg border border-line-strong bg-paper-2 px-2.5 py-1.5 text-right font-mono text-[13px] text-text focus:border-steel focus:bg-paper focus:outline-none";

function fmt(value: number | null, digits = 1): string {
  return value === null
    ? "—"
    : value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function pct(value: number | null): string {
  return value === null ? "—" : `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function NumberCell({
  value,
  label,
  onChange,
}: {
  value: number | null;
  label: string;
  onChange: (v: number | null) => void;
}) {
  const [text, setText] = useState(value === null ? "" : String(value));
  useEffect(() => setText(value === null ? "" : String(value)), [value]);
  return (
    <input
      inputMode="decimal"
      aria-label={label}
      className={CELL}
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={() => {
        const cleaned = text.replace(/,/g, "").trim();
        if (cleaned === "") return onChange(null);
        const n = Number(cleaned);
        if (Number.isFinite(n) && n >= 0) onChange(n);
        else setText(value === null ? "" : String(value));
      }}
    />
  );
}

function nextLineId(lines: BudgetLine[]): string {
  const n = lines.reduce(
    (max, l) => Math.max(max, Number(l.id.replace(/\D/g, "")) || 0),
    0,
  );
  return `L${String(n + 1).padStart(2, "0")}`;
}

/**
 * IT budget — the budgeting process and spend against budget, never a cost model.
 *
 * The 2026-09-14 boundary holds here in full: no share of revenue, no benchmark band, no
 * view of what technology "should" cost. The page reviews the target's figures against the
 * target's own budget, and how that budget is built, approved and controlled.
 *
 * Inputs are edited as one draft and saved together: the review recomputes from the whole
 * document, and a save per cell would recompute forty times while a year is typed in.
 */
export function ItBudgetPage({
  engagementId,
  embedded = false,
}: {
  engagementId: string;
  /** Inside the Assess page (Phase 8): no page header of its own. */
  embedded?: boolean;
}) {
  const queryClient = useQueryClient();
  const { show } = useToast();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["it-budget", engagementId],
    queryFn: () => itBudgetApi.get(engagementId),
  });
  const [draft, setDraft] = useState<ItBudgetInputs | null>(null);

  useEffect(() => {
    if (data && draft === null) setDraft(structuredClone(data.inputs));
  }, [data, draft]);

  const dirty = useMemo(
    () =>
      Boolean(
        data && draft && JSON.stringify(data.inputs) !== JSON.stringify(draft),
      ),
    [data, draft],
  );

  const saveMutation = useMutation({
    mutationFn: (inputs: ItBudgetInputs) =>
      itBudgetApi.save(engagementId, inputs),
    onSuccess: (fresh: ItBudgetRead) => {
      queryClient.setQueryData(["it-budget", engagementId], fresh);
      setDraft(structuredClone(fresh.inputs));
      show("IT budget saved");
    },
    onError: (err: unknown) => {
      const detail =
        err instanceof ApiError && err.fieldErrors.length > 0
          ? ` — ${err.fieldErrors[0].message}`
          : "";
      show(
        (err instanceof ApiError ? err.message : "Could not save") + detail,
        "error",
      );
    },
  });

  if (isLoading || (data && !draft)) {
    return (
      <div
        className={
          embedded ? "" : "mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24"
        }
      >
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (isError || !data || !draft) {
    return (
      <div
        className={embedded ? "" : "mx-auto w-full max-w-[720px] px-7 py-20"}
      >
        <ErrorState
          title="Couldn't load the IT budget"
          action={
            <button
              type="button"
              onClick={() => void refetch()}
              className="rounded-full border border-ink px-5 py-2.5 font-sans text-[13px] text-text"
            >
              Try again
            </button>
          }
        />
      </div>
    );
  }

  const update = (fn: (d: ItBudgetInputs) => void) =>
    setDraft((d) => {
      if (!d) return d;
      const next = structuredClone(d);
      fn(next);
      return next;
    });

  const { review } = data;
  const unit = [draft.currency, draft.unit].filter(Boolean).join(" ");

  return (
    <div
      className={
        embedded ? "" : "mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24"
      }
    >
      {!embedded && (
        <header className="mb-8 border-b border-line-strong pb-7">
          <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-muted">
            IT budget
          </p>
          <h1 className="mb-3 font-serif text-[34px] leading-tight text-ink">
            Budgeting process review
          </h1>
          <p className="max-w-[82ch] font-sans text-[15px] leading-relaxed text-muted">
            How the technology budget is built, approved and controlled, and
            where reported spend landed against it over the review period. This
            reviews the budgeting process — it does not build, validate or
            benchmark a cost model, and it shows no share of revenue.
          </p>
        </header>
      )}
      <FinancialsUpload
        engagementId={engagementId}
        onImported={() => {
          setDraft(null);
          void queryClient.invalidateQueries({
            queryKey: ["it-budget", engagementId],
          });
        }}
      />

      <div className="sticky top-0 z-10 -mx-7 mb-6 flex items-center justify-between gap-3 border-b border-line bg-paper/95 px-7 py-3 backdrop-blur">
        <span className="font-sans text-[13px] text-muted">
          {dirty
            ? "Unsaved changes — the review below reflects the last save."
            : data.saved
              ? "All changes saved."
              : "Not saved yet — defaults shown."}
        </span>
        <div className="flex gap-2">
          {dirty && (
            <button
              type="button"
              onClick={() => setDraft(structuredClone(data.inputs))}
              className="rounded-full px-4 py-2 font-sans text-[13px] text-muted hover:text-text"
            >
              Discard
            </button>
          )}
          <button
            type="button"
            disabled={!dirty || saveMutation.isPending}
            onClick={() => saveMutation.mutate(draft)}
            className="rounded-full bg-ink px-5 py-2 font-sans text-[13px] font-medium text-paper-on-ink hover:bg-ink-2 disabled:opacity-40"
          >
            {saveMutation.isPending ? "Saving…" : "Save and review"}
          </button>
        </div>
      </div>

      {/* ------------------------------------------------------------ figures */}
      <section className="mb-10">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="font-serif text-[24px] text-ink">
              Budget and actual, as reported
            </h2>
            <p className="font-sans text-[13px] text-muted">
              Three financial years is the house default. Relabel the years to
              match the accounts.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              aria-label="Currency"
              placeholder="Currency (e.g. GBP)"
              value={draft.currency}
              onChange={(e) =>
                update((d) => void (d.currency = e.target.value))
              }
              className="w-[150px] rounded-full border border-line-strong bg-paper-2 px-3.5 py-2 font-sans text-[12.5px]"
            />
            <input
              aria-label="Unit"
              placeholder="Unit (e.g. thousands)"
              value={draft.unit}
              onChange={(e) => update((d) => void (d.unit = e.target.value))}
              className="w-[170px] rounded-full border border-line-strong bg-paper-2 px-3.5 py-2 font-sans text-[12.5px]"
            />
            <button
              type="button"
              disabled={draft.years.length >= 10}
              onClick={() =>
                update((d) => {
                  const last = d.years.at(-1) ?? "FY";
                  const n = Number(last.replace(/\D/g, ""));
                  d.years.push(
                    n
                      ? last.replace(String(n), String(n + 1))
                      : `Year ${d.years.length + 1}`,
                  );
                  for (const line of d.lines) {
                    line.budget.push(null);
                    line.actual.push(null);
                  }
                })
              }
              className="rounded-full border border-line-strong px-3.5 py-2 font-sans text-[12.5px] font-medium hover:bg-paper-2 disabled:opacity-40"
            >
              + Year
            </button>
          </div>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-line-strong">
          <table className="w-full border-collapse font-sans text-[13px]">
            <thead>
              <tr className="bg-paper-2">
                <th
                  rowSpan={2}
                  className="min-w-[240px] px-4 py-2 text-left font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted"
                >
                  Line
                </th>
                <th
                  rowSpan={2}
                  className="px-3 py-2 text-left font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted"
                >
                  Run / change
                </th>
                {draft.years.map((year, i) => (
                  <th
                    key={i}
                    colSpan={2}
                    className="border-l border-line px-3 pt-2 pb-1"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <input
                        aria-label={`Year ${i + 1} label`}
                        value={year}
                        onChange={(e) =>
                          update((d) => void (d.years[i] = e.target.value))
                        }
                        className="w-[96px] rounded-md border border-transparent bg-transparent px-1.5 py-0.5 text-center font-mono text-[12px] font-semibold text-text hover:border-line-strong focus:border-steel focus:outline-none"
                      />
                      {draft.years.length > 1 && (
                        <button
                          type="button"
                          aria-label={`Remove ${year}`}
                          onClick={() =>
                            update((d) => {
                              d.years.splice(i, 1);
                              for (const line of d.lines) {
                                line.budget.splice(i, 1);
                                line.actual.splice(i, 1);
                              }
                            })
                          }
                          className="font-sans text-[12px] text-muted-2 hover:text-redline"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  </th>
                ))}
                <th rowSpan={2} />
              </tr>
              <tr className="bg-paper-2">
                {draft.years.map((_, i) => (
                  <th
                    key={i}
                    colSpan={2}
                    className="border-l border-line px-3 pb-2"
                  >
                    <div className="grid grid-cols-2 gap-2 font-mono text-[10px] font-medium uppercase text-muted">
                      <span className="text-right">Budget</span>
                      <span className="text-right">Actual</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {draft.lines.map((line, li) => (
                <tr key={line.id} className="border-t border-line">
                  <td className="px-4 py-2">
                    <input
                      aria-label="Line name"
                      value={line.name}
                      onChange={(e) =>
                        update((d) => void (d.lines[li].name = e.target.value))
                      }
                      className="w-full rounded-md border border-transparent bg-transparent px-1.5 py-1 font-sans text-[13.5px] font-medium text-text hover:border-line-strong focus:border-steel focus:outline-none"
                    />
                  </td>
                  <td className="px-3 py-2">
                    <select
                      aria-label="Run or change"
                      value={line.kind}
                      onChange={(e) =>
                        update(
                          (d) =>
                            void (d.lines[li].kind = e.target
                              .value as LineKind),
                        )
                      }
                      className="rounded-md border border-line-strong bg-paper-2 px-2 py-1 font-sans text-[12.5px]"
                    >
                      <option value="run">Run</option>
                      <option value="change">Change</option>
                    </select>
                  </td>
                  {draft.years.map((year, yi) => (
                    <td
                      key={yi}
                      colSpan={2}
                      className="border-l border-line px-3 py-2"
                    >
                      <div className="grid grid-cols-2 gap-2">
                        <NumberCell
                          label={`${line.name} ${year} budget`}
                          value={line.budget[yi] ?? null}
                          onChange={(v) =>
                            update((d) => void (d.lines[li].budget[yi] = v))
                          }
                        />
                        <NumberCell
                          label={`${line.name} ${year} actual`}
                          value={line.actual[yi] ?? null}
                          onChange={(v) =>
                            update((d) => void (d.lines[li].actual[yi] = v))
                          }
                        />
                      </div>
                    </td>
                  ))}
                  <td className="px-3 py-2 text-right">
                    <button
                      type="button"
                      aria-label={`Remove ${line.name}`}
                      onClick={() => update((d) => void d.lines.splice(li, 1))}
                      className="font-sans text-[12px] text-muted-2 hover:text-redline"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <button
          type="button"
          onClick={() =>
            update(
              (d) =>
                void d.lines.push({
                  id: nextLineId(d.lines),
                  name: "New line",
                  kind: "run",
                  budget: d.years.map(() => null),
                  actual: d.years.map(() => null),
                }),
            )
          }
          className="mt-3 rounded-full border border-line-strong px-3.5 py-2 font-sans text-[12.5px] font-medium hover:bg-paper-2"
        >
          + Line
        </button>
      </section>

      {/* ------------------------------------------------------------ process questions */}
      <section className="mb-10">
        <h2 className="mb-1 font-serif text-[24px] text-ink">
          How the budget is run
        </h2>
        <p className="mb-4 font-sans text-[13px] text-muted">
          Each weak answer raises a finding. None of them produce a score.
        </p>
        <div className="grid gap-3 lg:grid-cols-2">
          {data.questions.map((q) => {
            const answer = draft.answers[q.id] ?? { value: "", remarks: "" };
            const setAnswer = (patch: Partial<typeof answer>) =>
              update((d) => void (d.answers[q.id] = { ...answer, ...patch }));
            return (
              <div
                key={q.id}
                className="rounded-2xl border border-line-strong bg-paper px-5 py-4"
              >
                <p className="font-sans text-[15px] font-semibold text-text">
                  {q.text}
                </p>
                <div
                  role="radiogroup"
                  aria-label={q.text}
                  className="mt-3 grid gap-1.5"
                >
                  {q.options.map((option) => {
                    const selected = answer.value === option;
                    return (
                      <button
                        key={option}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        onClick={() =>
                          setAnswer({ value: selected ? "" : option })
                        }
                        className={`rounded-xl border px-3.5 py-2 text-left font-sans text-[13.5px] transition-colors ${
                          selected
                            ? "border-ink bg-kpmg-blue-tint font-medium text-text"
                            : "border-line-strong text-muted hover:bg-paper-2 hover:text-text"
                        }`}
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
                {answer.value && (
                  <TextArea
                    rows={2}
                    aria-label="Remarks"
                    placeholder="What management said, and what evidence supports it"
                    className="mt-3 !min-h-0 text-[13.5px]"
                    value={answer.remarks}
                    onChange={(e) => setAnswer({ remarks: e.target.value })}
                  />
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ------------------------------------------------------------ review */}
      <section>
        <h2 className="mb-1 flex items-center font-serif text-[24px] text-ink">
          Review
          <InfoTip label="the budget review" title="How the review flags spend">
            <BudgetVarianceExplain
              tolerance={review.tolerance_pct}
              movement={review.movement_pct}
            />
          </InfoTip>
        </h2>
        <p className="mb-4 font-sans text-[13px] text-muted">
          Variance beyond ±{review.tolerance_pct}% of budget, and year-on-year
          movement in actual spend beyond {review.movement_pct}%, are flagged
          for management to explain. The total variance compares only lines that
          carry a budget; spend with no budget is a finding of its own.
          {unit && ` Figures in ${unit}.`}
        </p>
        {review.coverage_note && (
          <p className="mb-4 rounded-lg bg-paper-2 px-3.5 py-2.5 font-sans text-[12.5px] text-muted">
            {review.coverage_note}
          </p>
        )}

        <div className="card mb-6 overflow-x-auto">
          <table className="w-full border-collapse font-sans text-[13px]">
            <thead>
              <tr className="bg-paper-2 text-right">
                {["Year", "Budget", "Actual", "Variance", "Run", "Change"].map(
                  (h, i) => (
                    <th
                      key={h}
                      className={`px-4 py-2.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted ${i === 0 ? "text-left" : ""}`}
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {review.totals.map((t) => (
                <tr
                  key={t.year}
                  className="border-t border-line text-right font-mono text-[13px]"
                >
                  <td className="px-4 py-2.5 text-left font-semibold">
                    {t.year}
                  </td>
                  <td className="px-4 py-2.5">{fmt(t.budget)}</td>
                  <td className="px-4 py-2.5">{fmt(t.actual)}</td>
                  <td
                    className={`px-4 py-2.5 ${
                      t.variance_pct !== null &&
                      Math.abs(t.variance_pct) > review.tolerance_pct
                        ? "font-semibold text-priority-critical"
                        : ""
                    }`}
                  >
                    {pct(t.variance_pct)}
                  </td>
                  <td className="px-4 py-2.5">
                    {t.run_share_pct === null ? "—" : `${t.run_share_pct}%`}
                  </td>
                  <td className="px-4 py-2.5">
                    {t.change_share_pct === null
                      ? "—"
                      : `${t.change_share_pct}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className="mb-3 font-sans text-[15px] font-semibold text-text">
          Findings{" "}
          <span className="font-mono text-[12px] text-muted-2">
            {review.findings.length}
          </span>
        </h3>
        {review.findings.length === 0 ? (
          <p className="font-sans text-[13.5px] text-muted">
            No findings on what has been entered so far.
          </p>
        ) : (
          <ul className="space-y-2">
            {review.findings.map((f, i) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-xl border border-line px-4 py-3"
              >
                <SeverityBadge severity={f.severity} />
                <span className="mt-0.5 rounded-full bg-paper-2 px-2 py-0.5 font-mono text-[10px] uppercase text-muted">
                  {f.source === "process"
                    ? "Process"
                    : f.source === "variance"
                      ? "Variance"
                      : f.source === "movement"
                        ? "Movement"
                        : "No budget"}
                </span>
                <p className="font-sans text-[13.5px] leading-[1.5] text-text">
                  {f.text}
                </p>
              </li>
            ))}
          </ul>
        )}

        <label className="mt-8 block">
          <span className="mb-1.5 block font-mono text-[10.5px] uppercase tracking-wide text-muted">
            Notes
          </span>
          <TextArea
            rows={3}
            className="!min-h-0 text-[14px]"
            placeholder="Source of the figures, adjustments made, what management said"
            value={draft.notes}
            onChange={(e) => update((d) => void (d.notes = e.target.value))}
          />
        </label>
      </section>
    </div>
  );
}

/**
 * The IT financials sheet: the target supplies its own budget and actuals (Phase 8).
 * The same sheet travels in the IRL workbook; an upload never clears a figure.
 */
function FinancialsUpload({
  engagementId,
  onImported,
}: {
  engagementId: string;
  onImported: () => void;
}) {
  const { show } = useToast();
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  return (
    <div className="mb-6 flex flex-wrap items-center gap-3 rounded-2xl border border-line-strong bg-paper-2 px-5 py-3.5">
      <p className="mr-auto max-w-[70ch] font-sans text-[13px] text-muted">
        The target can supply its budget and actual figures on the IT financials
        sheet — in the IRL workbook, or as its own template. An upload fills the
        figures below and never clears one.
      </p>
      <a
        href={itBudgetApi.templateUrl(engagementId)}
        className="rounded-full border border-line-strong px-3.5 py-2 font-sans text-[12.5px] font-medium hover:bg-paper"
      >
        Download template
      </a>
      <button
        type="button"
        disabled={busy}
        onClick={() => input.current?.click()}
        className="rounded-full border border-line-strong px-3.5 py-2 font-sans text-[12.5px] font-medium hover:bg-paper disabled:opacity-50"
      >
        {busy ? "Reading…" : "Upload financials"}
      </button>
      <input
        ref={input}
        type="file"
        accept=".xlsx"
        className="hidden"
        aria-label="Upload the IT financials sheet"
        onChange={async (e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          if (!file) return;
          setBusy(true);
          try {
            const result = await itBudgetApi.importFinancials(
              engagementId,
              file,
            );
            show(result.note);
            onImported();
          } catch (err) {
            show(
              err instanceof ApiError
                ? err.message
                : "Could not read that file",
              "error",
            );
          } finally {
            setBusy(false);
          }
        }}
      />
    </div>
  );
}
