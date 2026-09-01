"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { IrlTable } from "@/components/engagement/irl-table";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { API_BASE_URL, ApiError } from "@/lib/api/client";
import { engagementsApi } from "@/lib/api/engagements";
import { irlApi } from "@/lib/api/irl";

export function IrlPage({ engagementId }: { engagementId: string }) {
  const queryClient = useQueryClient();
  const { show } = useToast();

  const { data: engagement, isLoading: isLoadingEngagement } = useQuery({
    queryKey: ["engagement", engagementId],
    queryFn: () => engagementsApi.get(engagementId),
  });

  const {
    data: irl,
    isLoading: isLoadingIrl,
    isError,
    error,
  } = useQuery({
    queryKey: ["irl", engagementId],
    queryFn: () => irlApi.getLatest(engagementId),
    retry: false,
  });

  const generateMutation = useMutation({
    mutationFn: () => irlApi.generate(engagementId),
    onSuccess: (fresh) => {
      queryClient.setQueryData(["irl", engagementId], fresh);
      show("Request list generated");
    },
    onError: (err: unknown) => {
      show(
        err instanceof ApiError ? err.message : "Could not generate a request list",
        "error",
      );
    },
  });

  if (isLoadingEngagement || isLoadingIrl) {
    return (
      <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  // The IRL is built from the scope's evidence lists, so a scope is a real precondition.
  if (engagement && engagement.status !== "scoped") {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="Generate a scope of work first"
          description="The request list asks for the evidence the scope decided it needs, so it cannot be built before the scope exists."
          action={
            <Link
              href={`/engagements/${engagementId}/scope`}
              className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink"
            >
              Go to scope of work
            </Link>
          }
        />
      </main>
    );
  }

  const notGeneratedYet = isError && error instanceof ApiError && error.code === "no_irl";

  if (notGeneratedYet) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="No request list yet"
          description="Build the initial request list from the scope of work. Running company research first makes the questions specific to this target."
          action={
            <button
              type="button"
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink disabled:opacity-50"
            >
              {generateMutation.isPending ? "Generating…" : "Generate request list"}
            </button>
          }
        />
      </main>
    );
  }

  if (isError || !irl) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState title="Couldn't load the request list" />
      </main>
    );
  }

  const { payload } = irl;
  const answered = Object.values(irl.responses).filter((v) => v.trim()).length;

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      <div className="mb-6 flex items-center justify-between gap-4">
        <span className="font-sans text-[13px] text-muted">
          Version {irl.version}
          {" · "}
          {new Date(irl.created_at).toLocaleDateString()}
          {payload.source_scope_version != null && ` · from scope v${payload.source_scope_version}`}
        </span>
        <div className="flex items-center gap-2">
          <a
            href={`${API_BASE_URL}/engagements/${engagementId}/irl/export.xlsx`}
            download
            className="rounded-full bg-kpmg-blue px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink transition-colors hover:bg-kpmg-blue-dark"
          >
            Download Excel
          </a>
          <button
            type="button"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2 disabled:opacity-50"
          >
            {generateMutation.isPending ? "Regenerating…" : "Regenerate"}
          </button>
        </div>
      </div>

      <div className="mb-6">
        <p className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
          Initial request list
        </p>
        <h1 className="mb-4 font-display text-3xl font-semibold text-text">
          {payload.company_name ?? "The target"}
        </h1>
        <p className="max-w-[72ch] font-sans text-[15px] leading-[1.65] text-text">
          {payload.intro}
        </p>
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-x-5 gap-y-1 font-sans text-[13px] text-muted">
        <span>
          {payload.questions.length} request{payload.questions.length === 1 ? "" : "s"} across{" "}
          {payload.functions.length} function{payload.functions.length === 1 ? "" : "s"}
        </span>
        <span>{answered} answered</span>
        {!payload.used_research && (
          <Link
            href={`/engagements/${engagementId}/research`}
            className="text-steel underline underline-offset-2"
          >
            Run company research to tailor these questions
          </Link>
        )}
      </div>

      <IrlTable engagementId={engagementId} payload={payload} responses={irl.responses} />
    </main>
  );
}
