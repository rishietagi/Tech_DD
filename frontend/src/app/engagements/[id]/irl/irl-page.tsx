"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRef, useState } from "react";

import { IrlAddQuestion } from "@/components/engagement/irl-add-question";
import { IrlTable } from "@/components/engagement/irl-table";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { API_BASE_URL, ApiError } from "@/lib/api/client";
import { engagementsApi } from "@/lib/api/engagements";
import { irlApi } from "@/lib/api/irl";
import type { ImportResponsesResult, IrlRead, IrlTracking } from "@/types/irl";

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

  // The edit endpoints all return the whole list, so the cache is replaced wholesale and
  // the counts stay consistent with the row that just changed.
  const replace = (fresh: IrlRead) => queryClient.setQueryData(["irl", engagementId], fresh);

  const updateQuestion = async (
    questionId: string,
    patch: { question?: string; function?: string; scope_area?: string },
  ) => {
    try {
      replace(await irlApi.updateQuestion(engagementId, questionId, patch));
    } catch {
      show("Could not save that change", "error");
    }
  };

  const saveTracking = async (
    questionId: string,
    patch: {
      status?: IrlTracking["status"];
      document_type?: string;
      remarks?: string;
    },
  ) => {
    try {
      replace(await irlApi.saveTracking(engagementId, questionId, patch));
    } catch {
      show("Could not save that change", "error");
    }
  };

  const deleteQuestion = async (questionId: string) => {
    try {
      replace(await irlApi.deleteQuestion(engagementId, questionId));
      show("Request removed");
    } catch {
      show("Could not remove that request", "error");
    }
  };

  const addQuestion = async (body: {
    question: string;
    function: string;
    scope_area?: string;
  }) => {
    replace(await irlApi.addQuestion(engagementId, body));
    show("Request added");
  };

  const [importResult, setImportResult] = useState<ImportResponsesResult | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);

  const importMutation = useMutation({
    mutationFn: (file: File) => irlApi.importResponses(engagementId, file),
    onSuccess: async (result) => {
      setImportResult(result);
      // Responses live in their own table, so the list has to be refetched to show them.
      replace(await irlApi.getLatest(engagementId));
      if (result.updated > 0) {
        show(`${result.updated} response${result.updated === 1 ? "" : "s"} imported`);
      } else {
        // Not a thrown error — the file was readable, it just changed nothing. The
        // summary panel below explains why, so the toast only has to flag it.
        show("No responses were imported", "error");
      }
    },
    onError: (err: unknown) => {
      setImportResult(null);
      show(err instanceof ApiError ? err.message : "Could not read that workbook", "error");
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
          {/* The completed workbook comes back here. The input is hidden because a bare
              file input cannot be styled to match, and the button is the real control. */}
          <input
            ref={fileInput}
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) importMutation.mutate(file);
              event.target.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            disabled={importMutation.isPending}
            className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium transition-colors hover:bg-paper-2 disabled:opacity-50"
          >
            {importMutation.isPending ? "Reading…" : "Upload responses"}
          </button>
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
        <span>
          {
            Object.values(irl.tracking).filter(
              (t) => t.status === "received_completely",
            ).length
          }{" "}
          received
        </span>
        {!payload.used_research && (
          <Link
            href={`/engagements/${engagementId}/research`}
            className="text-steel underline underline-offset-2"
          >
            Run company research to tailor these questions
          </Link>
        )}
      </div>

      {/* What the upload actually changed. Reported rather than assumed: an import that
          matched nothing looks identical to one that worked. */}
      {importResult && (
        <div className="mb-5 rounded-xl border border-line-strong bg-paper-2 px-5 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-sans text-[14px] text-text">
                {importResult.updated} response
                {importResult.updated === 1 ? "" : "s"} imported from{" "}
                {importResult.matched} matched row
                {importResult.matched === 1 ? "" : "s"}
                {importResult.skipped_blank > 0 &&
                  ` · ${importResult.skipped_blank} left blank`}
              </p>
              {importResult.note && (
                <p className="mt-1 max-w-[80ch] font-sans text-[12.5px] text-muted">
                  {importResult.note}
                </p>
              )}
              {importResult.unmatched_rows.length > 0 && (
                <ul className="mt-2 max-w-[80ch] list-disc space-y-0.5 pl-5 font-sans text-[12px] text-muted-2">
                  {importResult.unmatched_rows.map((row) => (
                    <li key={row}>{row}</li>
                  ))}
                </ul>
              )}
            </div>
            <button
              type="button"
              onClick={() => setImportResult(null)}
              className="flex-none font-sans text-[12px] text-muted hover:text-text"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <IrlTable
        engagementId={engagementId}
        payload={payload}
        responses={irl.responses}
        tracking={irl.tracking}
        onUpdate={updateQuestion}
        onDelete={deleteQuestion}
        onTrack={saveTracking}
      />

      <IrlAddQuestion
        scopeAreas={payload.functions.map((f) => f.name)}
        functions={Array.from(new Set(payload.questions.map((q) => q.function))).sort()}
        onAdd={addQuestion}
      />
    </main>
  );
}
