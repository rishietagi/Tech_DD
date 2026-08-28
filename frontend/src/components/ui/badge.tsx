type BadgeTone = "neutral" | "redline" | "steel";

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "border-line-strong text-muted",
  redline: "border-redline text-redline",
  steel: "border-steel text-steel",
};

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: React.ReactNode }) {
  return (
    <span
      className={`inline-block rounded-[2px] border px-2 py-0.5 font-mono text-[10.5px] tracking-[0.08em] uppercase ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
