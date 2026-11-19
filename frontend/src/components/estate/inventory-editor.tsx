"use client";

import { useEffect, useRef, useState } from "react";

import { Field } from "@/components/ui/field";
import { MultiSelect } from "@/components/ui/multi-select";
import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import { ApiError } from "@/lib/api/client";
import type {
  FieldDef,
  FieldValue,
  InventoryItem,
  InventoryKind,
  KindDef,
  ProcessRef,
} from "@/types/estate";

type Values = Record<string, FieldValue>;

function emptyFor(field: FieldDef): FieldValue {
  return ["multi_select", "process_list", "app_refs"].includes(field.type)
    ? []
    : "";
}

/**
 * Add or edit one inventory item. The form is generated from the YAML field definitions,
 * so a field a practitioner adds to `inventory.yaml` appears here without a code change.
 *
 * Only changed fields are sent on edit — the endpoint is partial, and resending every
 * field would overwrite a value someone else just imported.
 */
export function InventoryEditor({
  kind,
  definition,
  item,
  processes,
  applications,
  onClose,
  onSave,
  onDelete,
}: {
  kind: InventoryKind;
  definition: KindDef;
  item: InventoryItem | null;
  processes: ProcessRef[];
  applications: InventoryItem[];
  onClose: () => void;
  onSave: (fields: Values) => Promise<void>;
  onDelete?: () => Promise<void>;
}) {
  const initial: Values = Object.fromEntries(
    definition.fields.map((f) => [f.key, item?.fields[f.key] ?? emptyFor(f)]),
  );
  const [values, setValues] = useState<Values>(initial);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const dialog = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    dialog.current
      ?.querySelector<HTMLElement>("input, textarea, select")
      ?.focus();
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const set = (key: string, value: FieldValue) =>
    setValues((v) => ({ ...v, [key]: value }));

  const submit = async () => {
    const changed: Values = item
      ? Object.fromEntries(
          Object.entries(values).filter(
            ([k, v]) => JSON.stringify(v) !== JSON.stringify(initial[k]),
          ),
        )
      : Object.fromEntries(
          Object.entries(values).filter(([, v]) =>
            Array.isArray(v) ? v.length > 0 : v !== "",
          ),
        );
    if (item && Object.keys(changed).length === 0) {
      onClose();
      return;
    }
    setBusy(true);
    setErrors({});
    setFormError(null);
    try {
      await onSave(changed);
      onClose();
    } catch (err) {
      if (err instanceof ApiError && err.fieldErrors.length > 0) {
        setErrors(
          Object.fromEntries(err.fieldErrors.map((e) => [e.field, e.message])),
        );
      }
      setFormError(err instanceof ApiError ? err.message : "Could not save");
    } finally {
      setBusy(false);
    }
  };

  const renderField = (field: FieldDef, id: string) => {
    const value = values[field.key];
    const invalid = Boolean(errors[field.key]);
    switch (field.type) {
      case "long_text":
        return (
          <TextArea
            id={id}
            rows={2}
            invalid={invalid}
            className="!min-h-0 text-[14px]"
            value={value as string}
            onChange={(e) => set(field.key, e.target.value)}
          />
        );
      case "select":
        return (
          <Select
            id={id}
            invalid={invalid}
            className="py-2.5 text-[14px]"
            value={value as string}
            onChange={(e) => set(field.key, e.target.value)}
            options={[
              { value: "", label: "—" },
              ...field.options.map((o) => ({ value: o, label: o })),
            ]}
          />
        );
      case "multi_select":
        return (
          <MultiSelect
            name={field.label}
            value={value as string[]}
            onChange={(v) => set(field.key, v)}
            options={field.options.map((o) => ({ value: o, label: o }))}
          />
        );
      case "process_list":
        return (
          <MultiSelect
            name={field.label}
            value={value as string[]}
            onChange={(v) => set(field.key, v)}
            options={processes.map((p) => ({ value: p.key, label: p.name }))}
          />
        );
      case "app_refs":
        return applications.length === 0 ? (
          <p className="font-sans text-[13px] text-muted-2">
            No applications in the inventory yet.
          </p>
        ) : (
          <MultiSelect
            name={field.label}
            value={value as string[]}
            onChange={(v) => set(field.key, v)}
            options={applications.map((a) => ({
              value: a.ref,
              label: `${a.ref} ${String(a.fields.name ?? "")}`,
            }))}
          />
        );
      default:
        return (
          <TextInput
            id={id}
            invalid={invalid}
            className="py-2.5 text-[14px]"
            inputMode={field.type === "number" ? "decimal" : undefined}
            placeholder={
              field.type === "date"
                ? "YYYY-MM-DD"
                : field.type === "number"
                  ? "A figure, e.g. 120000"
                  : undefined
            }
            value={value as string}
            onChange={(e) => set(field.key, e.target.value)}
          />
        );
    }
  };

  const nounFor: Record<InventoryKind, string> = {
    application: "application",
    data_domain: "data domain",
    platform: "platform",
    it_role: "role",
    it_contract: "contract",
    it_project: "project",
    cyber_tool: "tool",
  };

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-ink/25"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-label={item ? `Edit ${item.ref}` : `Add ${nounFor[kind]}`}
        className="flex h-full w-full max-w-[620px] flex-col bg-paper shadow-2xl"
      >
        <header className="flex flex-none items-start justify-between gap-4 border-b border-line-strong px-7 py-5">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-wide text-muted">
              {definition.label}
            </p>
            <h2 className="font-serif text-[24px] leading-tight text-ink">
              {item
                ? `${item.ref} · ${String(item.fields.name ?? "")}`
                : `New ${nounFor[kind]}`}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full px-2 py-1 font-sans text-[13px] text-muted hover:text-text"
            aria-label="Close"
          >
            Close
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-7 py-6">
          {definition.fields.map((field) => (
            <Field
              key={field.key}
              label={field.label}
              required={field.required}
              hint={field.template_note || undefined}
              error={errors[field.key]}
            >
              {(id) => renderField(field, id)}
            </Field>
          ))}
        </div>

        <footer className="flex flex-none items-center justify-between gap-3 border-t border-line-strong px-7 py-4">
          <div>
            {item && onDelete && !confirmDelete && (
              <button
                type="button"
                onClick={() => setConfirmDelete(true)}
                className="font-sans text-[13px] text-redline hover:underline"
              >
                Delete
              </button>
            )}
            {confirmDelete && onDelete && (
              <span className="flex items-center gap-3 font-sans text-[13px]">
                <span className="text-text">
                  Delete {item?.ref} and its assessment answers?
                </span>
                <button
                  type="button"
                  onClick={async () => {
                    setBusy(true);
                    try {
                      await onDelete();
                      onClose();
                    } finally {
                      setBusy(false);
                    }
                  }}
                  className="font-semibold text-redline hover:underline"
                >
                  Delete
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmDelete(false)}
                  className="text-muted"
                >
                  Keep
                </button>
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {formError && (
              <span className="font-sans text-[12.5px] text-redline">
                {formError}
              </span>
            )}
            <button
              type="button"
              onClick={() => void submit()}
              disabled={busy}
              className="rounded-full bg-ink px-5 py-2.5 font-sans text-[13px] font-medium text-paper-on-ink hover:bg-ink-2 disabled:opacity-50"
            >
              {busy
                ? "Saving…"
                : item
                  ? "Save changes"
                  : `Add ${nounFor[kind]}`}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
