"use client";

import { useEffect, useRef, useState } from "react";

import { TextArea } from "@/components/ui/text-area";
import type { AssessmentRead, Nudge, ProcessStep, Question } from "@/types/assess";
import { nudgeApplies } from "@/types/assess";

/**
 * Debounce for free-text autosave. Long enough that a sentence is not written one PATCH
 * per keystroke, short enough that an analyst moving on to the next question has already
 * saved. Select answers save immediately — a click is a completed decision.
 */
const SAVE_DEBOUNCE_MS = 700;

type SaveState = "idle" | "saving" | "saved" | "error";

function SaveIndicator({ state }: { state: SaveState }) {
  if (state === "idle") return null;
  const text =
    state === "saving" ? "Saving…" : state === "saved" ? "Saved" : "Not saved — retry";
  return (
    <span
      role="status"
      className={`font-mono text-[11px] uppercase ${
        state === "error" ? "text-redline" : "text-muted-2"
      }`}
    >
      {text}
    </span>
  );
}

/** One free-text box that autosaves, used for text questions and for nudge follow-ups. */
function TextAnswer({
  questionId,
  value,
  placeholder,
  onSave,
}: {
  questionId: string;
  value: string;
  placeholder: string;
  onSave: (questionId: string, patch: { value?: string; remarks?: string }) => Promise<void>;
}) {
  const [draft, setDraft] = useState(value);
  const [state, setState] = useState<SaveState>("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // The last value we know the server holds. Guards against a stale re-render (the PATCH
  // returns the whole assessment) overwriting what is currently being typed.
  const committed = useRef(value);

  useEffect(() => {
    if (value !== committed.current) {
      committed.current = value;
      setDraft(value);
    }
  }, [value]);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const handleChange = (next: string) => {
    setDraft(next);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setState("saving");
      try {
        await onSave(questionId, { value: next });
        committed.current = next;
        setState("saved");
      } catch {
        setState("error");
      }
    }, SAVE_DEBOUNCE_MS);
  };

  return (
    <div>
      <TextArea
        rows={3}
        value={draft}
        placeholder={placeholder}
        onChange={(event) => handleChange(event.target.value)}
        aria-label={placeholder}
      />
      <div className="mt-1 flex justify-end">
        <SaveIndicator state={state} />
      </div>
    </div>
  );
}


/**
 * The consultant's note on the option they just picked.
 *
 * Rishi, 2026-09-02: the option alone is not the evidence. "Data ingested" is the answer;
 * *where from, by whom, how often* is what makes it defensible in a report.
 *
 * Appears only once an option is selected — a remark has no meaning before there is an
 * answer to qualify, and showing 20 empty boxes would bury the questionnaire.
 */
function RemarksBox({
  questionId,
  value,
  onSave,
}: {
  questionId: string;
  value: string;
  onSave: (questionId: string, patch: { value?: string; remarks?: string }) => Promise<void>;
}) {
  const [draft, setDraft] = useState(value);
  const [state, setState] = useState<SaveState>("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const committed = useRef(value);

  useEffect(() => {
    if (value !== committed.current) {
      committed.current = value;
      setDraft(value);
    }
  }, [value]);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const handleChange = (next: string) => {
    setDraft(next);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setState("saving");
      try {
        // Only `remarks` is sent, so saving a note never disturbs the selected option.
        await onSave(questionId, { remarks: next });
        committed.current = next;
        setState("saved");
      } catch {
        setState("error");
      }
    }, SAVE_DEBOUNCE_MS);
  };

  return (
    <div className="mt-3 border-l-2 border-line-strong pl-4">
      <p className="mb-1.5 font-mono text-[10px] uppercase tracking-wide text-muted">
        Remarks
      </p>
      <TextArea
        rows={2}
        value={draft}
        placeholder="What was said — systems named, volumes quoted, caveats given"
        onChange={(event) => handleChange(event.target.value)}
        aria-label="Remarks"
        className="min-h-0 text-[14px]"
      />
      <div className="mt-1 flex justify-end">
        <SaveIndicator state={state} />
      </div>
    </div>
  );
}

/**
 * A follow-up that appeared because of the answer above it.
 *
 * Visually subordinate and marked, so a reader can tell what the analyst was asked
 * because of something they said from what everyone is asked.
 */
function NudgeBlock({
  nudge,
  value,
  onSave,
}: {
  nudge: Nudge;
  value: string;
  onSave: (questionId: string, patch: { value?: string; remarks?: string }) => Promise<void>;
}) {
  return (
    <div className="mt-3 border-l-2 border-steel pl-4">
      <p className="mb-1 font-mono text-[10px] uppercase tracking-wide text-steel">
        Follow up
      </p>
      <p className="mb-2 font-sans text-[14px] leading-relaxed text-text">{nudge.ask}</p>
      <TextAnswer
        questionId={nudge.id}
        value={value}
        placeholder="Record what management said"
        onSave={onSave}
      />
    </div>
  );
}

function QuestionBlock({
  question,
  answers,
  remarks,
  onSave,
}: {
  question: Question;
  answers: Record<string, string>;
  remarks: Record<string, string>;
  onSave: (questionId: string, patch: { value?: string; remarks?: string }) => Promise<void>;
}) {
  const answer = answers[question.id] ?? "";
  const [selectState, setSelectState] = useState<SaveState>("idle");

  const chooseOption = async (label: string) => {
    // Clicking the selected option again clears it, so a mis-click is recoverable
    // without a separate control.
    const next = answer === label ? "" : label;
    setSelectState("saving");
    try {
      await onSave(question.id, { value: next });
      setSelectState("saved");
    } catch {
      setSelectState("error");
    }
  };

  const visibleNudges = question.nudges.filter((nudge) => nudgeApplies(nudge, answer));

  return (
    <div className="border-t border-line py-5 first:border-t-0">
      <div className="mb-3 flex items-baseline gap-3">
        <span className="font-mono text-[11px] text-muted-2">{question.id}</span>
        {question.is_custom && (
          <span className="rounded-full border border-line-strong px-2 py-0.5 font-mono text-[10px] uppercase text-muted">
            Added
          </span>
        )}
      </div>
      <p className="mb-3 font-sans text-[15px] leading-relaxed text-text">{question.text}</p>

      {question.type === "single_select" ? (
        <>
          <div role="radiogroup" aria-label={question.text} className="flex flex-col gap-1.5">
            {question.options.map((option) => {
              const selected = answer === option.label;
              return (
                <button
                  key={option.label}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => void chooseOption(option.label)}
                  className={`flex items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left font-sans text-[14px] transition-colors focus:outline-none focus-visible:border-steel ${
                    selected
                      ? "border-ink bg-paper-3 text-text"
                      : "border-line-strong bg-paper-2 text-muted hover:border-line-strong hover:text-text"
                  }`}
                >
                  <span
                    aria-hidden
                    className={`h-3 w-3 flex-none rounded-full border ${
                      selected ? "border-ink bg-ink" : "border-line-strong"
                    }`}
                  />
                  <span className="flex-1">{option.label}</span>
                </button>
              );
            })}
          </div>
          <div className="mt-1 flex justify-end">
            <SaveIndicator state={selectState} />
          </div>
          {answer && (
            <RemarksBox
              questionId={question.id}
              value={remarks[question.id] ?? ""}
              onSave={onSave}
            />
          )}
        </>
      ) : (
        <TextAnswer
          questionId={question.id}
          value={answer}
          placeholder="Record the response"
          onSave={onSave}
        />
      )}

      {visibleNudges.map((nudge) => (
        <NudgeBlock
          key={nudge.id}
          nudge={nudge}
          value={answers[nudge.id] ?? ""}
          onSave={onSave}
        />
      ))}
    </div>
  );
}

function AddQuestion({
  stepKey,
  onAdd,
}: {
  stepKey: string;
  onAdd: (stepKey: string, text: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setBusy(true);
    try {
      await onAdd(stepKey, trimmed);
      setText("");
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] text-muted transition-colors hover:border-ink hover:text-text"
      >
        + Add a question to this step
      </button>
    );
  }

  return (
    <div className="mt-4 rounded-xl border border-line-strong bg-paper-2 p-4">
      <label
        htmlFor={`add-${stepKey}`}
        className="mb-2 block font-mono text-[11px] uppercase text-muted"
      >
        New question
      </label>
      <TextArea
        id={`add-${stepKey}`}
        rows={2}
        value={text}
        placeholder="What else should be asked about this step?"
        onChange={(event) => setText(event.target.value)}
      />
      <p className="mt-2 font-sans text-[12px] text-muted">
        Added questions capture evidence but do not score — they have no place on the
        maturity ladder.
      </p>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={() => void submit()}
          disabled={busy || !text.trim()}
          className="rounded-full border border-ink bg-ink px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink disabled:opacity-40"
        >
          {busy ? "Adding…" : "Add question"}
        </button>
        <button
          type="button"
          onClick={() => { setOpen(false); setText(""); }}
          className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] text-muted"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function StepBlock({
  step,
  answers,
  remarks,
  onSave,
  onAdd,
}: {
  step: ProcessStep;
  answers: Record<string, string>;
  remarks: Record<string, string>;
  onSave: (questionId: string, patch: { value?: string; remarks?: string }) => Promise<void>;
  onAdd: (stepKey: string, text: string) => Promise<void>;
}) {
  const answered = step.questions.filter((q) => (answers[q.id] ?? "").trim()).length;

  return (
    <section className="mb-10 rounded-2xl border border-line-strong bg-paper p-6">
      <header className="mb-4 border-b border-line pb-4">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-3">
          <h2 className="font-serif text-[22px] text-ink">
            <span className="mr-3 font-mono text-[13px] text-muted-2">
              §{String(step.sn).padStart(2, "0")}
            </span>
            {step.title}
          </h2>
          <span className="font-mono text-[11px] uppercase text-muted-2">
            {step.weight}% weight · {answered}/{step.questions.length} answered
          </span>
        </div>
        <p className="max-w-[72ch] font-sans text-[14px] leading-relaxed text-muted">
          {step.intent}
        </p>
      </header>

      {step.questions.map((question) => (
        <QuestionBlock
          key={question.id}
          question={question}
          answers={answers}
          remarks={remarks}
          onSave={onSave}
        />
      ))}

      <AddQuestion stepKey={step.key} onAdd={onAdd} />
    </section>
  );
}

export function ProcessQuestionnaire({
  assessment,
  onSave,
  onAdd,
}: {
  assessment: AssessmentRead;
  onSave: (questionId: string, patch: { value?: string; remarks?: string }) => Promise<void>;
  onAdd: (stepKey: string, text: string) => Promise<void>;
}) {
  const answers: Record<string, string> = Object.fromEntries(
    Object.entries(assessment.answers).map(([id, a]) => [id, a.value]),
  );
  const remarks: Record<string, string> = Object.fromEntries(
    Object.entries(assessment.answers).map(([id, a]) => [id, a.remarks ?? ""]),
  );

  return (
    <div>
      {assessment.steps.map((step) => (
        <StepBlock
          key={step.key}
          step={step}
          answers={answers}
          remarks={remarks}
          onSave={onSave}
          onAdd={onAdd}
        />
      ))}
    </div>
  );
}
