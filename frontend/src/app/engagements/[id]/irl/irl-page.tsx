"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRef, useState } from "react";

import { IrlAddQuestion } from "@/components/engagement/irl-add-question";
import {
  ImportSummary,
  InventorySection,
} from "@/components/estate/inventory-section";
import { IrlRequestList } from "@/components/engagement/irl-request-list";
import {
  IrlSummaryRail,
  summarise,
} from "@/components/engagement/irl-summary-rail";
import { ReminderPanel } from "@/components/engagement/reminder-panel";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { API_BASE_URL, ApiError } from "@/lib/api/client";
import { checklistApi } from "@/lib/api/checklist";
import { engagementsApi } from "@/lib/api/engagements";
import { irlApi } from "@/lib/api/irl";
import type { ChecklistRead } from "@/types/checklist";
import type { ImportResponsesResult, IrlRead, IrlTracking } from "@/types/irl";

/**
 * Information requests — the single screen for what was asked of the target and what
 * arrived: the request list, and every template the target completes (applications, data
 * and infrastructure, IT team and contracts, projects, cyber tools, IT financials).
 * Renamed from "Initial request list" in Phase 8 (Rishi, 2026-11-18); the workbook keeps
 * the name IRL, which is what clients call it.
 *
 * Absorbed the checklist page on 2026-09-09 (Rishi). The split had been defensible while
 * the checklist was only a progress view, but the shared-drive scan writes findings —
 * follow-up questions, document types, matched files — that only make sense next to the
 * request they belong to. Two pages meant the scan ran on one and its output appeared on
 * the other.
 */

/** A pill button. Primary is the one action that produces something new. */
const ACTION =
  "rounded-full border border-line-strong px-3.5 py-2 font-sans text-[12.5px] font-medium transition-colors hover:bg-paper-2 disabled:opacity-50";

type Section =
  "requests" | "applications" | "data_tech" | "people" | "projects" | "cyber";

const SECTIONS: { key: Section; label: string }[] = [
  { key: "requests", label: "Requests" },
  { key: "applications", label: "Applications" },
  { key: "data_tech", label: "Data & infrastructure" },
  { key: "people", label: "IT team & contracts" },
  { key: "projects", label: "Projects" },
  { key: "cyber", label: "Cyber tools" },
];

export function IrlPage({ engagementId }: { engagementId: string }) {
  const queryClient = useQueryClient();
  const { show } = useToast();
  const [section, setSection] = useState<Section>("requests");

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
        err instanceof ApiError
          ? err.message
          : "Could not generate a request list",
        "error",
      );
    },
  });

  // The edit endpoints all return the whole list, so the cache is replaced wholesale and
  // the counts stay consistent with the row that just changed.
  const replace = (fresh: IrlRead) =>
    queryClient.setQueryData(["irl", engagementId], fresh);

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

  const [importResult, setImportResult] =
    useState<ImportResponsesResult | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);

  const importMutation = useMutation({
    mutationFn: (file: File) => irlApi.importResponses(engagementId, file),
    onSuccess: async (result) => {
      setImportResult(result);
      // Responses live in their own table, so the list has to be refetched to show them.
      replace(await irlApi.getLatest(engagementId));
      const inventoryChanged = (result.inventory?.summaries ?? []).reduce(
        (n, sheet) => n + sheet.created + sheet.updated,
        0,
      );
      if (inventoryChanged > 0) {
        await queryClient.invalidateQueries({
          queryKey: ["inventory", engagementId],
        });
        await queryClient.invalidateQueries({ queryKey: ["estate"] });
      }
      if (result.updated > 0 || inventoryChanged > 0) {
        const parts = [];
        if (result.updated > 0) {
          parts.push(
            `${result.updated} response${result.updated === 1 ? "" : "s"}`,
          );
        }
        if (inventoryChanged > 0) {
          parts.push(
            `${inventoryChanged} inventory row${inventoryChanged === 1 ? "" : "s"}`,
          );
        }
        show(`${parts.join(" and ")} imported`);
      } else {
        // Not a thrown error — the file was readable, it just changed nothing. The
        // summary panel below explains why, so the toast only has to flag it.
        show("No responses were imported", "error");
      }
    },
    onError: (err: unknown) => {
      setImportResult(null);
      show(
        err instanceof ApiError ? err.message : "Could not read that workbook",
        "error",
      );
    },
  });

  // ------------------------------------------------------- the shared-drive scan
  const scanMutation = useMutation({
    mutationFn: () => checklistApi.scan(engagementId),
    onSuccess: async (fresh: ChecklistRead) => {
      // The scan writes to the document-status table, which the IRL reads for its
      // tracking — so the list itself has to be refetched, not just this response cached.
      replace(await irlApi.getLatest(engagementId));

      const scan = fresh.scan;
      if (!scan) {
        show("Request list updated from the shared drive");
        return;
      }
      // Say what the walk actually did. A scan that read 52 files and changed nothing is
      // a different event from one that found no drive, and the consultant needs to be
      // able to tell them apart without diffing the rows.
      const parts = [
        `${scan.files_seen} file${scan.files_seen === 1 ? "" : "s"} read`,
        `${scan.updated} request${scan.updated === 1 ? "" : "s"} updated`,
      ];
      if (scan.follow_ups > 0) {
        parts.push(
          `${scan.follow_ups} follow-up${scan.follow_ups === 1 ? "" : "s"} raised`,
        );
      }
      if (scan.skipped_human > 0)
        parts.push(`${scan.skipped_human} left as set by hand`);
      if (scan.unmatched_files.length > 0) {
        parts.push(`${scan.unmatched_files.length} file(s) nothing asked for`);
      }

      // A scan that fell back to filename matching cannot judge completeness and writes
      // no follow-up questions. It looks identical to a good one unless we say so — and
      // a consultant who thinks the drive was read would trust it too far.
      if (scan.generator !== "llm") {
        show(
          `${parts.join(" · ")} — matched on filenames only, so completeness was not ` +
            `assessed and no follow-up questions were raised. Run the scan again to read ` +
            `the documents.`,
          "error",
        );
        return;
      }
      show(parts.join(" · "));
    },
    onError: (err: unknown) => {
      show(
        err instanceof ApiError
          ? err.message
          : "Could not scan the shared drive",
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

  const notGeneratedYet =
    isError && error instanceof ApiError && error.code === "no_irl";

  if (notGeneratedYet) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="No information requests yet"
          description="Build the request list from the scope of work. Running company research first makes the questions specific to this target."
          action={
            <button
              type="button"
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink disabled:opacity-50"
            >
              {generateMutation.isPending
                ? "Generating…"
                : "Generate request list"}
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
  const kinds = Object.fromEntries(
    payload.questions.map((q) => [q.id, q.kind]),
  );
  const progress = summarise(irl.tracking, irl.responses, kinds);
  const lastScannedAt =
    Object.values(irl.tracking)
      .map((t) => t.scanned_at)
      .filter((v): v is string => Boolean(v))
      .sort()
      .at(-1) ?? null;

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pb-24">
      <IrlSummaryRail
        companyName={payload.company_name ?? null}
        version={irl.version}
        createdAt={irl.created_at}
        sourceScopeVersion={payload.source_scope_version ?? null}
        lastScannedAt={lastScannedAt}
        progress={progress}
        actions={
          <>
            <button
              type="button"
              onClick={() => scanMutation.mutate()}
              disabled={scanMutation.isPending}
              title="Reads every file on the shared drive, matches it to a request, and writes the status, document type and any follow-up questions"
              className="rounded-full bg-ink px-3.5 py-2 font-sans text-[12.5px] font-medium text-paper-on-ink transition-colors hover:bg-ink-2 disabled:opacity-50"
            >
              {scanMutation.isPending
                ? "Reading the drive…"
                : "Scan shared drive"}
            </button>
            <a
              href={`${API_BASE_URL}/engagements/${engagementId}/irl/export.xlsx`}
              download
              className="rounded-full bg-kpmg-blue px-3.5 py-2 font-sans text-[12.5px] font-medium text-paper-on-ink transition-colors hover:bg-kpmg-blue-dark"
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
              className={ACTION}
            >
              {importMutation.isPending ? "Reading…" : "Upload responses"}
            </button>
            <button
              type="button"
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className={ACTION}
            >
              {generateMutation.isPending ? "Regenerating…" : "Regenerate"}
            </button>
          </>
        }
      />

      {/* A scan reads and judges every file, so it runs for the better part of a minute.
          Saying so beats a button that looks stuck. */}
      {scanMutation.isPending && (
        <div
          role="status"
          className="mb-6 flex items-start gap-3 rounded-2xl border border-steel/40 bg-steel-tint px-5 py-4"
        >
          <span
            aria-hidden
            className="mt-1 h-2 w-2 flex-none animate-pulse rounded-full bg-steel"
          />
          <p className="font-sans text-[13.5px] leading-[1.55] text-text">
            Reading each document on the shared drive and matching it to a
            request. This usually takes under a minute — statuses, document
            types and follow-up questions land on the rows below when it
            finishes.
          </p>
        </div>
      )}

      {/* Requests, and the two structured intakes the target completes in the same
          workbook (PHASE6_PLAN D2). One page, because they go out and come back as one file. */}
      <div
        role="tablist"
        aria-label="Request list sections"
        className="mb-7 flex flex-wrap gap-1 rounded-full border border-line-strong bg-paper-2 p-1"
      >
        {SECTIONS.map((s) => (
          <button
            key={s.key}
            type="button"
            role="tab"
            aria-selected={section === s.key}
            onClick={() => setSection(s.key)}
            className={`rounded-full px-4 py-2 font-sans text-[13px] font-medium transition-colors ${
              section === s.key
                ? "bg-ink text-paper-on-ink"
                : "text-muted hover:text-text"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {importResult?.inventory &&
        importResult.inventory.summaries.length > 0 && (
          <ImportSummary
            result={importResult.inventory}
            onDismiss={() =>
              setImportResult((r) => (r ? { ...r, inventory: null } : r))
            }
          />
        )}

      {section === "applications" && (
        <InventorySection
          engagementId={engagementId}
          kinds={["application"]}
          intro="Every system the business runs on: functionality, version and licences, customisation, integration, hosting, support and lifecycle. Facts only; criticality, automation and AI are judged in Assess."
        />
      )}

      {section === "data_tech" && (
        <InventorySection
          engagementId={engagementId}
          kinds={["data_domain", "platform"]}
          intro="What data the business holds and where it is mastered, and the infrastructure platforms underneath the applications. Governance quality, support status and recoverability are judged in Assess."
        />
      )}

      {section === "people" && (
        <InventorySection
          engagementId={engagementId}
          kinds={["it_role", "it_contract"]}
          intro="Who runs the technology and on what terms it is bought. The team shows key-person risk and the in-house versus outsourced mix; contracts are reviewed for their terms and expiry — renewal dates, notice periods, change of control and anything held by the parent."
        />
      )}

      {section === "projects" && (
        <InventorySection
          engagementId={engagementId}
          kinds={["it_project"]}
          intro="The technology projects in flight and planned: objective, status, dates, allocated capital against what has been used, percentage complete, delivery model and vendor. The target's own figures — Assess measures them against the plan and reconciles the roadmap against the change budget."
        />
      )}

      {section === "cyber" && (
        <InventorySection
          engagementId={engagementId}
          kinds={["cyber_tool"]}
          intro="Which security tools the target runs, from a checklist of purposes. A tool is evidence beside a control, never proof that it works: a tool the target lacks fails its check in Assess until the analyst answers it; a tool it has passes nothing by itself."
        />
      )}

      {section === "requests" && (
        <>
          {payload.intro && (
            <p className="mb-6 max-w-[78ch] font-sans text-[14.5px] leading-[1.65] text-muted">
              {payload.intro}
            </p>
          )}

          {!payload.used_research && (
            <Link
              href={`/engagements/${engagementId}/research`}
              className="mb-6 inline-block font-sans text-[13px] text-steel underline underline-offset-2"
            >
              Run company research to tailor these questions
            </Link>
          )}

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

          <IrlRequestList
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
            functions={Array.from(
              new Set(payload.questions.map((q) => q.function)),
            ).sort()}
            onAdd={addQuestion}
          />

          <ReminderPanel
            progress={progress}
            companyName={payload.company_name ?? null}
          />
        </>
      )}
    </main>
  );
}
