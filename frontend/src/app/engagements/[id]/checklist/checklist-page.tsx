"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { ReminderPanel } from "@/components/engagement/reminder-panel";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { checklistApi } from "@/lib/api/checklist";
import type { ChecklistRead } from "@/types/checklist";

export function ChecklistPage({ engagementId }: { engagementId: string }) {
  const queryClient = useQueryClient();
  const { show } = useToast();

  const {
    data: checklist,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["checklist", engagementId],
    queryFn: () => checklistApi.get(engagementId),
    // "No request list yet" is a meaningful state, not a failure.
    retry: false,
  });

  // Editing moved to the request list on 2026-09-02; this page only reads. The
  // `PATCH /checklist/{id}` endpoint is deliberately left in place — the shared-drive
  // scanner will write through it, and removing it would take the scanner's contract
  // with it.

  const scanMutation = useMutation({
    mutationFn: () => checklistApi.scan(engagementId),
    onSuccess: (fresh: ChecklistRead) => {
      queryClient.setQueryData(["checklist", engagementId], fresh);
      show("Checklist updated from the shared drive");
    },
    onError: (err: unknown) => {
      show(err instanceof ApiError ? err.message : "Could not scan the shared drive", "error");
    },
  });

  if (isLoading) {
    return (
      <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  const noIrlYet = isError && error instanceof ApiError && error.code === "no_irl";

  if (noIrlYet) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="Generate the request list first"
          description="The checklist tracks what has arrived against each request, so it needs a request list to track."
          action={
            <Link
              href={`/engagements/${engagementId}/irl`}
              className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink"
            >
              Go to the request list
            </Link>
          }
        />
      </main>
    );
  }

  if (isError || !checklist) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState title="Couldn't load the checklist" />
      </main>
    );
  }

  const { summary } = checklist;
  const received = summary.received_completely;
  const percent = summary.total ? Math.round((received / summary.total) * 100) : 0;

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      <div className="mb-6 flex items-center justify-between gap-4">
        <span className="font-sans text-[13px] text-muted">
          Tracking request list v{checklist.irl_version}
          {checklist.last_scanned_at &&
            ` · last scanned ${new Date(checklist.last_scanned_at).toLocaleString()}`}
        </span>
        <button
          type="button"
          onClick={() => scanMutation.mutate()}
          disabled={scanMutation.isPending}
          title="Walks the shared drive and updates statuses — wired at deployment"
          className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2 disabled:opacity-50"
        >
          {scanMutation.isPending ? "Scanning…" : "Scan shared drive"}
        </button>
      </div>

      <div className="mb-6">
        <p className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
          Document checklist
        </p>
        <h1 className="mb-4 font-display text-3xl font-semibold text-text">
          {checklist.company_name ?? "The target"}
        </h1>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 font-sans text-[13px] text-muted">
          <span>
            <span className="font-semibold text-text">
              {received} of {summary.total}
            </span>{" "}
            received in full ({percent}%)
          </span>
          {summary.received_partially > 0 && (
            <span>{summary.received_partially} partially received</span>
          )}
          <span>{summary.not_received} not yet received</span>
          {summary.outstanding_critical > 0 && (
            <span className="font-semibold text-priority-critical">
              {summary.outstanding_critical} critical outstanding
            </span>
          )}
        </div>
      </div>

      {/* Per-request tracking moved into the request list on 2026-09-02 (Rishi), so the
          analyst works one screen. This page kept the half that is genuinely a different
          job: chasing progress, not recording it. Two views of one dataset is fine; two
          places to *edit* it is how they drift. */}
      <div className="mb-8 rounded-2xl border border-line-strong bg-paper-2 px-6 py-5">
        <p className="mb-1 font-sans text-[14px] text-text">
          Documents are marked received on the request list itself.
        </p>
        <p className="max-w-[70ch] font-sans text-[13px] leading-relaxed text-muted">
          Each request there carries its status, document type and remarks beside the
          question, so what was asked and what arrived sit on one row. This page tracks
          overall progress and drafts the chaser.
        </p>
        <Link
          href={`/engagements/${engagementId}/irl`}
          className="mt-3 inline-block rounded-full border border-ink bg-ink px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink"
        >
          Open the request list
        </Link>
      </div>

      <ReminderPanel summary={summary} companyName={checklist.company_name} />
    </main>
  );
}
