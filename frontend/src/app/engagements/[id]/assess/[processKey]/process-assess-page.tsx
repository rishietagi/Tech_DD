"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { ProcessQuestionnaire } from "@/components/engagement/process-questionnaire";
import { ProcessScore } from "@/components/engagement/process-score";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { assessApi } from "@/lib/api/assess";
import { ApiError } from "@/lib/api/client";
import type { AssessmentRead, AssessmentScoreRead } from "@/types/assess";

type Tab = "questionnaire" | "score";

export function ProcessAssessPage({
  engagementId,
  processKey,
}: {
  engagementId: string;
  processKey: string;
}) {
  const queryClient = useQueryClient();
  const { show } = useToast();
  const [tab, setTab] = useState<Tab>("questionnaire");

  const assessmentKey = ["assessment", engagementId, processKey];
  const scoreKey = ["assessment-score", engagementId, processKey];

  const {
    data: assessment,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: assessmentKey,
    queryFn: () => assessApi.get(engagementId, processKey),
    // "Not yet defined" is a meaningful state, not a transient failure.
    retry: false,
  });

  const { data: score } = useQuery({
    queryKey: scoreKey,
    queryFn: () => assessApi.getScore(engagementId, processKey),
    // A process that has never been scored 404s. That is expected, not an error.
    retry: false,
    enabled: !isError,
  });

  const saveAnswer = async (questionId: string, value: string) => {
    const fresh = await assessApi.saveAnswer(engagementId, processKey, questionId, value);
    // The endpoint returns the whole assessment, so the progress count stays in step with
    // the answer just written.
    queryClient.setQueryData(assessmentKey, fresh);
  };

  const addQuestionMutation = useMutation({
    mutationFn: ({ stepKey, text }: { stepKey: string; text: string }) =>
      assessApi.addQuestion(engagementId, processKey, stepKey, text),
    onSuccess: (fresh: AssessmentRead) => {
      queryClient.setQueryData(assessmentKey, fresh);
      show("Question added");
    },
    onError: () => show("Could not add that question", "error"),
  });

  const scoreMutation = useMutation({
    mutationFn: () => assessApi.score(engagementId, processKey),
    onSuccess: (fresh: AssessmentScoreRead) => {
      queryClient.setQueryData(scoreKey, fresh);
      void queryClient.invalidateQueries({ queryKey: ["assess-processes", engagementId] });
      void queryClient.invalidateQueries({ queryKey: assessmentKey });
      setTab("score");
      show(`Scored ${fresh.payload.index.toFixed(1)}/100 — ${fresh.payload.band_label}`);
    },
    onError: (err: unknown) =>
      show(err instanceof ApiError ? err.message : "Could not score this process", "error"),
  });

  if (isLoading) {
    return (
      <main className="mx-auto w-full max-w-[1200px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  // A process named in the product but with no questionnaire behind it yet.
  if (isError && error instanceof ApiError && error.code === "process_not_defined") {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <EmptyState
          title="This process is not yet defined"
          description={error.message}
          action={
            <Link
              href={`/engagements/${engagementId}/assess`}
              className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink"
            >
              Back to processes
            </Link>
          }
        />
      </main>
    );
  }

  if (isError || !assessment) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState
          title="Could not load this assessment"
          description={error instanceof Error ? error.message : undefined}
        />
      </main>
    );
  }

  const progress =
    assessment.question_count > 0
      ? Math.round((assessment.answered_count / assessment.question_count) * 100)
      : 0;
  const nothingAnswered = assessment.answered_count === 0;

  return (
    <main className="mx-auto w-full max-w-[1200px] px-7 pt-12 pb-24">
      <header className="mb-8 border-b border-line-strong pb-7">
        <Link
          href={`/engagements/${engagementId}/assess`}
          className="mb-3 inline-block font-mono text-[11px] uppercase tracking-wide text-muted hover:text-text"
        >
          ← Assess
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <h1 className="mb-3 font-serif text-[34px] leading-tight text-ink">
              {assessment.name}
            </h1>
            <p className="max-w-[70ch] font-sans text-[15px] leading-relaxed text-muted">
              {assessment.description}
            </p>
          </div>

          <button
            type="button"
            onClick={() => scoreMutation.mutate()}
            disabled={scoreMutation.isPending || nothingAnswered}
            title={
              nothingAnswered
                ? "Answer at least one question before scoring"
                : "Score this process from the recorded answers"
            }
            className="flex-none rounded-full border border-ink bg-ink px-6 py-3 font-sans text-[14px] font-medium text-paper-on-ink transition-opacity disabled:opacity-40"
          >
            {scoreMutation.isPending ? "Scoring…" : "Score this process"}
          </button>
        </div>

        <div className="mt-6 flex items-center gap-3">
          <div
            className="h-1.5 w-full max-w-[360px] overflow-hidden rounded-full bg-paper-3"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Questionnaire progress"
          >
            <div className="h-full rounded-full bg-ink" style={{ width: `${progress}%` }} />
          </div>
          <span className="font-mono text-[11px] uppercase text-muted-2">
            {assessment.answered_count}/{assessment.question_count} answered
          </span>
        </div>
      </header>

      <nav className="mb-8 flex gap-1 border-b border-line" aria-label="Assessment views">
        {(["questionnaire", "score"] as const).map((value) => {
          const active = tab === value;
          const disabled = value === "score" && !score;
          return (
            <button
              key={value}
              type="button"
              disabled={disabled}
              onClick={() => setTab(value)}
              aria-current={active ? "page" : undefined}
              className={`-mb-px border-b-2 px-4 py-2.5 font-sans text-[14px] transition-colors disabled:opacity-40 ${
                active
                  ? "border-ink text-ink"
                  : "border-transparent text-muted hover:text-text"
              }`}
            >
              {value === "questionnaire" ? "Questionnaire" : "Score & summary"}
            </button>
          );
        })}
      </nav>

      {tab === "questionnaire" ? (
        <ProcessQuestionnaire
          assessment={assessment}
          onSave={saveAnswer}
          onAdd={async (stepKey, text) => {
            await addQuestionMutation.mutateAsync({ stepKey, text });
          }}
        />
      ) : score ? (
        <>
          {score.payload.questionnaire_version !== assessment.questionnaire_version && (
            <p className="mb-6 rounded-xl border border-redline bg-redline-tint px-5 py-3 font-sans text-[13px] text-text">
              This score was produced against questionnaire v
              {score.payload.questionnaire_version}; the questionnaire is now v
              {assessment.questionnaire_version}. Re-score to bring it up to date.
            </p>
          )}
          <ProcessScore payload={score.payload} />
        </>
      ) : (
        <EmptyState
          title="Not scored yet"
          description="Answer the questionnaire, then score the process to produce the index and the executive summary."
        />
      )}
    </main>
  );
}
