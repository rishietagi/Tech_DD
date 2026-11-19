"use client";

import { useMemo, useState } from "react";

import { IrlRequestCard } from "@/components/engagement/irl-request-card";
import type { IrlPayload, IrlQuestion, IrlTracking } from "@/types/irl";

/**
 * The request list itself: requests grouped under their scope area, each group
 * collapsible, with filters across the top.
 *
 * Replaced the five-column table on 2026-09-09. Ninety requests in one flat table meant
 * a 1,500px horizontal scroll and no way to answer the question an analyst actually
 * arrives with — "what is still outstanding, and what do I have to chase?" The filters
 * answer it directly, and the grouping keeps the scope's own structure visible, which is
 * the thing that makes a request defensible: every one traces to an area the scope opened.
 */

type Filter =
  "all" | "outstanding" | "follow_ups" | "received" | "documents" | "questions";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "outstanding", label: "Outstanding" },
  { value: "follow_ups", label: "Needs follow-up" },
  { value: "received", label: "Received" },
  { value: "documents", label: "Documents" },
  { value: "questions", label: "Questions" },
];

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

/** Fold the spelling differences that otherwise make search lie.
 *
 *  The model writes the request list in US English ("license", "organization") while the
 *  team searching it is British, and the drive's own filenames are British too
 *  ("Software-Licence-Inventory-SAP.xlsx"). Typing "licence" returned nothing at all
 *  against nine matching requests, which reads as "we were never asked for that" rather
 *  than as a spelling miss. Cheaper and more honest than normalising the content. */
function fold(text: string): string {
  return text
    .toLowerCase()
    .replace(/(\w)ised\b/g, "$1ized")
    .replace(/(\w)isation/g, "$1ization")
    .replace(/(\w)ise\b/g, "$1ize")
    .replace(/licence/g, "license")
    .replace(/practise/g, "practice")
    .replace(/defence/g, "defense")
    .replace(/centre/g, "center")
    .replace(/cataloguing/g, "cataloging")
    .replace(/catalogue/g, "catalog")
    .replace(/programme/g, "program");
}

function matches(
  filter: Filter,
  question: IrlQuestion,
  tracking: IrlTracking | undefined,
): boolean {
  switch (filter) {
    case "outstanding":
      return !tracking || tracking.status !== "received_completely";
    case "follow_ups":
      return (tracking?.follow_up_questions.length ?? 0) > 0;
    case "received":
      return tracking?.status === "received_completely";
    case "documents":
      return question.kind === "document";
    case "questions":
      return question.kind === "question";
    default:
      return true;
  }
}

/** How much of one group has arrived — shown on the group header so a collapsed section
 *  still reports its state. */
function groupProgress(
  questions: IrlQuestion[],
  tracking: Record<string, IrlTracking>,
) {
  const received = questions.filter(
    (q) => tracking[q.id]?.status === "received_completely",
  ).length;
  const followUps = questions.reduce(
    (n, q) => n + (tracking[q.id]?.follow_up_questions.length ?? 0),
    0,
  );
  return { received, followUps };
}

export function IrlRequestList({
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
  const [filter, setFilter] = useState<Filter>("all");
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");

  const groups = useMemo(() => {
    const ordered = orderedQuestions(payload);
    const term = fold(search.trim());

    const visible = ordered.filter((question) => {
      if (!matches(filter, question, tracking[question.id])) return false;
      if (!term) return true;
      const track = tracking[question.id];
      // Searching the document type and the matched filenames too, so "licence" finds
      // the row the scan filed under Software-Licence-Inventory-SAP.xlsx.
      const haystack = fold(
        [
          question.question,
          question.function,
          question.scope_area ?? "",
          track?.document_type ?? "",
          ...(track?.matched_files ?? []),
        ].join(" "),
      );
      return haystack.includes(term);
    });

    const byArea = new Map<string, IrlQuestion[]>();
    for (const question of visible) {
      const area = question.scope_area || "Additional requests";
      const bucket = byArea.get(area);
      if (bucket) bucket.push(question);
      else byArea.set(area, [question]);
    }
    return Array.from(byArea.entries());
  }, [payload, tracking, filter, search]);

  const shown = groups.reduce((n, [, questions]) => n + questions.length, 0);

  return (
    <section>
      {/* ------------------------------------------------------------------ filters */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div
          className="flex flex-wrap items-center gap-1.5"
          role="group"
          aria-label="Filter requests"
        >
          {FILTERS.map((option) => {
            const active = filter === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setFilter(option.value)}
                aria-pressed={active}
                className={`rounded-full border px-3 py-1.5 font-sans text-[12.5px] font-medium transition-colors ${
                  active
                    ? "border-ink bg-ink text-paper-on-ink"
                    : "border-line-strong bg-paper text-muted hover:bg-paper-2 hover:text-text"
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>

        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search requests…"
          aria-label="Search requests"
          className="w-[240px] rounded-full border border-line-strong bg-paper px-4 py-1.5 font-sans text-[12.5px] text-text placeholder:text-muted-2 focus:border-steel focus:outline-none"
        />
      </div>

      {shown === 0 ? (
        <div className="rounded-2xl border border-dashed border-line-strong bg-paper-2/50 px-6 py-14 text-center">
          <p className="font-sans text-[14px] text-text">
            No requests match that filter.
          </p>
          <button
            type="button"
            onClick={() => {
              setFilter("all");
              setSearch("");
            }}
            className="mt-2 font-sans text-[13px] text-steel underline underline-offset-2"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {groups.map(([area, questions]) => {
            const isCollapsed = collapsed.has(area);
            const { received, followUps } = groupProgress(questions, tracking);

            return (
              <div
                key={area}
                className="overflow-hidden rounded-2xl border border-line-strong bg-paper"
              >
                <button
                  type="button"
                  onClick={() =>
                    setCollapsed((previous) => {
                      const next = new Set(previous);
                      if (next.has(area)) next.delete(area);
                      else next.add(area);
                      return next;
                    })
                  }
                  aria-expanded={!isCollapsed}
                  className="flex w-full items-center justify-between gap-4 border-b border-line-strong bg-paper-2 px-5 py-3 text-left transition-colors hover:bg-paper-3"
                >
                  <span className="flex min-w-0 items-center gap-2.5">
                    <span
                      aria-hidden
                      className={`font-mono text-[10px] text-muted-2 transition-transform ${
                        isCollapsed ? "" : "rotate-90"
                      }`}
                    >
                      ▸
                    </span>
                    <span className="truncate font-sans text-[13.5px] font-semibold text-kpmg-blue">
                      {area}
                    </span>
                  </span>
                  <span className="flex flex-none items-center gap-3 font-mono text-[10px] tracking-wide text-muted-2 uppercase">
                    {followUps > 0 && (
                      <span className="text-redline">
                        {followUps} follow-up
                      </span>
                    )}
                    <span>
                      {received}/{questions.length} in
                    </span>
                  </span>
                </button>

                {!isCollapsed && (
                  <div>
                    {questions.map((question) => (
                      <IrlRequestCard
                        key={question.id}
                        engagementId={engagementId}
                        question={question}
                        response={responses[question.id] ?? ""}
                        tracking={tracking[question.id]}
                        onUpdate={(patch) => onUpdate(question.id, patch)}
                        onDelete={() => onDelete(question.id)}
                        onTrack={(patch) => onTrack(question.id, patch)}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
