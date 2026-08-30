"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { EngagementStatusBadge } from "@/components/engagement/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { TextInput } from "@/components/ui/text-input";
import { engagementsApi } from "@/lib/api/engagements";

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

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["engagements", { q, status }],
    queryFn: () => engagementsApi.list({ q: q || undefined, status_filter: status || undefined, limit: 100 }),
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
