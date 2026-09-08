"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { BandBadge } from "@/components/engagement/band-badge";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { assessApi } from "@/lib/api/assess";
import type { ProcessSummary } from "@/types/assess";

function ProcessCard({
  engagementId,
  process,
}: {
  engagementId: string;
  process: ProcessSummary;
}) {
  const progress =
    process.question_count > 0
      ? Math.round((process.answered_count / process.question_count) * 100)
      : 0;

  // A process with no questionnaire is shown, not hidden — the shape of the module
  // should be visible — but it is plainly not a link and says why.
  if (!process.defined) {
    return (
      <div className="rounded-2xl border border-dashed border-line-strong bg-paper-2 p-6">
        <div className="mb-2 flex items-baseline gap-3">
          <span className="font-mono text-[12px] text-muted-2">{process.short_name}</span>
          <h2 className="font-serif text-[20px] text-muted">{process.name}</h2>
        </div>
        <p className="mb-4 max-w-[52ch] font-sans text-[14px] leading-relaxed text-muted-2">
          {process.description}
        </p>
        <span className="rounded-full border border-line-strong px-3 py-1 font-mono text-[10px] uppercase tracking-wide text-muted-2">
          Not yet defined
        </span>
      </div>
    );
  }

  return (
    <Link
      href={`/engagements/${engagementId}/assess/${process.key}`}
      className="block rounded-2xl border border-line-strong bg-paper p-6 transition-colors hover:border-ink focus:outline-none focus-visible:border-steel"
    >
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-[12px] text-muted-2">{process.short_name}</span>
          <h2 className="font-serif text-[20px] text-ink">{process.name}</h2>
        </div>
        {process.has_score && process.band && process.index !== null && (
          <div className="flex items-center gap-3">
            <span className="font-mono text-[13px] text-text">
              {process.index.toFixed(1)}/100
            </span>
            <BandBadge band={process.band} />
          </div>
        )}
      </div>

      <p className="mb-5 max-w-[52ch] font-sans text-[14px] leading-relaxed text-muted">
        {process.description}
      </p>

      <div className="flex items-center gap-3">
        <div
          className="h-1.5 flex-1 overflow-hidden rounded-full bg-paper-3"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${process.name} questionnaire progress`}
        >
          <div className="h-full rounded-full bg-ink" style={{ width: `${progress}%` }} />
        </div>
        <span className="font-mono text-[11px] uppercase text-muted-2">
          {process.answered_count}/{process.question_count} answered
        </span>
      </div>
    </Link>
  );
}

export function AssessIndexPage({ engagementId }: { engagementId: string }) {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["assess-processes", engagementId],
    queryFn: () => assessApi.listProcesses(engagementId),
  });

  if (isLoading) {
    return (
      <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  if (isError || !data) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState
          title="Could not load the processes"
          description={error instanceof Error ? error.message : undefined}
          action={
            <button
              type="button"
              onClick={() => void refetch()}
              className="rounded-full border border-ink px-5 py-2.5 font-sans text-[13px] text-text"
            >
              Try again
            </button>
          }
        />
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      <header className="mb-9 border-b border-line-strong pb-7">
        <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-muted">
          Assess
        </p>
        <h1 className="mb-3 font-serif text-[34px] leading-tight text-ink">
          Business process automation
        </h1>
        <p className="max-w-[74ch] font-sans text-[15px] leading-relaxed text-muted">
          How much of the work still needs a person. Licences reveal what was bought;
          process automation reveals what is used, and the gap between the two is where
          diligence findings live. Each process is assessed step by step and scored on a
          0–100 automation index.
        </p>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        {data.processes.map((process) => (
          <ProcessCard key={process.key} engagementId={engagementId} process={process} />
        ))}
      </div>
    </main>
  );
}
