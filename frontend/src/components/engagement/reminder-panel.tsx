"use client";

import { useState } from "react";

import type { ChecklistSummary } from "@/types/checklist";

/** Email reminders to the consultant — NOT CONNECTED.
 *
 * The preview counts are real, drawn from the live checklist, so the panel shows what a
 * reminder would actually say. The Send button is visibly disabled rather than wired to
 * a stub that pretends to work: a button that looks functional and silently does nothing
 * is worse in a demo than one that is honestly marked as pending.
 *
 * See docs/phases/PHASE4_PLAN.md for what wiring this involves.
 */
export function ReminderPanel({
  summary,
  companyName,
}: {
  summary: ChecklistSummary;
  companyName: string | null;
}) {
  const [recipient, setRecipient] = useState("");
  const outstanding = summary.not_received + summary.received_partially;

  return (
    <section className="mt-10 rounded-2xl border border-line-strong bg-paper-2 px-5 py-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-[15px] font-semibold text-text">
          Email reminder to the consultant
        </h2>
        <span className="rounded-full border border-line-strong bg-paper px-2.5 py-0.5 font-sans text-[11px] font-medium text-muted">
          Not connected yet
        </span>
      </div>

      <p className="mb-4 max-w-[72ch] font-sans text-[13px] leading-[1.55] text-muted">
        Once connected, this sends the outstanding items to the consultant on the
        engagement as a scheduled nudge. The preview below is built from the live
        checklist.
      </p>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="flex-1 basis-[280px]">
          <span className="mb-1 block font-sans text-[12px] font-medium text-muted">
            To
          </span>
          <input
            type="email"
            value={recipient}
            onChange={(event) => setRecipient(event.target.value)}
            placeholder="consultant@kpmg.com"
            className="w-full rounded-lg border border-line-strong bg-paper px-3 py-2 font-sans text-[13px] text-text placeholder:text-muted-2 focus:border-steel focus:outline-none"
          />
        </label>
        <button
          type="button"
          disabled
          title="Email delivery is wired at deployment"
          className="cursor-not-allowed rounded-full border border-line-strong bg-paper px-5 py-2 font-sans text-[13px] font-medium text-muted-2 opacity-70"
        >
          Send reminder
        </button>
      </div>

      <div className="rounded-xl border border-line bg-paper px-4 py-3">
        <p className="mb-2 font-sans text-[11px] font-semibold tracking-[0.06em] text-muted-2 uppercase">
          Preview
        </p>
        <p className="font-sans text-[13px] leading-[1.6] text-text">
          <span className="font-semibold">
            {companyName ?? "The target"} — {outstanding} outstanding request
            {outstanding === 1 ? "" : "s"}
          </span>
          <br />
          {summary.outstanding_critical} critical and {summary.outstanding_high} high
          priority still to arrive. {summary.received_completely} of {summary.total}{" "}
          received in full
          {summary.received_partially > 0 && `, ${summary.received_partially} partially`}.
        </p>
      </div>
    </section>
  );
}
