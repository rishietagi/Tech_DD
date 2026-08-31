"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { ScopeDocument } from "@/components/engagement/scope-document";
import { ScopeDocumentV2 } from "@/components/engagement/scope-document-v2";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { API_BASE_URL, ApiError } from "@/lib/api/client";
import { engagementsApi, scopeApi } from "@/lib/api/engagements";
import { isV2Payload } from "@/types/engagement";

export function ScopePage({ engagementId }: { engagementId: string }) {
  const queryClient = useQueryClient();
  const { show } = useToast();

  const { data: engagement, isLoading: isLoadingEngagement } = useQuery({
    queryKey: ["engagement", engagementId],
    queryFn: () => engagementsApi.get(engagementId),
  });

  const {
    data: scope,
    isLoading: isLoadingScope,
    isError,
    error,
  } = useQuery({
    queryKey: ["scope", engagementId],
    queryFn: () => scopeApi.getLatest(engagementId),
    retry: false,
    enabled: !!engagement,
  });

  const generateMutation = useMutation({
    mutationFn: () => scopeApi.generate(engagementId),
    onSuccess: (newScope) => {
      queryClient.setQueryData(["scope", engagementId], newScope);
      show("Scope generated");
    },
    onError: () => show("Could not generate a scope", "error"),
  });

  const noScopeYet = isError && error instanceof ApiError && error.code === "no_scope";

  if (isLoadingEngagement || isLoadingScope) {
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
          title="This engagement hasn't been filed yet"
          description="A scope of work can only be generated once the intake is complete and filed."
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

  if (noScopeYet) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="No scope generated yet"
          description="Derive the scope of work from this engagement's intake."
          action={
            <button
              type="button"
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink disabled:opacity-50"
            >
              {generateMutation.isPending ? "Generating…" : "Generate scope"}
            </button>
          }
        />
      </main>
    );
  }

  if (isError || !scope) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState title="Couldn't load the scope of work" />
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      <div className="mb-6 flex items-center justify-between gap-4">
        <span className="font-sans text-[13px] text-muted">
          Version {scope.version}
          {" · "}
          {new Date(scope.created_at).toLocaleDateString()}
        </span>
        <div className="flex items-center gap-2">
          {isV2Payload(scope.payload) && (
            <>
              {/* A scope of work is usually circulated as a deck, so PPT leads.
                  `download` names the file if the browser handles the
                  Content-Disposition itself. */}
              <a
                href={`${API_BASE_URL}/engagements/${engagementId}/scope/export.pptx`}
                download
                className="rounded-full bg-kpmg-blue px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink transition-colors hover:bg-kpmg-blue-dark"
              >
                Download PPT
              </a>
              <a
                href={`${API_BASE_URL}/engagements/${engagementId}/scope/export.pdf`}
                download
                className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2"
              >
                Download PDF
              </a>
              <a
                href={`${API_BASE_URL}/engagements/${engagementId}/scope/export`}
                className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2"
              >
                Export Markdown
              </a>
            </>
          )}
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
      {isV2Payload(scope.payload) ? (
        <ScopeDocumentV2 scope={scope.payload} />
      ) : (
        <ScopeDocument payload={scope.payload} version={scope.version} />
      )}
    </main>
  );
}
