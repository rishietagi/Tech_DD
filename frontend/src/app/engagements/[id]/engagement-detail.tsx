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
      <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-96 w-full" />
      </main>
    );
  }

  if (isError || !engagement) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState
          title="Couldn't load this engagement"
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
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
            {engagement.denorm?.company_name ?? "Target not yet named"}
          </div>
          <h1 className="font-display font-semibold text-3xl">{engagement.deal_name}</h1>
          <div className="mt-2 flex items-center gap-3">
            <EngagementStatusBadge status={engagement.status} />
            <span className="font-sans text-xs text-muted-2">
              Updated {new Date(engagement.updated_at).toLocaleString()}
            </span>
          </div>
        </div>
        {/* The modules this engagement contains. More will be added here as the
            project grows; each is its own route under /engagements/[id]. */}
        <div className="flex flex-none flex-wrap items-center gap-2">
          <Link
            href={`/engagements/${engagementId}/scope`}
            className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink transition-colors hover:border-kpmg-blue-dark hover:bg-kpmg-blue-dark"
          >
            Scope of work
          </Link>
          <Link
            href={`/engagements/${engagementId}/research`}
            className="rounded-full border border-line-strong px-5 py-3 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2"
          >
            Company research
          </Link>
          <Link
            href={`/engagements/${engagementId}/irl`}
            className="rounded-full border border-line-strong px-5 py-3 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2"
          >
            Request list
          </Link>
        </div>
      </div>

      <CoverSheet engagementId={engagementId} intake={engagement.intake} />
    </main>
  );
}
