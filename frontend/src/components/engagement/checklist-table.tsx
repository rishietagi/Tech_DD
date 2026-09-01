"use client";

import { useState } from "react";

import { PriorityBadge } from "@/components/engagement/priority-badge";
import type { ChecklistItem, DocumentStatus } from "@/types/checklist";
import { DOCUMENT_STATUSES, STATUS_LABELS } from "@/types/checklist";

const STATUS_CLASSES: Record<DocumentStatus, string> = {
  received_completely: "bg-status-received-tint text-status-received",
  received_partially: "bg-status-partial-tint text-status-partial",
  not_received: "bg-status-missing-tint text-status-missing",
};

/** One row. Holds the pending state for its own two editable fields, so a slow save on
 *  one request never blocks typing in another. */
function ChecklistRow({
  item,
  onUpdate,
}: {
  item: ChecklistItem;
  onUpdate: (
    questionId: string,
    patch: { status?: DocumentStatus; document_type?: string },
  ) => Promise<void>;
}) {
  const [status, setStatus] = useState<DocumentStatus>(item.status);
  const [docType, setDocType] = useState(item.document_type);
  const [saving, setSaving] = useState(false);

  const changeStatus = async (next: DocumentStatus) => {
    setStatus(next);
    setSaving(true);
    try {
      await onUpdate(item.question_id, { status: next });
    } finally {
      setSaving(false);
    }
  };

  const commitDocType = async () => {
    if (docType === item.document_type) return;
    setSaving(true);
    try {
      await onUpdate(item.question_id, { document_type: docType });
    } finally {
      setSaving(false);
    }
  };

  return (
    <tr className="border-b border-line last:border-b-0 align-top">
      <td className="px-4 py-3">
        <div className="mb-1 flex flex-wrap items-center gap-2">
          <PriorityBadge priority={item.priority} reason={item.priority_reason} />
          <span className="font-sans text-[11.5px] text-muted-2">{item.function}</span>
        </div>
        <p className="font-sans text-[14px] leading-[1.55] text-text">
          {item.document_requested}
        </p>
        {item.source_row_title && (
          <p className="mt-1 font-sans text-[11.5px] text-muted-2">
            From scope area: {item.source_row_title}
          </p>
        )}
      </td>

      <td className="px-4 py-3">
        <input
          value={docType}
          onChange={(event) => setDocType(event.target.value)}
          onBlur={commitDocType}
          aria-label="Document type"
          placeholder="e.g. Policy, Report…"
          className="w-full rounded-lg border border-line-strong bg-paper px-2.5 py-1.5 font-sans text-[13px] text-text placeholder:text-muted-2 focus:border-steel focus:outline-none"
        />
      </td>

      <td className="px-4 py-3">
        <select
          value={status}
          onChange={(event) => void changeStatus(event.target.value as DocumentStatus)}
          disabled={saving}
          aria-label="Status"
          className={`w-full rounded-lg border border-line-strong px-2.5 py-1.5 font-sans text-[13px] font-medium focus:border-steel focus:outline-none disabled:opacity-60 ${STATUS_CLASSES[status]}`}
        >
          {DOCUMENT_STATUSES.map((value) => (
            <option key={value} value={value}>
              {STATUS_LABELS[value]}
            </option>
          ))}
        </select>
        {item.matched_files.length > 0 && (
          <p className="mt-1 font-sans text-[11.5px] text-muted-2">
            Matched: {item.matched_files.join(", ")}
          </p>
        )}
      </td>
    </tr>
  );
}

export function ChecklistTable({
  items,
  onUpdate,
}: {
  items: ChecklistItem[];
  onUpdate: (
    questionId: string,
    patch: { status?: DocumentStatus; document_type?: string },
  ) => Promise<void>;
}) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-line-strong">
      <table className="w-full min-w-[960px] border-collapse">
        <thead>
          <tr className="border-b border-line-strong bg-paper-2 text-left">
            <th className="w-[54%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Documents requested
            </th>
            <th className="w-[20%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Document type
            </th>
            <th className="w-[26%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <ChecklistRow key={item.question_id} item={item} onUpdate={onUpdate} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
