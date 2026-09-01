import type { Priority } from "@/types/checklist";
import { PRIORITY_LABELS } from "@/types/checklist";

/** Colour and tint per level. Kept here so the badge and the legend cannot drift. */
export const PRIORITY_CLASSES: Record<Priority, string> = {
  critical: "bg-priority-critical-tint text-priority-critical",
  high: "bg-priority-high-tint text-priority-high",
  medium: "bg-priority-medium-tint text-priority-medium",
  low: "bg-priority-low-tint text-priority-low",
};

export function PriorityBadge({ priority, reason }: { priority: Priority; reason?: string }) {
  return (
    <span
      // The reason is the tooltip: a colour with no explanation is not auditable, and a
      // consultant should be able to disagree with a ranking on stated grounds.
      title={reason}
      className={`inline-block flex-none rounded-full px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase ${PRIORITY_CLASSES[priority]}`}
    >
      {PRIORITY_LABELS[priority]}
    </span>
  );
}
