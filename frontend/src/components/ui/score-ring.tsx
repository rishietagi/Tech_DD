import type { Band } from "@/types/assess";

/**
 * One colour scale for every 0-100 score, keyed to the five bands so a ring, a bar and a
 * badge for the same number always agree. Bands: ≤20, ≤40, ≤60, ≤80, above.
 */
export function bandOf(value: number): Band {
  if (value <= 20) return "manual";
  if (value <= 40) return "emerging";
  if (value <= 60) return "standardised";
  if (value <= 80) return "integrated";
  return "optimised";
}

const STROKE: Record<Band, string> = {
  manual: "var(--priority-critical)",
  emerging: "var(--priority-high)",
  standardised: "var(--kpmg-blue)",
  integrated: "var(--kpmg-blue-light)",
  optimised: "var(--status-received)",
};

const BG: Record<Band, string> = {
  manual: "bg-priority-critical",
  emerging: "bg-priority-high",
  standardised: "bg-kpmg-blue",
  integrated: "bg-kpmg-blue-light",
  optimised: "bg-status-received",
};

/** The fill class for a bar or meter showing `value` on 0-100. */
export function scoreFill(value: number | null): string {
  return value === null ? "bg-line" : BG[bandOf(value)];
}

const BEFORE: Record<Band, string> = {
  manual: "before:bg-priority-critical",
  emerging: "before:bg-priority-high",
  standardised: "before:bg-kpmg-blue",
  integrated: "before:bg-kpmg-blue-light",
  optimised: "before:bg-status-received",
};

/** The same scale for a `before:` accent strip (spelled out so Tailwind sees it). */
export function scoreBefore(value: number | null): string {
  return value === null ? "before:bg-paper-3" : BEFORE[bandOf(value)];
}

/** A circular gauge for a 0-100 index. */
export function ScoreRing({
  value,
  size = 112,
  label,
}: {
  value: number;
  size?: number;
  label?: string;
}) {
  const stroke = 9;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className="relative flex-none"
      style={{ width: size, height: size }}
      role="img"
      aria-label={label ?? `${pct.toFixed(0)} out of 100`}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--paper-3)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={STROKE[bandOf(pct)]}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct / 100)}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-[30px] leading-none font-semibold text-ink tabular-nums">
          {pct.toFixed(0)}
        </span>
        <span className="mt-0.5 font-sans text-[10.5px] text-muted-2">
          of 100
        </span>
      </div>
    </div>
  );
}
