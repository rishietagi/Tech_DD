"use client";

import { useState } from "react";

import type { IrlProgress } from "@/components/engagement/irl-summary-rail";

/** Email reminders to the consultant — NOT CONNECTED.
 *
 * The preview counts are real, drawn from the live request list, so the panel shows what
 * a reminder would actually say. The Send button is visibly disabled rather than wired to
 * a stub that pretends to work: a button that looks functional and silently does nothing
 * is worse in a demo than one that is honestly marked as pending.
 *
 * Collapsed by default since 2026-09-09, when it moved off the deleted checklist page.
 * It is a real planned feature, so deleting it would have quietly dropped one — but it
 * does not earn permanent space on the screen an analyst works in all day.
 *
 * See docs/phases/PHASE4_PLAN.md for what wiring this involves.
 */
export function ReminderPanel({
  progress,
  companyName,
}: {
  progress: IrlProgress;
  companyName: string | null;
}) {
  const [open, setOpen] = useState(false);
  const [recipient, setRecipient] = useState("");
  const outstanding = progress.notReceived + progress.receivedPartially;

  return (
    <section className="mt-8 overflow-hidden rounded-2xl border border-line-strong bg-paper-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-5 py-3.5 text-left transition-colors hover:bg-paper-3"
      >
        <span className="flex items-center gap-2.5">
          <span
            aria-hidden
            className={`font-mono text-[10px] text-muted-2 transition-transform ${open ? "rotate-90" : ""}`}
          >
            ▸
          </span>
          <span className="font-display text-[14.5px] font-semibold text-text">
            Email reminder to the consultant
          </span>
        </span>
        <span className="flex-none rounded-full border border-line-strong bg-paper px-2.5 py-0.5 font-mono text-[9.5px] tracking-wide text-muted uppercase">
          Not connected yet
        </span>
      </button>

      {open && (
        <div className="border-t border-line-strong px-5 py-4">
          <p className="mb-4 max-w-[72ch] font-sans text-[13px] leading-[1.55] text-muted">
            Once connected, this sends the outstanding items to the consultant on the
            engagement as a scheduled nudge. The preview below is built from the live
            request list.
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
            <p className="mb-2 font-mono text-[9.5px] font-semibold tracking-[0.08em] text-muted-2 uppercase">
              Preview
            </p>
            <p className="font-sans text-[13px] leading-[1.6] text-text">
              <span className="font-semibold">
                {companyName ?? "The target"} — {outstanding} outstanding request
                {outstanding === 1 ? "" : "s"}
              </span>
              <br />
              {progress.outstandingCritical} critical and {progress.outstandingHigh} high
              priority still to arrive. {progress.receivedCompletely} of {progress.total}{" "}
              received in full
              {progress.receivedPartially > 0 &&
                `, ${progress.receivedPartially} partially`}
              .
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
