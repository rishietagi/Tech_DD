import { IrlResponseCell } from "@/components/engagement/irl-response-cell";
import type { IrlPayload, IrlQuestion } from "@/types/irl";

/** Questions in function order, falling back to payload order.
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

export function IrlTable({
  engagementId,
  payload,
  responses,
}: {
  engagementId: string;
  payload: IrlPayload;
  responses: Record<string, string>;
}) {
  const questions = orderedQuestions(payload);

  return (
    <div className="overflow-x-auto rounded-2xl border border-line-strong">
      <table className="w-full min-w-[960px] border-collapse">
        <thead>
          <tr className="border-b border-line-strong bg-paper-2 text-left">
            <th className="w-[16%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Function
            </th>
            <th className="w-[52%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Question
            </th>
            <th className="w-[32%] px-4 py-3 font-sans text-[11px] font-semibold text-muted uppercase">
              Response
            </th>
          </tr>
        </thead>
        <tbody>
          {questions.map((question, index) => {
            // A function label on the first row of each run, so a long list stays
            // readable without repeating the same word down the column.
            const isFirstOfFunction =
              index === 0 || questions[index - 1].function !== question.function;

            return (
              <tr
                key={question.id}
                className={`border-b border-line last:border-b-0 ${
                  isFirstOfFunction ? "border-t-2 border-t-line-strong" : ""
                }`}
              >
                <td className="px-4 py-3 align-top">
                  {isFirstOfFunction && (
                    <span className="font-sans text-[13px] font-semibold text-kpmg-blue">
                      {question.function}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 align-top">
                  <p className="font-sans text-[14px] leading-[1.55] text-text">
                    {question.question}
                  </p>
                  {question.source_row_title && (
                    <p className="mt-1 font-sans text-[11.5px] text-muted-2">
                      From scope area: {question.source_row_title}
                    </p>
                  )}
                </td>
                <td className="px-4 py-3 align-top">
                  <IrlResponseCell
                    engagementId={engagementId}
                    questionId={question.id}
                    initialValue={responses[question.id] ?? ""}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
