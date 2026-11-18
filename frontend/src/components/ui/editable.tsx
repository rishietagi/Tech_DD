"use client";

import { useEffect, useRef, useState } from "react";

import { TextArea } from "@/components/ui/text-area";

/**
 * Edit-in-place primitives. Everything the app exports is editable before export
 * (Rishi, 2026-11-18), so these sit on every client-facing text block — the scope deck and
 * the report. The view renders exactly what exports; Edit swaps it for a field.
 */

function Controls({
  editing,
  busy,
  edited,
  onEdit,
  onSave,
  onCancel,
  onRevert,
  label,
}: {
  editing: boolean;
  busy: boolean;
  edited?: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onRevert?: () => void;
  label: string;
}) {
  if (editing) {
    return (
      <div className="mt-2 flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-full px-3 py-1.5 font-sans text-[12px] text-muted hover:text-text"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onSave}
          className="rounded-full bg-ink px-3.5 py-1.5 font-sans text-[12px] font-medium text-paper-on-ink hover:bg-ink-2 disabled:opacity-50"
        >
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
    );
  }
  return (
    <span className="ml-2 inline-flex items-center gap-2 align-middle opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
      <button
        type="button"
        onClick={onEdit}
        aria-label={`Edit ${label}`}
        className="font-sans text-[11.5px] font-medium text-steel hover:underline"
      >
        Edit
      </button>
      {edited && onRevert && (
        <button
          type="button"
          onClick={onRevert}
          className="font-sans text-[11.5px] text-muted hover:text-text"
        >
          Revert
        </button>
      )}
    </span>
  );
}

function EditedTag({ edited }: { edited?: boolean }) {
  if (!edited) return null;
  return (
    <span className="ml-2 align-middle font-mono text-[9.5px] tracking-wide text-steel uppercase">
      Edited
    </span>
  );
}

export function EditableText({
  value,
  onSave,
  onRevert,
  edited,
  label,
  rows = 3,
  children,
}: {
  value: string;
  onSave: (value: string) => Promise<void>;
  onRevert?: () => Promise<void>;
  edited?: boolean;
  label: string;
  rows?: number;
  children: React.ReactNode;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const [busy, setBusy] = useState(false);
  const field = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!editing) setDraft(value);
  }, [value, editing]);
  useEffect(() => {
    if (editing) field.current?.focus();
  }, [editing]);

  const save = async () => {
    setBusy(true);
    try {
      await onSave(draft);
      setEditing(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="group">
      {editing ? (
        <TextArea
          ref={field}
          rows={rows}
          aria-label={label}
          className="!min-h-0 text-[14px]"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setEditing(false);
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void save();
          }}
        />
      ) : (
        <div>
          {children}
          <EditedTag edited={edited} />
          <Controls
            editing={false}
            busy={busy}
            edited={edited}
            label={label}
            onEdit={() => setEditing(true)}
            onSave={() => void save()}
            onCancel={() => setEditing(false)}
            onRevert={onRevert ? () => void onRevert() : undefined}
          />
        </div>
      )}
      {editing && (
        <Controls
          editing
          busy={busy}
          label={label}
          onEdit={() => undefined}
          onSave={() => void save()}
          onCancel={() => setEditing(false)}
        />
      )}
    </div>
  );
}

/** A list edited as text, one item per line. Blank lines are dropped on save. */
export function EditableList({
  items,
  onSave,
  onRevert,
  edited,
  label,
  children,
}: {
  items: string[];
  onSave: (items: string[]) => Promise<void>;
  onRevert?: () => Promise<void>;
  edited?: boolean;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <EditableText
      value={items.join("\n")}
      rows={Math.min(Math.max(items.length + 1, 3), 14)}
      label={`${label} (one per line)`}
      edited={edited}
      onRevert={onRevert}
      onSave={(text) =>
        onSave(
          text
            .split("\n")
            .map((line) => line.replace(/^\s*[•\-*]\s*/, "").trim())
            .filter(Boolean),
        )
      }
    >
      {children}
    </EditableText>
  );
}
