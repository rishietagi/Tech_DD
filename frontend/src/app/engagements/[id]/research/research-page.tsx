"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { ResearchSummary } from "@/components/engagement/research-summary";
import { ResearchEditor } from "@/components/engagement/research-editor";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { engagementsApi } from "@/lib/api/engagements";
import { researchApi } from "@/lib/api/research";

export function ResearchPage({ engagementId }: { engagementId: string }) {
  const queryClient = useQueryClient();
  const { show } = useToast();
  const [editing, setEditing] = useState(false);
  const saved = (fresh: Parameters<typeof queryClient.setQueryData>[1]) => {
    queryClient.setQueryData(["research", engagementId], fresh);
    setEditing(false);
    show("Research brief saved");
  };

  const { data: engagement, isLoading: isLoadingEngagement } = useQuery({
    queryKey: ["engagement", engagementId],
    queryFn: () => engagementsApi.get(engagementId),
  });

  const {
    data: research,
    isLoading: isLoadingResearch,
    isError,
    error,
  } = useQuery({
    queryKey: ["research", engagementId],
    queryFn: () => researchApi.getLatest(engagementId),
    // "Not run yet" is a meaningful state, not a failure — see the scope page.
    retry: false,
  });

  const runMutation = useMutation({
    mutationFn: () => researchApi.run(engagementId),
    onSuccess: (fresh) => {
      queryClient.setQueryData(["research", engagementId], fresh);
      show("Research complete");
    },
    onError: (err: unknown) => {
      show(
        err instanceof ApiError
          ? err.message
          : "Could not research this target",
        "error",
      );
    },
  });

  if (isLoadingEngagement || isLoadingResearch) {
    return (
      <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  if (engagement && engagement.status === "draft") {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="File the engagement first"
          description="Research runs against the target captured in the intake."
          action={
            <Link
              href={`/intake/${engagementId}/review`}
              className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink"
            >
              Go to review
            </Link>
          }
        />
      </main>
    );
  }

  const notRunYet =
    isError && error instanceof ApiError && error.code === "no_research";

  if (notRunYet && editing) {
    return (
      <main className="mx-auto w-full max-w-[1200px] px-7 pt-12 pb-24">
        <ResearchEditor
          engagementId={engagementId}
          research={null}
          onSaved={saved}
          onCancel={() => setEditing(false)}
        />
      </main>
    );
  }

  if (notRunYet) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="No research yet"
          description="Search public sources for what is known about this target — funding, incidents, technology and regulatory history — with every point linked to where it came from. With the AI off, write the brief by hand from what you know."
          action={
            <div className="flex flex-wrap justify-center gap-3">
              <button
                type="button"
                onClick={() => runMutation.mutate()}
                disabled={runMutation.isPending}
                className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink disabled:opacity-50"
              >
                {runMutation.isPending
                  ? "Researching…"
                  : "Research this target"}
              </button>
              <button
                type="button"
                onClick={() => setEditing(true)}
                className="rounded-full border border-line-strong px-5 py-3 font-sans text-[13px] font-medium text-text hover:bg-paper-2"
              >
                Write it by hand
              </button>
            </div>
          }
        />
      </main>
    );
  }

  if (isError || !research) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState title="Couldn't load the research" />
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      {/* flex-wrap: at phone width the version line and the button do not fit on one
          row, and without it the button is pushed past the viewport edge. */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <span className="font-sans text-[13px] text-muted">
          Version {research.version}
          {" · "}
          {new Date(research.created_at).toLocaleDateString()}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setEditing((e) => !e)}
            className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2"
          >
            {editing ? "Close editor" : "Edit brief"}
          </button>
          <button
            type="button"
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending}
            className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2 disabled:opacity-50"
          >
            {runMutation.isPending ? "Researching…" : "Run again"}
          </button>
        </div>
      </div>
      {editing && (
        <ResearchEditor
          engagementId={engagementId}
          research={research.payload}
          onSaved={saved}
          onCancel={() => setEditing(false)}
        />
      )}

      <div className="mb-8">
        <p className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
          Company research
        </p>
        <h1 className="font-display text-3xl font-semibold text-text">
          {research.company_name ?? "The target"}
        </h1>
      </div>

      <ResearchSummary research={research.payload} />
    </main>
  );
}
