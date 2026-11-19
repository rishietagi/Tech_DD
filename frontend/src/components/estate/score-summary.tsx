import { BandBadge } from "@/components/engagement/band-badge";
import { InfoTip } from "@/components/ui/info-tip";
import type { Band } from "@/types/assess";

/**
 * The top of every Assess result: the score, its band, and a short summary. Kept plain on
 * purpose (Rishi, 2026-11-19: "minimalistic") — one number, one word, a paragraph.
 */
export function ScoreSummary({
  label,
  explain,
  index,
  band,
  bandLabel,
  bandMeaning,
  summary,
  note,
  meta,
}: {
  label: string;
  explain: React.ReactNode;
  index: number | null;
  band: Band | null;
  bandLabel?: string;
  bandMeaning?: string;
  summary: string;
  note?: string | null;
  meta?: string;
}) {
  return (
    <section className="mb-10 grid gap-x-10 gap-y-4 border-b border-line pb-8 lg:grid-cols-[240px_minmax(0,1fr)]">
      <div>
        <p className="flex items-center font-sans text-[12px] font-medium text-muted">
          {label}
          <InfoTip label={label.toLowerCase()}>{explain}</InfoTip>
        </p>
        {index !== null && band ? (
          <>
            <p className="mt-1 font-display text-[52px] leading-none font-semibold text-ink tabular-nums">
              {index.toFixed(0)}
              <span className="ml-1 text-[18px] font-normal text-muted-2">
                /100
              </span>
            </p>
            <div className="mt-3">
              <BandBadge band={band} label={bandLabel} title={bandMeaning} />
            </div>
          </>
        ) : (
          <p className="mt-2 font-sans text-[14px] text-muted">
            Not enough evidence for a score yet.
          </p>
        )}
      </div>
      <div className="max-w-[78ch]">
        <p className="font-sans text-[15px] leading-[1.65] text-text">
          {summary}
        </p>
        {bandMeaning && (
          <p className="mt-3 font-sans text-[13.5px] leading-[1.55] text-muted">
            {bandMeaning}
          </p>
        )}
        {(note || meta) && (
          <p className="mt-3 font-sans text-[12px] text-muted-2">
            {[note, meta].filter(Boolean).join(" · ")}
          </p>
        )}
      </div>
    </section>
  );
}
