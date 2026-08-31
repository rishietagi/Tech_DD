"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { EngagementStatusBadge } from "@/components/engagement/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { TextInput } from "@/components/ui/text-input";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { engagementsApi } from "@/lib/api/engagements";
import type { EngagementSummary } from "@/types/engagement";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "draft", label: "Draft" },
  { value: "filed", label: "Filed" },
  { value: "scoped", label: "Scoped" },
  { value: "archived", label: "Archived" },
];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function EngagementTable() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [pendingDelete, setPendingDelete] = useState<EngagementSummary | null>(null);
  const queryClient = useQueryClient();
  const { show } = useToast();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["engagements", { q, status }],
    queryFn: () => engagementsApi.list({ q: q || undefined, status_filter: status || undefined, limit: 100 }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => engagementsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["engagements"] });
      setPendingDelete(null);
      show("Engagement deleted");
    },
    onError: (error: unknown) => {
      setPendingDelete(null);
      show(error instanceof ApiError ? error.message : "Could not delete this engagement", "error");
    },
  });

  return (
    <div>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <TextInput
          placeholder="Search by deal name…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="sm:max-w-xs"
        />
        <Select
          options={STATUS_OPTIONS}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="sm:max-w-[200px]"
        />
      </div>

      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
        </div>
      )}

      {isError && (
        <ErrorState
          title="Couldn't load engagements"
          action={
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-full border border-line-strong px-5 py-2.5 font-sans text-[13px] font-medium"
            >
              Retry
            </button>
          }
        />
      )}

      {data && data.items.length === 0 && (
        <EmptyState title="No engagements match" description="Try a different search or filter, or start a new intake." />
      )}

      {data && data.items.length > 0 && (
        <div className="overflow-x-auto rounded-2xl border border-line-strong">
          <table className="w-full min-w-[720px] border-collapse">
            <thead>
              <tr className="border-b border-line-strong bg-paper-2 text-left">
                <th className="px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">Deal</th>
                <th className="px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">Target</th>
                <th className="px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">Structure</th>
                <th className="px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">DD Type</th>
                <th className="px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">Status</th>
                <th className="px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">Updated</th>
                <th className="px-4 py-3 text-right font-sans text-[11px] font-semibold text-muted uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((engagement) => (
                <tr key={engagement.id} className="border-b border-line last:border-b-0 hover:bg-paper-2">
                  <td className="px-4 py-3">
                    <Link href={`/engagements/${engagement.id}`} className="font-sans text-sm font-medium underline">
                      {engagement.deal_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-sans text-sm text-muted">
                    {engagement.denorm?.company_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 font-sans text-sm text-muted">
                    {engagement.denorm?.investment_type && engagement.denorm?.stake
                      ? `${engagement.denorm.investment_type} / ${engagement.denorm.stake}`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 font-sans text-xs font-medium text-muted uppercase">
                    {engagement.denorm?.dd_type ?? "Undetermined"}
                  </td>
                  <td className="px-4 py-3">
                    <EngagementStatusBadge status={engagement.status} />
                  </td>
                  <td className="px-4 py-3 font-sans text-xs text-muted-2">{formatDate(engagement.updated_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => setPendingDelete(engagement)}
                        className="rounded-full border border-line-strong px-3 py-1.5 font-sans text-[12px] font-medium text-redline transition-colors hover:border-redline hover:bg-redline-tint"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Deletion cannot be undone, so the dialog names the deal and says exactly what
          goes with it rather than asking a generic "are you sure?". */}
      {pendingDelete && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
          onClick={() => !deleteMutation.isPending && setPendingDelete(null)}
        >
          <div
            className="w-full max-w-[440px] rounded-2xl border border-line-strong bg-paper p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="delete-dialog-title" className="mb-2 font-display text-[17px] font-semibold text-text">
              Delete “{pendingDelete.deal_name}”?
            </h2>
            <p className="mb-5 font-sans text-[14px] leading-[1.55] text-muted">
              This permanently removes the engagement, its intake and every generated scope
              version from the database. It cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPendingDelete(null)}
                disabled={deleteMutation.isPending}
                className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => deleteMutation.mutate(pendingDelete.id)}
                disabled={deleteMutation.isPending}
                className="rounded-full bg-redline px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink transition-colors hover:bg-redline-dark disabled:opacity-50"
              >
                {deleteMutation.isPending ? "Deleting…" : "Delete permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
