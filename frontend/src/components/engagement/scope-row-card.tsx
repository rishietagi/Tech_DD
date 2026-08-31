"use client";

import { useState } from "react";

import type { ScopedRow } from "@/types/engagement";

export function ScopeRowCard({ row }: { row: ScopedRow }) {
  const [open, setOpen] = useState(false);
  const isOutOfScope = row.tier === 0;

  return (
    <article
      className={`border-t border-line py-5 first:border-t-0 ${isOutOfScope ? "opacity-60" : ""}`}
    >
      {/* No tier badge (Rishi, 2026-08-31): depth is an internal decision, so it is not
          shown as a label on the row. It still governs which rows open and how deep, and
          the reasoning stays available under "Why this depth" below. */}
      <div className="mb-2">
        <h3 className="font-display text-[17px] font-semibold text-text">
          <span className="mr-2.5 font-sans text-[13px] font-medium text-muted-2">
            {String(row.sn).padStart(2, "0")}
          </span>
          {row.title}
        </h3>
      </div>

      {row.lines.map((line, index) => (
        <p key={index} className="mb-2 max-w-[70ch] font-sans text-[14.5px] leading-[1.6] text-text">
          {line.text}
        </p>
      ))}

      {row.out_of_scope_note && (
        <p className="mt-2 font-sans text-[13px] text-muted italic">{row.out_of_scope_note}</p>
      )}

      {row.edited_by_human && (
        <p className="mt-2 rounded-lg bg-steel-tint px-3 py-2 font-sans text-[12.5px] text-steel">
          Edited by hand
          {row.original_tier !== null && row.original_tier !== row.tier && (
            <> — the engine had this at Tier {row.original_tier}</>
          )}
          {row.override_reason && <>. {row.override_reason}</>}
        </p>
      )}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="mt-2.5 font-sans text-[12.5px] font-medium text-steel underline underline-offset-2"
      >
        {open ? "Hide detail" : "Evidence, depth and provenance"}
      </button>

      {open && (
        <div className="mt-3 grid grid-cols-1 gap-5 rounded-xl bg-paper-2 p-4 sm:grid-cols-2">
          <div>
            <h4 className="mb-1.5 font-sans text-[11px] font-semibold text-muted-2 uppercase">
              Evidence requested
            </h4>
            <ul className="list-disc space-y-1 pl-4 font-sans text-[13px] text-text">
              {row.evidence_requests.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <div>
              <h4 className="mb-1 font-sans text-[11px] font-semibold text-muted-2 uppercase">
                Why this depth
              </h4>
              <p className="font-sans text-[13px] text-text">{row.tier_reason}</p>
              {row.adjustments.length > 0 && (
                <ul className="mt-1 space-y-0.5">
                  {row.adjustments.map((adjustment) => (
                    <li key={adjustment} className="font-sans text-[12.5px] text-muted">
                      · {adjustment}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {row.triggered_by.length > 0 && (
              <div>
                <h4 className="mb-1 font-sans text-[11px] font-semibold text-muted-2 uppercase">
                  Triggered by
                </h4>
                <p className="font-sans text-[12.5px] text-muted">
                  {row.triggered_by.join(", ")}
                  {row.dd_master_ref && <span className="ml-2 italic">· {row.dd_master_ref}</span>}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
