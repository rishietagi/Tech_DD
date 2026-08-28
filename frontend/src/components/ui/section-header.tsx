export function SectionHeader({ num, title, hint }: { num: string; title: string; hint?: string }) {
  return (
    <div className="mb-5">
      <div className="mb-2 flex items-baseline gap-3">
        <span className="font-mono text-[13px] text-redline">§{num}</span>
        <h2 className="font-sans text-sm font-semibold tracking-[0.08em] text-text uppercase">{title}</h2>
      </div>
      {hint && <p className="max-w-[58ch] font-serif text-[15.5px] leading-[1.55] text-muted italic">{hint}</p>}
    </div>
  );
}
