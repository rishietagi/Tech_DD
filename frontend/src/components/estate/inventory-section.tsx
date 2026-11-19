"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { InventoryEditor } from "@/components/estate/inventory-editor";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { inventoryApi } from "@/lib/api/estate";
import type {
  FieldValue,
  InventoryImportResult,
  InventoryItem,
  InventoryKind,
  InventoryRead,
} from "@/types/estate";
import { displayValue } from "@/types/estate";

/** The columns worth scanning down a table. Everything else is in the editor. */
const COLUMNS: Record<InventoryKind, string[]> = {
  application: [
    "vendor",
    "category",
    "processes",
    "hosting",
    "lifecycle",
    "contract_end",
  ],
  data_domain: ["sensitivity", "system_of_record", "business_owner", "regimes"],
  platform: ["vendor", "category", "location", "lifecycle", "apps_hosted"],
  it_role: [
    "designation",
    "function",
    "engagement",
    "key_skills",
    "length_of_service",
    "sole_holder",
  ],
  it_contract: [
    "counterparty",
    "type",
    "start_date",
    "end_date",
    "annual_value",
    "change_of_control",
  ],
  it_project: [
    "status",
    "planned_end",
    "allocated",
    "used",
    "pct_complete",
    "vendor",
  ],
  cyber_tool: ["available", "product", "managed_by", "coverage"],
};

const PILL =
  "rounded-full border border-line-strong px-3.5 py-2 font-sans text-[12.5px] font-medium transition-colors hover:bg-paper-2 disabled:opacity-50";

/** A value the table should draw attention to — unknowns and end-of-life. */
function isFlag(key: string, value: string): boolean {
  if (!value) return false;
  if (["vendor"].includes(key) && value.toUpperCase() === "TBD") return true;
  return /^(Unknown|End of life|Out of support)/.test(value);
}

function KindTable({
  engagementId,
  kind,
  data,
  onEdit,
  onAdd,
  onImported,
}: {
  engagementId: string;
  kind: InventoryKind;
  data: InventoryRead;
  onEdit: (item: InventoryItem) => void;
  onAdd: () => void;
  onImported: (result: InventoryImportResult) => void;
}) {
  const { show } = useToast();
  const definition = data.definitions[kind];
  const items = data.items.filter((i) => i.kind === kind);
  const labels = Object.fromEntries(
    definition.fields.map((f) => [f.key, f.label]),
  );
  const fileInput = useRef<HTMLInputElement | null>(null);

  const importMutation = useMutation({
    mutationFn: (file: File) =>
      inventoryApi.importTemplate(engagementId, kind, file),
    onSuccess: onImported,
    onError: (err: unknown) =>
      show(
        err instanceof ApiError ? err.message : "Could not read that workbook",
        "error",
      ),
  });

  return (
    <section className="mb-10">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-serif text-[22px] leading-tight text-ink">
            {definition.label}{" "}
            <span className="font-mono text-[13px] text-muted-2">
              {items.length}
            </span>
          </h3>
          <p className="mt-1 max-w-[80ch] font-sans text-[12.5px] text-muted">
            {definition.source}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <a
            href={inventoryApi.templateUrl(engagementId, kind)}
            download
            className={PILL}
          >
            Download template
          </a>
          <input
            ref={fileInput}
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) importMutation.mutate(file);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            className={PILL}
            disabled={importMutation.isPending}
            onClick={() => fileInput.current?.click()}
          >
            {importMutation.isPending ? "Reading…" : "Upload template"}
          </button>
          <button
            type="button"
            onClick={onAdd}
            className="rounded-full bg-ink px-3.5 py-2 font-sans text-[12.5px] font-medium text-paper-on-ink hover:bg-ink-2"
          >
            + Add
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line-strong bg-paper-2 px-6 py-8 text-center font-sans text-[13.5px] text-muted">
          Nothing recorded yet. Add one here, or send the template — it also
          travels as a sheet in the request-list workbook.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line-strong">
          <table className="w-full min-w-[860px] border-collapse font-sans text-[13px]">
            <thead>
              <tr className="bg-paper-2 text-left">
                <th className="w-[64px] px-4 py-2.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted">
                  ID
                </th>
                <th className="px-4 py-2.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted">
                  {labels.name}
                </th>
                {COLUMNS[kind].map((key) => (
                  <th
                    key={key}
                    className="px-4 py-2.5 font-mono text-[10.5px] font-medium uppercase tracking-wide text-muted"
                  >
                    {labels[key]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  tabIndex={0}
                  onClick={() => onEdit(item)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") onEdit(item);
                  }}
                  className="cursor-pointer border-t border-line align-top transition-colors hover:bg-kpmg-blue-tint focus:bg-kpmg-blue-tint focus:outline-none"
                >
                  <td className="px-4 py-3 font-mono text-[12px] font-semibold text-muted">
                    {item.ref}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-text">
                      {displayValue(item.fields.name)}
                    </div>
                    {item.fields.description && (
                      <div className="mt-0.5 line-clamp-1 text-[12px] text-muted">
                        {displayValue(item.fields.description)}
                      </div>
                    )}
                  </td>
                  {COLUMNS[kind].map((key) => {
                    const text = displayValue(
                      item.fields[key] as FieldValue | undefined,
                      key === "processes" ? data.processes : undefined,
                    );
                    return (
                      <td
                        key={key}
                        className={`px-4 py-3 ${isFlag(key, text) ? "font-medium text-priority-high" : "text-text"}`}
                      >
                        {text || <span className="text-muted-2">—</span>}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function ImportSummary({
  result,
  onDismiss,
}: {
  result: InventoryImportResult;
  onDismiss: () => void;
}) {
  const warnings = result.summaries.flatMap((s) =>
    s.warnings.map((w) => `${s.sheet}: ${w}`),
  );
  return (
    <div className="mb-6 rounded-xl border border-line-strong bg-paper-2 px-5 py-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          {result.summaries.length === 0 ? (
            <p className="font-sans text-[14px] text-text">
              {result.note || "Nothing was imported."}
            </p>
          ) : (
            <ul className="space-y-0.5 font-sans text-[14px] text-text">
              {result.summaries.map((s) => (
                <li key={s.kind}>
                  <span className="font-medium">{s.sheet}</span>: {s.created}{" "}
                  added, {s.updated} updated, {s.unchanged} unchanged
                </li>
              ))}
            </ul>
          )}
          {warnings.length > 0 && (
            <ul className="mt-2 max-w-[90ch] list-disc space-y-0.5 pl-5 font-sans text-[12px] text-muted">
              {warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="flex-none font-sans text-[12px] text-muted hover:text-text"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}

/**
 * The structured intakes on the request list (PHASE6_PLAN D2). The target supplies facts
 * here; the judgement on them happens in Assess.
 */
export function InventorySection({
  engagementId,
  kinds,
  intro,
}: {
  engagementId: string;
  kinds: InventoryKind[];
  intro: string;
}) {
  const queryClient = useQueryClient();
  const { show } = useToast();
  const [editing, setEditing] = useState<{
    kind: InventoryKind;
    item: InventoryItem | null;
  } | null>(null);
  const [imported, setImported] = useState<InventoryImportResult | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["inventory", engagementId],
    queryFn: () => inventoryApi.list(engagementId),
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["inventory", engagementId],
    });
    // Answers to a deleted item go with it, so the assessments must re-read.
    await queryClient.invalidateQueries({ queryKey: ["estate"] });
  };

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError || !data) {
    return (
      <ErrorState
        title="Couldn't load the inventory"
        action={
          <button type="button" onClick={() => void refetch()} className={PILL}>
            Try again
          </button>
        }
      />
    );
  }

  const applications = data.items.filter((i) => i.kind === "application");

  return (
    <div>
      <p className="mb-6 max-w-[80ch] font-sans text-[14px] leading-[1.6] text-muted">
        {intro}
      </p>
      {imported && (
        <ImportSummary result={imported} onDismiss={() => setImported(null)} />
      )}

      {kinds.map((kind) => (
        <KindTable
          key={kind}
          engagementId={engagementId}
          kind={kind}
          data={data}
          onEdit={(item) => setEditing({ kind, item })}
          onAdd={() => setEditing({ kind, item: null })}
          onImported={async (result) => {
            setImported(result);
            await refresh();
            const changed = result.summaries.reduce(
              (n, s) => n + s.created + s.updated,
              0,
            );
            show(
              changed > 0
                ? `${changed} row${changed === 1 ? "" : "s"} imported`
                : "Nothing changed",
              changed > 0 ? "neutral" : "error",
            );
          }}
        />
      ))}

      {editing && (
        <InventoryEditor
          kind={editing.kind}
          definition={data.definitions[editing.kind]}
          item={editing.item}
          processes={data.processes}
          applications={applications}
          onClose={() => setEditing(null)}
          onSave={async (fields) => {
            if (editing.item) {
              await inventoryApi.update(engagementId, editing.item.id, fields);
              show(`${editing.item.ref} saved`);
            } else {
              const created = await inventoryApi.create(
                engagementId,
                editing.kind,
                fields,
              );
              show(`${created.ref} added`);
            }
            await refresh();
          }}
          onDelete={
            editing.item
              ? async () => {
                  const item = editing.item;
                  if (!item) return;
                  await inventoryApi.remove(engagementId, item.id);
                  show(`${item.ref} deleted`);
                  await refresh();
                }
              : undefined
          }
        />
      )}
    </div>
  );
}
