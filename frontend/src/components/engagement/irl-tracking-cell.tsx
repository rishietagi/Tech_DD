"use client";

import { useEffect, useRef, useState } from "react";

import { TextArea } from "@/components/ui/text-area";
import type { IrlTracking, RequestKind } from "@/types/irl";

/**
 * What the deal team observes about one request's document: has it arrived, what kind of
 * artefact is it, and any remarks.
 *
 * Rendered inside the IRL from 2026-09-02 so the analyst does not work two screens. None
 * of this is exported to the client workbook — it is the team's own assessment of what
 * has arrived, and of the target's responsiveness.
 */

/** The same three states, named for what is actually being tracked.
 *
 *  "Received completely" against a question the client answered in prose is nonsense, and
 *  a consultant reading the column would not trust either label. The stored values are
 *  identical — only the wording changes — so the checklist, the summary counts and the
 *  scanner all keep working off one set of states. */
const STATUS_OPTIONS: Record<RequestKind, { value: IrlTracking["status"]; label: string }[]> = {
  document: [
    { value: "not_received", label: "Not yet received" },
    { value: "received_partially", label: "Received partially" },
    { value: "received_completely", label: "Received completely" },
  ],
  question: [
    { value: "not_received", label: "Not yet answered" },
    { value: "received_partially", label: "Partially answered" },
    { value: "received_completely", label: "Answered" },
  ],
};

const STATUS_CLASSES: Record<IrlTracking["status"], string> = {
  not_received: "border-status-missing text-status-missing bg-paper",
  received_partially: "border-status-partial text-status-partial bg-status-partial-tint",
  received_completely: "border-status-received text-status-received bg-status-received-tint",
};

/** Remarks autosave on a debounce, the same way responses already do. */
const SAVE_DEBOUNCE_MS = 700;

export function IrlTrackingCell({
  tracking,
  kind,
  onSave,
}: {
  tracking: IrlTracking;
  kind: RequestKind;
  onSave: (patch: {
    status?: IrlTracking["status"];
    document_type?: string;
    remarks?: string;
  }) => Promise<void>;
}) {
  const [remarks, setRemarks] = useState(tracking.remarks);
  const [docType, setDocType] = useState(tracking.document_type);
  const [saving, setSaving] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Last value we know the server holds, so a re-render from the whole-list response
  // cannot overwrite what is being typed.
  const committed = useRef({ remarks: tracking.remarks, docType: tracking.document_type });

  useEffect(() => {
    if (tracking.remarks !== committed.current.remarks) {
      committed.current.remarks = tracking.remarks;
      setRemarks(tracking.remarks);
    }
    if (tracking.document_type !== committed.current.docType) {
      committed.current.docType = tracking.document_type;
      setDocType(tracking.document_type);
    }
  }, [tracking.remarks, tracking.document_type]);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const debouncedSave = (patch: { document_type?: string; remarks?: string }) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setSaving(true);
      try {
        await onSave(patch);
        if (patch.remarks !== undefined) committed.current.remarks = patch.remarks;
        if (patch.document_type !== undefined) committed.current.docType = patch.document_type;
      } finally {
        setSaving(false);
      }
    }, SAVE_DEBOUNCE_MS);
  };

  return (
    <div className="space-y-2">
      <select
        value={tracking.status}
        onChange={(event) =>
          void onSave({ status: event.target.value as IrlTracking["status"] })
        }
        aria-label={kind === "question" ? "Answer status" : "Document status"}
        className={`w-full rounded-lg border px-2.5 py-1.5 font-sans text-[12.5px] font-medium transition-colors focus:border-steel focus:outline-none ${STATUS_CLASSES[tracking.status]}`}
      >
        {STATUS_OPTIONS[kind].map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {/* A question has no artefact to classify, so the type field would only ever be
          filled in by mistake. */}
      {kind === "document" && (
      <input
        type="text"
        value={docType}
        placeholder="Document type"
        aria-label="Document type"
        onChange={(event) => {
          setDocType(event.target.value);
          debouncedSave({ document_type: event.target.value });
        }}
        className="w-full rounded-lg border border-line-strong bg-paper-2 px-2.5 py-1.5 font-sans text-[12.5px] text-text focus:border-steel focus:bg-paper focus:outline-none"
      />
      )}

      <TextArea
        rows={2}
        value={remarks}
        placeholder={
          kind === "question"
            ? "Remarks — what was said, what is still unclear"
            : "Remarks — what arrived, what is missing"
        }
        aria-label="Remarks"
        className="min-h-0 text-[12.5px]"
        onChange={(event) => {
          setRemarks(event.target.value);
          debouncedSave({ remarks: event.target.value });
        }}
      />

      {saving && (
        <span role="status" className="font-mono text-[10px] uppercase text-muted-2">
          Saving…
        </span>
      )}
    </div>
  );
}
