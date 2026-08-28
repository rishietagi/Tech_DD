"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { CoverSheet } from "@/components/intake/cover-sheet";
import { EngagementStatusBadge } from "@/components/engagement/status-badge";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { engagementsApi } from "@/lib/api/engagements";

export function EngagementDetail({ engagementId }: { engagementId: string }) {
  const { data: engagement, isLoading, isError, refetch } = useQuery({
    queryKey: ["engagement", engagementId],
    queryFn: () => engagementsApi.get(engagementId),
  });

  if (isLoading) {
    return (
      <main className="mx-auto max-w-[1120px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-96 w-full" />
      </main>
    );
  }

  if (isError || !engagement) {
    return (
      <main className="mx-auto max-w-[720px] px-7 py-20">
        <ErrorState
          title="Couldn't load this engagement"
          action={
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-[3px] border border-line-strong px-5 py-2.5 font-mono text-xs uppercase"
            >
              Retry
            </button>
          }
        />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-[1120px] px-7 pt-12 pb-24">
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1 font-mono text-xs tracking-[0.16em] text-redline uppercase">
            {engagement.denorm?.company_name ?? "Target not yet named"}
          </div>
          <h1 className="font-serif text-3xl font-medium">{engagement.deal_name}</h1>
          <div className="mt-2 flex items-center gap-3">
            <EngagementStatusBadge status={engagement.status} />
            <span className="font-mono text-xs text-muted-2">
              Updated {new Date(engagement.updated_at).toLocaleString()}
            </span>
          </div>
        </div>
        <Link
          href={`/engagements/${engagementId}/scope`}
          className="rounded-[3px] border border-ink bg-ink px-5 py-3 font-mono text-xs tracking-[0.08em] text-paper-on-ink uppercase transition-colors hover:border-redline-dark hover:bg-redline-dark"
        >
          View scope of work
        </Link>
      </div>

      <CoverSheet engagementId={engagementId} intake={engagement.intake} />
    </main>
  );
}
