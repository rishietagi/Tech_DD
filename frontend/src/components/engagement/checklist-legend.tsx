import { PRIORITY_CLASSES } from "@/components/engagement/priority-badge";
import { PRIORITIES, PRIORITY_LABELS, PRIORITY_MEANINGS } from "@/types/checklist";

/** What each colour means. Required, not decoration — a four-colour ramp with no key
 *  is a guessing game. */
export function ChecklistLegend() {
  return (
    <div className="mb-5 rounded-xl border border-line bg-paper-2 px-4 py-3">
      <p className="mb-2 font-sans text-[11px] font-semibold tracking-[0.06em] text-muted-2 uppercase">
        Priority
      </p>
      <ul className="flex flex-wrap gap-x-6 gap-y-2">
        {PRIORITIES.map((priority) => (
          <li key={priority} className="flex items-center gap-2">
            <span
              className={`inline-block rounded-full px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase ${PRIORITY_CLASSES[priority]}`}
            >
              {PRIORITY_LABELS[priority]}
            </span>
            <span className="font-sans text-[12.5px] text-muted">
              {PRIORITY_MEANINGS[priority]}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
