"use client";

import { useState } from "react";

import { IrlResponseCell } from "@/components/engagement/irl-response-cell";
import { IrlTrackingCell } from "@/components/engagement/irl-tracking-cell";
import { PriorityBadge } from "@/components/engagement/priority-badge";
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import type { IrlPayload, IrlQuestion, IrlTracking } from "@/types/irl";

/** Questions in grouping order, falling back to payload order.
 *
 * Mirrors `_ordered_questions` in the Excel exporter so the screen and the workbook
 * agree. A question missing from the grouping must still render — losing a request
 * silently would be worse than an imperfect order. */
function orderedQuestions(payload: IrlPayload): IrlQuestion[] {
  const byId = new Map(payload.questions.map((q) => [q.id, q]));
  const ordered: IrlQuestion[] = [];
  const seen = new Set<string>();

  for (const group of payload.functions) {
    for (const id of group.question_ids) {
      const question = byId.get(id);
      if (question && !seen.has(id)) {
        ordered.push(question);
        seen.add(id);
      }
    }
  }
  for (const question of payload.questions) {
    if (!seen.has(question.id)) {
      ordered.push(question);
      seen.add(question.id);
    }
  }
  return ordered;
}

/** Document or question, shown on the row.
 *
 *  The client needs to know which before they start — one goes to whoever pulls files,
 *  the other to whoever can answer it. */
function KindBadge({ kind }: { kind: IrlQuestion["kind"] }) {
  const isQuestion = kind === "question";
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 font-sans text-[10px] font-semibold uppercase ${
        isQuestion
          ? "border-steel bg-steel-tint text-steel"
          : "border-line-strong bg-paper-2 text-muted"
      }`}
    >
      {isQuestion ? "Question" : "Document"}
    </span>
  );
}

const SOURCE_LABEL: Record<string, string> = {
  scope: "From the scope",
  llm: "Added by the model",
  manual: "Added by hand",
};

/** One question cell, switching between reading and editing in place. */
function QuestionCell({
  question,
  onSave,
  onDelete,
}: {
  question: IrlQuestion;
  onSave: (patch: { question?: string; function?: string }) => Promise<void>;
  onDelete: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(question.question);
  const [fn, setFn] = useState(question.function);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const save = async () => {
    if (!draft.trim()) return;
    setBusy(true);
    try {
      await onSave({ question: draft.trim(), function: fn.trim() || undefined });
      setEditing(false);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      await onDelete();
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  if (editing) {
    return (
      <div>
        <TextArea
          rows={3}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          aria-label="Question text"
        />
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <label className="font-mono text-[10px] uppercase text-muted" htmlFor={`fn-${question.id}`}>
            Function
          </label>
          <TextInput
            id={`fn-${question.id}`}
            value={fn}
            onChange={(event) => setFn(event.target.value)}
            className="max-w-[200px]"
          />
        </div>
        <div className="mt-2 flex gap-2">
          <button
            type="button"
            onClick={() => void save()}
            disabled={busy || !draft.trim()}
            className="rounded-full bg-kpmg-blue px-3.5 py-1.5 font-sans text-[12px] font-medium text-paper-on-ink disabled:opacity-40"
          >
            {busy ? "Saving…" : "Save"}
          </button>
          <button
            type="button"
            onClick={() => {
              setDraft(question.question);
              setFn(question.function);
              setEditing(false);
            }}
            className="rounded-full border border-line-strong px-3.5 py-1.5 font-sans text-[12px] text-muted"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="group/q">
      <p className="font-sans text-[14px] leading-[1.55] text-text">{question.question}</p>

      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-sans text-[11.5px] text-muted-2">
          {SOURCE_LABEL[question.source] ?? question.source}
        </span>
        {question.citation && (
          <span className="font-mono text-[11px] text-muted-2" title="Source of this question">
            {question.citation}
          </span>
        )}
        {question.edited_by_human && (
          <span
            className="font-sans text-[11.5px] text-steel"
            title={
              question.original_question
                ? `Originally: ${question.original_question}`
                : undefined
            }
          >
            Edited by hand
          </span>
        )}

        {/* Controls stay quiet until the row is hovered or focused, so a long list reads
            as a document rather than a form. */}
        <span className="opacity-0 transition-opacity group-hover/q:opacity-100 focus-within:opacity-100">
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="mr-2 font-sans text-[11.5px] text-kpmg-blue underline-offset-2 hover:underline"
          >
            Edit
          </button>
          {confirming ? (
            <>
              <button
                type="button"
                onClick={() => void remove()}
                disabled={busy}
                className="mr-1 font-sans text-[11.5px] font-semibold text-redline underline-offset-2 hover:underline disabled:opacity-40"
              >
                {busy ? "Removing…" : "Confirm delete"}
              </button>
              <button
                type="button"
                onClick={() => setConfirming(false)}
                className="font-sans text-[11.5px] text-muted"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setConfirming(true)}
              className="font-sans text-[11.5px] text-redline underline-offset-2 hover:underline"
            >
              Delete
            </button>
          )}
        </span>
      </div>
    </div>
  );
}

export function IrlTable({
  engagementId,
  payload,
  responses,
  tracking,
  onUpdate,
  onDelete,
  onTrack,
}: {
  engagementId: string;
  payload: IrlPayload;
  responses: Record<string, string>;
  /** What the deal team observes about each document. Never exported to the client. */
  tracking: Record<string, IrlTracking>;
  onUpdate: (
    questionId: string,
    patch: { question?: string; function?: string; scope_area?: string },
  ) => Promise<void>;
  onDelete: (questionId: string) => Promise<void>;
  onTrack: (
    questionId: string,
    patch: {
      status?: IrlTracking["status"];
      document_type?: string;
      remarks?: string;
    },
  ) => Promise<void>;
}) {
  const questions = orderedQuestions(payload);

  return (
    <div className="overflow-x-auto rounded-2xl border border-line-strong">
      <table className="w-full min-w-[1500px] border-collapse">
        <thead>
          <tr className="border-b border-line-strong bg-paper-2 text-left">
            <th className="w-[12%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Scope area
            </th>
            <th className="w-[9%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Function
            </th>
            <th className="w-[31%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Request
            </th>
            <th className="w-[24%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Response
            </th>
            {/* Internal. Deliberately absent from the exported workbook — status and
                remarks are the team's assessment, not something the client should read. */}
            <th className="w-[24%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Status &amp; remarks
            </th>
          </tr>
        </thead>
        <tbody>
          {questions.map((question, index) => {
            // A scope-area label on the first row of each run, so a long list stays
            // readable without repeating the same heading down the column.
            const area = question.scope_area || "Additional requests";
            const previousArea =
              index === 0
                ? null
                : questions[index - 1].scope_area || "Additional requests";
            const isFirstOfArea = area !== previousArea;
            const track = tracking[question.id];

            return (
              <tr
                key={question.id}
                className={`border-b border-line last:border-b-0 ${
                  isFirstOfArea ? "border-t-2 border-t-line-strong" : ""
                }`}
              >
                <td className="px-4 py-3 align-top">
                  {isFirstOfArea && (
                    <span className="font-sans text-[13px] font-semibold text-kpmg-blue">
                      {area}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 align-top">
                  <span className="font-sans text-[13px] text-muted">{question.function}</span>
                </td>
                <td className="px-4 py-3 align-top">
                  <div className="mb-1.5 flex flex-wrap items-center gap-2">
                    <KindBadge kind={question.kind} />
                    {track && (
                      <PriorityBadge
                        priority={track.priority}
                        reason={track.priority_reason}
                      />
                    )}
                  </div>
                  <QuestionCell
                    question={question}
                    onSave={(patch) => onUpdate(question.id, patch)}
                    onDelete={() => onDelete(question.id)}
                  />
                </td>
                <td className="px-4 py-3 align-top">
                  <IrlResponseCell
                    engagementId={engagementId}
                    questionId={question.id}
                    initialValue={responses[question.id] ?? ""}
                  />
                </td>
                <td className="px-4 py-3 align-top">
                  {track && (
                    <IrlTrackingCell
                      tracking={track}
                      kind={question.kind}
                      onSave={(patch) => onTrack(question.id, patch)}
                    />
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
