import type { Band } from "@/types/assess";
import { BAND_LABELS } from "@/types/assess";
import { scoreFill } from "@/components/ui/score-ring";

/**
 * The five maturity bands reuse the existing priority/status ramp rather than adding a
 * sixth palette: low maturity reads as the problem colour, high maturity as the "good"
 * green already reserved for "arrived". No raw hex in components (CLAUDE.md §8).
 */
const BAND_CLASSES: Record<Band, string> = {
  manual:
    "border-priority-critical bg-priority-critical-tint text-priority-critical",
  emerging: "border-priority-high bg-priority-high-tint text-priority-high",
  standardised:
    "border-priority-medium bg-priority-medium-tint text-priority-medium",
  integrated: "border-steel bg-steel-tint text-steel",
  optimised:
    "border-status-received bg-status-received-tint text-status-received",
};

export function BandBadge({
  band,
  title,
  label,
}: {
  band: Band;
  title?: string;
  /** Overrides the automation wording — maturity indices say "Initial", not "Manual". */
  label?: string;
}) {
  return (
    <span
      title={title}
      className={`inline-block rounded-full border px-2.5 py-0.5 font-sans text-[11px] font-semibold uppercase ${BAND_CLASSES[band]}`}
    >
      {label || BAND_LABELS[band]}
    </span>
  );
}

/**
 * The 0-5 ladder position for one step, as a small filled meter.
 *
 * A number alone makes a reader do the comparison; the meter makes the shape of the
 * cycle legible down a column, which is the thing the model document says matters most.
 */
export function LadderMeter({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <span className="font-mono text-[11px] uppercase text-muted-2">
        Not assessed
      </span>
    );
  }
  const filled = Math.round(score);
  return (
    <span className="inline-flex items-center gap-2" aria-hidden>
      <span className="flex gap-[3px]">
        {[1, 2, 3, 4, 5].map((rung) => (
          <span
            key={rung}
            className={`h-3.5 w-[7px] rounded-[1px] ${
              rung <= filled ? scoreFill(score * 20) : "bg-paper-3"
            }`}
          />
        ))}
      </span>
      <span className="font-mono text-[12px] text-text">
        {score.toFixed(1)}
      </span>
    </span>
  );
}
