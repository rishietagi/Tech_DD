"use client";

import { useState } from "react";

import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";

/**
 * Add a request the generated list did not anticipate.
 *
 * Scope area and function are free text with a datalist of what the list already uses,
 * rather than a fixed dropdown: both are model-authored per engagement, so a closed list
 * would be wrong the moment a target needs a heading nobody anticipated. Suggesting the
 * existing values is what keeps them consistent without forcing them.
 */
export function IrlAddQuestion({
  scopeAreas,
  functions,
  onAdd,
}: {
  scopeAreas: string[];
  functions: string[];
  onAdd: (body: { question: string; function: string; scope_area?: string }) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [fn, setFn] = useState("");
  const [area, setArea] = useState("");
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setQuestion("");
    setFn("");
    setArea("");
    setOpen(false);
  };

  const submit = async () => {
    if (!question.trim() || !fn.trim()) return;
    setBusy(true);
    try {
      await onAdd({
        question: question.trim(),
        function: fn.trim(),
        scope_area: area.trim() || undefined,
      });
      reset();
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-4 rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] text-muted transition-colors hover:border-ink hover:text-text"
      >
        + Add a request
      </button>
    );
  }

  return (
    <div className="mt-4 rounded-2xl border border-line-strong bg-paper-2 p-5">
      <p className="mb-3 font-sans text-[11px] font-semibold tracking-[0.06em] text-muted uppercase">
        New request
      </p>

      <TextArea
        rows={2}
        value={question}
        placeholder="What should the target provide?"
        onChange={(event) => setQuestion(event.target.value)}
        aria-label="Request text"
      />

      <div className="mt-3 flex flex-wrap gap-4">
        <div>
          <label
            htmlFor="new-request-function"
            className="mb-1 block font-mono text-[10px] uppercase text-muted"
          >
            Function (required)
          </label>
          <TextInput
            id="new-request-function"
            list="irl-functions"
            value={fn}
            placeholder="e.g. Finance"
            onChange={(event) => setFn(event.target.value)}
            className="max-w-[220px]"
          />
          <datalist id="irl-functions">
            {functions.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
        </div>

        <div>
          <label
            htmlFor="new-request-area"
            className="mb-1 block font-mono text-[10px] uppercase text-muted"
          >
            Scope area (optional)
          </label>
          <TextInput
            id="new-request-area"
            list="irl-scope-areas"
            value={area}
            placeholder="Leave blank for Additional requests"
            onChange={(event) => setArea(event.target.value)}
            className="max-w-[280px]"
          />
          <datalist id="irl-scope-areas">
            {scopeAreas.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={() => void submit()}
          disabled={busy || !question.trim() || !fn.trim()}
          className="rounded-full bg-kpmg-blue px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink disabled:opacity-40"
        >
          {busy ? "Adding…" : "Add request"}
        </button>
        <button
          type="button"
          onClick={reset}
          className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] text-muted"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
