"use client";

import { useState } from "react";

import { TextArea } from "@/components/ui/text-area";
import { ApiError } from "@/lib/api/client";
import { researchApi } from "@/lib/api/research";
import type { ResearchPayload, ResearchRead } from "@/types/research";
import { BRIEF_LABELS, BRIEF_ORDER } from "@/types/research";

/**
 * Write the research brief by hand, or correct what the model wrote.
 *
 * Research has no rules version — facts about a company cannot be derived — so with the AI
 * off (AI_MODE=off, the default) this is the only way to have a brief at all, and the brief
 * feeds both the request list and the report. Text a hand edit replaces is kept on the
 * server in `human_edits`.
 */
export function ResearchEditor({
  engagementId,
  research,
  onSaved,
  onCancel,
}: {
  engagementId: string;
  research: ResearchPayload | null;
  onSaved: (fresh: ResearchRead) => void;
  onCancel: () => void;
}) {
  const [summary, setSummary] = useState(research?.summary ?? "");
  const [brief, setBrief] = useState<Record<string, string>>(
    Object.fromEntries(
      BRIEF_ORDER.map((key) => [
        key,
        research?.business_brief?.[key]?.text ?? "",
      ]),
    ),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      onSaved(
        await researchApi.edit(engagementId, {
          summary,
          business_brief: brief,
        }),
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not save the brief",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mb-10 rounded-2xl border border-line-strong bg-paper-2 p-6">
      <h2 className="mb-1 font-display text-xl font-semibold text-text">
        {research ? "Edit the research brief" : "Write the research brief"}
      </h2>
      <p className="mb-5 max-w-[78ch] font-sans text-[13px] text-muted">
        Leave a section empty if nothing is known — an empty section is omitted,
        not padded. What is written here feeds the request list and the report.
      </p>
      <label className="mb-4 block">
        <span className="mb-1.5 block font-sans text-[13px] font-semibold text-text">
          Summary
        </span>
        <TextArea
          rows={3}
          className="!min-h-0"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
        />
      </label>
      <div className="grid gap-4 lg:grid-cols-2">
        {BRIEF_ORDER.map((key) => (
          <label key={key} className="block">
            <span className="mb-1.5 block font-sans text-[13px] font-semibold text-text">
              {BRIEF_LABELS[key]}
            </span>
            <TextArea
              rows={4}
              className="!min-h-0 text-[14px]"
              value={brief[key]}
              onChange={(e) =>
                setBrief((b) => ({ ...b, [key]: e.target.value }))
              }
            />
          </label>
        ))}
      </div>
      <div className="mt-5 flex items-center justify-end gap-3">
        {error && (
          <span className="font-sans text-[12.5px] text-redline">{error}</span>
        )}
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
          onClick={() => void save()}
          className="rounded-full bg-ink px-5 py-2 font-sans text-[13px] font-medium text-paper-on-ink hover:bg-ink-2 disabled:opacity-50"
        >
          {busy ? "Saving…" : "Save brief"}
        </button>
      </div>
    </section>
  );
}
