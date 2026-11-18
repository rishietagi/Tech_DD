"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { RemarksBox } from "@/components/engagement/process-questionnaire";
import { GapRegister } from "@/components/estate/gap-register";
import {
  ApplicationResults,
  DataTechResults,
  ScoreHeader,
} from "@/components/estate/estate-results";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { estateApi } from "@/lib/api/estate";
import type {
  EstateDomain,
  EstateQuestion,
  EstateRead,
  EstateScoreRead,
  EstateSubject,
  GapEdit,
} from "@/types/estate";

const GROUP_LABELS: Record<string, string> = {
  criticality: "Criticality",
  business_fit: "Business fit",
  technical_fit: "Technical fit",
  automation: "Automation",
  ai: "Artificial intelligence",
  resilience: "Resilience",
  engineering: "Engineering practice",
  cyber: "Cyber security",
};

const KIND_LABELS: Record<string, string> = {
  application: "Applications",
  data_domain: "Data domains",
  platform: "Platforms",
  estate: "Estate",
};

const COPY: Record<
  EstateDomain,
  { indexLabel: string; scoreLabel: string; empty: string }
> = {
  applications: {
    indexLabel: "Application automation index",
    scoreLabel: "Score applications",
    empty:
      "Add the applications on the request list — from the target's completed inventory sheet, or by hand from management meetings — and they appear here to assess.",
  },
  data_tech: {
    indexLabel: "Data & technology index",
    scoreLabel: "Score data & technology",
    empty:
      "Add data domains and platforms on the request list. The estate checks below can be answered without them.",
  },
};

function QuestionCard({
  question,
  value,
  remarks,
  onPick,
  onRemarks,
  compact,
}: {
  question: EstateQuestion;
  value: string;
  remarks: string;
  onPick: (value: string) => void;
  onRemarks: (
    questionId: string,
    patch: { value?: string; remarks?: string },
  ) => Promise<void>;
  compact: boolean;
}) {
  return (
    <div className="rounded-2xl border border-line-strong bg-paper px-5 py-4">
      <p className="font-sans text-[15px] font-semibold text-text">
        {question.id.match(/^[A-Z]{2}\d$/) && (
          <span className="mr-2 font-mono text-[11.5px] font-normal text-muted">
            {question.id}
          </span>
        )}
        {question.text}
      </p>
      {question.help && (
        <p className="mt-0.5 font-sans text-[12.5px] text-muted">
          {question.help}
        </p>
      )}
      <div
        role="radiogroup"
        aria-label={question.text}
        className={compact ? "mt-3 flex flex-wrap gap-2" : "mt-3 grid gap-1.5"}
      >
        {question.options.map((option) => {
          const selected = option.value === value;
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={selected}
              // Clicking the chosen option again clears it — an answer picked by mistake
              // must be removable, or it scores as if it were evidence.
              onClick={() => onPick(selected ? "" : option.value)}
              className={`rounded-xl border px-3.5 py-2 text-left font-sans text-[13.5px] leading-[1.4] transition-colors ${
                compact ? "rounded-full" : ""
              } ${
                selected
                  ? "border-ink bg-kpmg-blue-tint font-medium text-text"
                  : "border-line-strong text-muted hover:bg-paper-2 hover:text-text"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
      {value && (
        <RemarksBox
          questionId={question.id}
          value={remarks}
          onSave={onRemarks}
        />
      )}
    </div>
  );
}

function SubjectList({
  subjects,
  selected,
  onSelect,
}: {
  subjects: EstateSubject[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  const kinds = Array.from(new Set(subjects.map((s) => s.kind)));
  return (
    <nav aria-label="Items to assess" className="space-y-5">
      {kinds.map((kind) => (
        <div key={kind}>
          <p className="mb-1.5 px-2 font-mono text-[10.5px] uppercase tracking-wide text-muted">
            {KIND_LABELS[kind]}
          </p>
          <ul className="space-y-1">
            {subjects
              .filter((s) => s.kind === kind)
              .map((s) => {
                const done =
                  s.answered >= s.question_count && s.question_count > 0;
                const active = s.id === selected;
                return (
                  <li key={s.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(s.id)}
                      aria-current={active ? "true" : undefined}
                      className={`w-full rounded-xl border px-3 py-2.5 text-left transition-colors ${
                        active
                          ? "border-ink bg-kpmg-blue-tint"
                          : "border-transparent hover:bg-paper-2"
                      }`}
                    >
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="truncate font-sans text-[13.5px] font-medium text-text">
                          <span className="mr-1.5 font-mono text-[11px] text-muted">
                            {s.ref}
                          </span>
                          {s.name}
                        </span>
                        <span
                          className={`flex-none font-mono text-[10.5px] ${done ? "text-status-received" : "text-muted-2"}`}
                        >
                          {s.answered}/{s.question_count}
                        </span>
                      </div>
                      {s.subtitle && (
                        <div className="truncate font-sans text-[11.5px] text-muted-2">
                          {s.subtitle}
                        </div>
                      )}
                    </button>
                  </li>
                );
              })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

/**
 * One estate assessment — applications, or data & technology.
 *
 * Two views: **Assess** (pick an item, answer its questions, add remarks) and **Score &
 * gap register** (the latest stored score). Scoring is a deliberate click, not a side
 * effect of answering: a score is a versioned judgement, and a version per keystroke would
 * make the history unreadable.
 */
export function EstateAssessment({
  engagementId,
  domain,
}: {
  engagementId: string;
  domain: EstateDomain;
}) {
  const queryClient = useQueryClient();
  const { show } = useToast();
  const [view, setView] = useState<"assess" | "results">("assess");
  const [selected, setSelected] = useState<string | null>(null);
  const copy = COPY[domain];

  const estateKey = ["estate", engagementId, domain];
  const scoreKey = ["estate", engagementId, domain, "score"];

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: estateKey,
    queryFn: () => estateApi.get(engagementId, domain),
  });

  const score = useQuery({
    queryKey: scoreKey,
    queryFn: () => estateApi.getScore(engagementId, domain),
    retry: false,
  });

  useEffect(() => {
    if (data && (!selected || !data.subjects.some((s) => s.id === selected))) {
      setSelected(data.subjects[0]?.id ?? null);
    }
  }, [data, selected]);

  const scoreMutation = useMutation({
    mutationFn: () => estateApi.score(engagementId, domain),
    onSuccess: (fresh) => {
      queryClient.setQueryData(scoreKey, fresh);
      queryClient.setQueryData<EstateRead | undefined>(estateKey, (old) =>
        old ? { ...old, latest_score_version: fresh.version } : old,
      );
      void queryClient.invalidateQueries({
        queryKey: ["estate-summary", engagementId],
      });
      setView("results");
      show(
        `Scored — version ${fresh.version}, ${fresh.payload.gaps.length} gaps`,
      );
    },
    onError: (err: unknown) =>
      show(
        err instanceof ApiError
          ? err.message
          : "Could not score the assessment",
        "error",
      ),
  });

  const save = async (
    subjectId: string,
    questionId: string,
    patch: { value?: string; remarks?: string },
  ) => {
    const fresh = await estateApi.saveAnswer(engagementId, domain, {
      subject_id: subjectId,
      question_id: questionId,
      ...patch,
    });
    queryClient.setQueryData(estateKey, fresh);
  };

  const editGap = async (key: string, edit: GapEdit) => {
    try {
      queryClient.setQueryData(
        scoreKey,
        await estateApi.editGap(engagementId, domain, key, edit),
      );
      show("Gap updated");
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : "Could not save that gap",
        "error",
      );
      throw err;
    }
  };

  const revertGap = async (key: string) => {
    queryClient.setQueryData(
      scoreKey,
      await estateApi.revertGap(engagementId, domain, key),
    );
    show("Reverted to the generated text");
  };

  if (isLoading) return <Skeleton className="h-96 w-full" />;
  if (isError || !data) {
    return (
      <ErrorState
        title="Couldn't load the assessment"
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
    );
  }

  const hasItems = data.subjects.some((s) => s.kind !== "estate");
  const subject = data.subjects.find((s) => s.id === selected) ?? null;
  const questions: EstateQuestion[] = subject
    ? (data.questions[subject.kind] ?? [])
    : [];
  const answers = subject ? (data.answers[subject.id] ?? {}) : {};
  const groups = Array.from(new Set(questions.map((q) => q.group)));
  const scoreRead: EstateScoreRead | undefined = score.data;
  const noScoreYet =
    score.isError &&
    score.error instanceof ApiError &&
    score.error.code === "no_score";
  const answeredTotal = data.subjects.reduce((n, s) => n + s.answered, 0);

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div
          role="tablist"
          aria-label="Assessment view"
          className="flex gap-1 rounded-full border border-line-strong bg-paper-2 p-1"
        >
          {(
            [
              ["assess", "Assess"],
              ["results", "Score & gap register"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={view === key}
              onClick={() => setView(key)}
              className={`rounded-full px-4 py-1.5 font-sans text-[13px] font-medium transition-colors ${
                view === key
                  ? "bg-ink text-paper-on-ink"
                  : "text-muted hover:text-text"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {scoreRead && (
            <span className="font-mono text-[11px] uppercase text-muted-2">
              Last scored: version {scoreRead.version}
            </span>
          )}
          <button
            type="button"
            onClick={() => scoreMutation.mutate()}
            disabled={
              scoreMutation.isPending || (answeredTotal === 0 && !hasItems)
            }
            title="Compute the scores and the gap register from the inventory and the answers, and store them as a new version"
            className="rounded-full bg-ink px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink hover:bg-ink-2 disabled:opacity-50"
          >
            {scoreMutation.isPending ? "Scoring…" : copy.scoreLabel}
          </button>
        </div>
      </div>

      {view === "assess" && (
        <>
          {!hasItems && (
            <div className="mb-6">
              <EmptyState
                title="Nothing inventoried yet"
                description={copy.empty}
                action={
                  <Link
                    href={`/engagements/${engagementId}/irl`}
                    className="rounded-full border border-ink px-5 py-2.5 font-sans text-[13px] text-text"
                  >
                    Go to the request list
                  </Link>
                }
              />
            </div>
          )}
          {data.subjects.length > 0 && (
            <div className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
              <aside className="lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)] lg:self-start lg:overflow-y-auto">
                <SubjectList
                  subjects={data.subjects}
                  selected={selected}
                  onSelect={setSelected}
                />
              </aside>
              <div>
                {subject && (
                  <>
                    <header className="mb-4">
                      <p className="font-mono text-[11px] uppercase tracking-wide text-muted">
                        {subject.ref} · {KIND_LABELS[subject.kind]}
                      </p>
                      <h3 className="font-serif text-[26px] leading-tight text-ink">
                        {subject.name}
                      </h3>
                      {subject.subtitle && (
                        <p className="font-sans text-[13px] text-muted">
                          {subject.subtitle}
                        </p>
                      )}
                    </header>
                    <div className="space-y-7">
                      {groups.map((group) => (
                        <div key={group}>
                          {groups.length > 1 && GROUP_LABELS[group] && (
                            <p className="mb-2 font-mono text-[10.5px] uppercase tracking-wide text-muted">
                              {GROUP_LABELS[group]}
                            </p>
                          )}
                          <div className="space-y-3">
                            {questions
                              .filter((q) => q.group === group)
                              .map((q) => (
                                <QuestionCard
                                  key={`${subject.id}-${q.id}`}
                                  question={q}
                                  value={answers[q.id]?.value ?? ""}
                                  remarks={answers[q.id]?.remarks ?? ""}
                                  compact={
                                    q.options.length <= 4 &&
                                    q.options.every((o) => o.label.length < 48)
                                  }
                                  onPick={(value) =>
                                    void save(subject.id, q.id, {
                                      value,
                                    }).catch(() =>
                                      show(
                                        "Could not save that answer",
                                        "error",
                                      ),
                                    )
                                  }
                                  onRemarks={(questionId, patch) =>
                                    save(subject.id, questionId, patch)
                                  }
                                />
                              ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {view === "results" && (
        <>
          {score.isLoading && <Skeleton className="h-64 w-full" />}
          {noScoreYet && (
            <EmptyState
              title="Not scored yet"
              description="Answer what you can, then score. Unanswered questions are left out of the arithmetic, never counted as zero, and the coverage note says what the score rests on."
            />
          )}
          {score.isError && !noScoreYet && (
            <ErrorState title="Couldn't load the score" />
          )}
          {scoreRead && (
            <>
              <ScoreHeader
                payload={scoreRead.payload}
                version={scoreRead.version}
                indexLabel={copy.indexLabel}
              />
              {scoreRead.payload.domain === "applications" ? (
                <ApplicationResults payload={scoreRead.payload} />
              ) : (
                <DataTechResults payload={scoreRead.payload} />
              )}
              <h3 className="mb-4 font-serif text-[24px] text-ink">
                Gap register
              </h3>
              <GapRegister
                gaps={scoreRead.payload.gaps}
                onEdit={editGap}
                onRevert={revertGap}
              />
            </>
          )}
        </>
      )}
    </div>
  );
}
