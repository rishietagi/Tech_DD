"use client";

import { useState } from "react";

import { IrlResponseCell } from "@/components/engagement/irl-response-cell";
import { IrlTrackingCell } from "@/components/engagement/irl-tracking-cell";
import { PriorityBadge } from "@/components/engagement/priority-badge";
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import type { IrlQuestion, IrlTracking } from "@/types/irl";

/**
 * One request, as a card rather than a table row.
 *
 * The table this replaced was five columns and 1,500px wide, and the shared-drive scan
 * then added follow-up questions, matched filenames and a reasoning line to every row.
 * A sixth column would have made a horizontal scrollbar the primary navigation.
 *
 * The card puts the request and its response on the left, where reading happens, and the
 * team's own tracking on the right, where deciding happens. The scan's evidence — which
 * files it matched, why it called the status what it did — collapses behind a toggle,
 * because it is the thing you check when you disagree, not the thing you read every time.
 * The follow-up questions do not collapse: they are the output of the scan and the reason
 * to look at the row at all.
 */

const SOURCE_LABEL: Record<string, string> = {
  scope: "From the scope",
  llm: "Added by the model",
  manual: "Added by hand",
};

function KindBadge({ kind }: { kind: IrlQuestion["kind"] }) {
  const isQuestion = kind === "question";
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 font-mono text-[9.5px] font-semibold tracking-wide uppercase ${
        isQuestion
          ? "border-steel/50 bg-steel-tint text-steel"
          : "border-line-strong bg-paper-2 text-muted"
      }`}
    >
      {isQuestion ? "Question" : "Document"}
    </span>
  );
}

/** Follow-up questions the scan raised. Never collapsed — this is what to act on. */
function FollowUps({ questions }: { questions: string[] }) {
  return (
    <div className="mt-3 rounded-lg border border-redline/25 bg-redline-tint px-3.5 py-3">
      <p className="mb-1.5 font-mono text-[9.5px] font-semibold tracking-[0.08em] text-redline uppercase">
        Follow up{questions.length > 1 ? ` · ${questions.length}` : ""}
      </p>
      <ul className="space-y-1.5">
        {questions.map((question) => (
          <li
            key={question}
            className="font-sans text-[12.5px] leading-[1.55] text-text before:mr-1.5 before:text-redline before:content-['—']"
          >
            {question}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** What the scan matched and why. Collapsed: checked on disagreement, not on every read. */
function ScanEvidence({ tracking }: { tracking: IrlTracking }) {
  const [open, setOpen] = useState(false);
  if (tracking.matched_files.length === 0 && !tracking.scan_reasoning) return null;

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="font-mono text-[9.5px] tracking-wide text-muted-2 uppercase transition-colors hover:text-steel"
      >
        {open ? "▾" : "▸"} Why this status
      </button>
      {open && (
        <div className="mt-1.5 space-y-1 border-l-2 border-line pl-2.5">
          {tracking.matched_files.map((file) => (
            <p key={file} className="font-mono text-[10px] break-all text-muted-2">
              {file}
            </p>
          ))}
          {tracking.scan_reasoning && (
            <p className="font-sans text-[11.5px] leading-[1.45] text-muted italic">
              {tracking.scan_reasoning}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function IrlRequestCard({
  engagementId,
  question,
  response,
  tracking,
  onUpdate,
  onDelete,
  onTrack,
}: {
  engagementId: string;
  question: IrlQuestion;
  response: string;
  tracking?: IrlTracking;
  onUpdate: (patch: { question?: string; function?: string }) => Promise<void>;
  onDelete: () => Promise<void>;
  onTrack: (patch: {
    status?: IrlTracking["status"];
    document_type?: string;
    remarks?: string;
  }) => Promise<void>;
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
      await onUpdate({ question: draft.trim(), function: fn.trim() || undefined });
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

  // A left edge coloured by status turns a long list into something scannable without
  // reading a word of it.
  const edge =
    tracking?.status === "received_completely"
      ? "border-l-status-received"
      : tracking?.status === "received_partially"
        ? "border-l-status-partial"
        : "border-l-line-strong";

  return (
    <article
      className={`group grid grid-cols-1 gap-x-6 gap-y-4 border-l-[3px] ${edge} border-b border-b-line bg-paper px-5 py-4 transition-colors last:border-b-0 hover:bg-paper-2/40 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)_minmax(0,0.95fr)]`}
    >
      {/* ---------------------------------------------------------------- the request */}
      <div className="min-w-0">
        <div className="mb-2 flex flex-wrap items-center gap-1.5">
          <KindBadge kind={question.kind} />
          {tracking && (
            <PriorityBadge priority={tracking.priority} reason={tracking.priority_reason} />
          )}
          <span className="font-mono text-[9.5px] tracking-wide text-muted-2 uppercase">
            {question.function}
          </span>
        </div>

        {editing ? (
          <div>
            <TextArea
              rows={3}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              aria-label="Question text"
            />
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <label
                className="font-mono text-[10px] text-muted uppercase"
                htmlFor={`fn-${question.id}`}
              >
                Function
              </label>
              <TextInput
                id={`fn-${question.id}`}
                value={fn}
                onChange={(event) => setFn(event.target.value)}
                className="max-w-[200px]"
              />
              <button
                type="button"
                onClick={() => void save()}
                disabled={busy}
                className="rounded-full bg-ink px-3.5 py-1.5 font-sans text-[12px] font-medium text-paper-on-ink disabled:opacity-50"
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
                className="font-sans text-[12px] text-muted"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <p className="font-sans text-[14px] leading-[1.6] text-text">
              {question.question}
            </p>

            <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="font-mono text-[9.5px] text-muted-2">
                {question.id}
                {question.source && SOURCE_LABEL[question.source]
                  ? ` · ${SOURCE_LABEL[question.source]}`
                  : ""}
              </span>
              {/* Row actions stay hidden until the row is hovered or focused, so 90 rows
                  do not read as 180 buttons. */}
              <span className="flex items-center gap-2 opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100">
                <button
                  type="button"
                  onClick={() => setEditing(true)}
                  className="font-sans text-[11.5px] text-steel underline-offset-2 hover:underline"
                >
                  Edit
                </button>
                {confirming ? (
                  <>
                    <button
                      type="button"
                      onClick={() => void remove()}
                      disabled={busy}
                      className="font-sans text-[11.5px] font-semibold text-redline underline-offset-2 hover:underline disabled:opacity-40"
                    >
                      {busy ? "Removing…" : "Confirm"}
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
          </>
        )}

        {tracking && tracking.follow_up_questions.length > 0 && (
          <FollowUps questions={tracking.follow_up_questions} />
        )}
      </div>

      {/* --------------------------------------------------------------- the response */}
      <div className="min-w-0">
        <p className="mb-1.5 font-mono text-[9.5px] tracking-[0.08em] text-muted-2 uppercase">
          Client response
        </p>
        <IrlResponseCell
          engagementId={engagementId}
          questionId={question.id}
          initialValue={response}
        />
      </div>

      {/* ------------------------------------------------- the team's own assessment */}
      <div className="min-w-0">
        <p className="mb-1.5 font-mono text-[9.5px] tracking-[0.08em] text-muted-2 uppercase">
          Internal tracking
        </p>
        {tracking && (
          <>
            <IrlTrackingCell tracking={tracking} kind={question.kind} onSave={onTrack} />
            <ScanEvidence tracking={tracking} />
          </>
        )}
      </div>
    </article>
  );
}
