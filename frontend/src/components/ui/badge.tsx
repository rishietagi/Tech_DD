type BadgeTone = "neutral" | "redline" | "steel";

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "border-line-strong text-muted",
  redline: "border-redline text-redline",
  steel: "border-steel text-steel",
};

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: React.ReactNode }) {
  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-0.5 font-sans text-[11px] font-semibold uppercase ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
