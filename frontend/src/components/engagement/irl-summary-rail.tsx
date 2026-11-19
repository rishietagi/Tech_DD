"use client";

import type { IrlTracking } from "@/types/irl";

/**
 * The header of the request list: what this deal is, how far the collection has got, and
 * every action that operates on the whole list.
 *
 * It is sticky. The list runs to ninety-odd requests and the actions that matter most —
 * scanning the drive, exporting, uploading responses — were previously only reachable by
 * scrolling back to the top, which is exactly when an analyst is deepest in the list.
 *
 * Absorbed the old checklist page's progress block on 2026-09-09. Two views of one
 * dataset was defensible; two pages was not, once the scan started writing findings that
 * only the request list could show.
 */

export interface IrlProgress {
  total: number;
  documents: number;
  receivedCompletely: number;
  receivedPartially: number;
  notReceived: number;
  answered: number;
  followUps: number;
  outstandingCritical: number;
  outstandingHigh: number;
}

/** Counted from the tracking map rather than a second endpoint, so the numbers cannot
 *  disagree with the rows underneath them. */
export function summarise(
  tracking: Record<string, IrlTracking>,
  responses: Record<string, string>,
  kinds: Record<string, "document" | "question">,
): IrlProgress {
  const values = Object.entries(tracking);
  const outstanding = values.filter(([, t]) => t.status !== "received_completely");

  return {
    total: values.length,
    documents: Object.values(kinds).filter((k) => k === "document").length,
    receivedCompletely: values.filter(([, t]) => t.status === "received_completely").length,
    receivedPartially: values.filter(([, t]) => t.status === "received_partially").length,
    notReceived: values.filter(([, t]) => t.status === "not_received").length,
    answered: Object.values(responses).filter((v) => v.trim()).length,
    followUps: values.reduce((n, [, t]) => n + t.follow_up_questions.length, 0),
    outstandingCritical: outstanding.filter(([, t]) => t.priority === "critical").length,
    outstandingHigh: outstanding.filter(([, t]) => t.priority === "high").length,
  };
}

/** A single number with its label. The number carries the weight; the label explains it. */
function Stat({
  value,
  label,
  tone = "neutral",
}: {
  value: number | string;
  label: string;
  tone?: "neutral" | "received" | "partial" | "attention";
}) {
  const toneClass = {
    neutral: "text-text",
    received: "text-status-received",
    partial: "text-status-partial",
    attention: "text-redline",
  }[tone];

  return (
    <div className="flex flex-col gap-0.5">
      <span className={`font-display text-[22px] leading-none font-semibold ${toneClass}`}>
        {value}
      </span>
      <span className="font-sans text-[11.5px] leading-tight text-muted">{label}</span>
    </div>
  );
}

/** Collection progress as one bar: received, partial, outstanding.
 *
 *  A stacked bar rather than three numbers because the shape of the remainder is the
 *  thing being read — "mostly partial" and "mostly missing" are different problems. */
function ProgressBar({ progress }: { progress: IrlProgress }) {
  const total = progress.total || 1;
  const complete = (progress.receivedCompletely / total) * 100;
  const partial = (progress.receivedPartially / total) * 100;

  return (
    <div
      className="flex h-1.5 w-full overflow-hidden rounded-full bg-paper-3"
      role="img"
      aria-label={`${progress.receivedCompletely} of ${progress.total} received in full, ${progress.receivedPartially} partially`}
    >
      <div className="bg-status-received transition-all" style={{ width: `${complete}%` }} />
      <div className="bg-status-partial transition-all" style={{ width: `${partial}%` }} />
    </div>
  );
}

export function IrlSummaryRail({
  companyName,
  version,
  createdAt,
  sourceScopeVersion,
  lastScannedAt,
  progress,
  actions,
}: {
  companyName: string | null;
  version: number;
  createdAt: string;
  sourceScopeVersion: number | null;
  lastScannedAt: string | null;
  progress: IrlProgress;
  actions: React.ReactNode;
}) {
  const percent = progress.total
    ? Math.round((progress.receivedCompletely / progress.total) * 100)
    : 0;

  return (
    <div className="sticky top-0 z-20 -mx-7 mb-7 border-b border-line-strong bg-paper/95 px-7 pt-8 pb-5 backdrop-blur-sm">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-x-6 gap-y-4">
        <div className="min-w-0">
          <p className="mb-1 font-sans text-[11px] font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
            Information requests
          </p>
          <h1 className="font-display text-[28px] leading-tight font-semibold text-text">
            {companyName ?? "The target"}
          </h1>
          <p className="mt-1 font-mono text-[11px] text-muted-2">
            v{version} · {new Date(createdAt).toLocaleDateString()}
            {sourceScopeVersion != null && ` · from scope v${sourceScopeVersion}`}
            {lastScannedAt &&
              ` · drive scanned ${new Date(lastScannedAt).toLocaleString(undefined, {
                day: "numeric",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
              })}`}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">{actions}</div>
      </div>

      <div className="flex flex-wrap items-end gap-x-8 gap-y-3">
        <Stat value={`${percent}%`} label="collected" tone="received" />
        <Stat value={progress.receivedCompletely} label="received in full" tone="received" />
        {progress.receivedPartially > 0 && (
          <Stat value={progress.receivedPartially} label="partial" tone="partial" />
        )}
        <Stat value={progress.notReceived} label="outstanding" />
        <Stat value={progress.answered} label="answered" />
        {progress.followUps > 0 && (
          <Stat value={progress.followUps} label="follow-ups to send" tone="attention" />
        )}
        {progress.outstandingCritical > 0 && (
          <Stat
            value={progress.outstandingCritical}
            label="critical outstanding"
            tone="attention"
          />
        )}
      </div>

      <div className="mt-4">
        <ProgressBar progress={progress} />
      </div>
    </div>
  );
}
