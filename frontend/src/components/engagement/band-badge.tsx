import type { Band } from "@/types/assess";
import { BAND_LABELS } from "@/types/assess";

/**
 * The band as a word with a small dot (Rishi, 2026-11-19: minimal, no loud colour). The dot
 * reuses the priority/status ramp: low maturity in the problem colour, high in the "good"
 * green already reserved for "arrived". No raw hex in components (CLAUDE.md §8).
 */
const BAND_DOT: Record<Band, string> = {
  manual: "bg-priority-critical",
  emerging: "bg-priority-high",
  standardised: "bg-kpmg-blue",
  integrated: "bg-kpmg-blue-light",
  optimised: "bg-status-received",
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
      className="inline-flex items-center gap-1.5 rounded-full border border-line-strong px-2.5 py-0.5 font-sans text-[12px] font-medium text-text"
    >
      <span className={`h-2 w-2 rounded-full ${BAND_DOT[band]}`} aria-hidden />
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
      <span className="font-sans text-[12px] text-muted-2">Not assessed</span>
    );
  }
  const filled = Math.round(score);
  return (
    <span className="inline-flex items-center gap-2" aria-hidden>
      <span className="flex gap-[3px]">
        {[1, 2, 3, 4, 5].map((rung) => (
          <span
            key={rung}
            className={`h-3 w-[6px] rounded-[1px] ${rung <= filled ? "bg-ink" : "bg-paper-3"}`}
          />
        ))}
      </span>
      <span className="font-mono text-[12px] text-text">
        {score.toFixed(1)}
      </span>
    </span>
  );
}
