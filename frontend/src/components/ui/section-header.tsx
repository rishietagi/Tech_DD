export function SectionHeader({ num, title, hint }: { num: string; title: string; hint?: string }) {
  return (
    <div className="mb-6">
      <div className="mb-2 flex items-baseline gap-2.5">
        <span className="font-sans text-[13px] font-semibold text-kpmg-blue">{num}</span>
        <h2 className="font-display text-xl font-semibold text-text">{title}</h2>
      </div>
      {hint && <p className="max-w-[58ch] font-sans text-[15px] leading-[1.55] text-muted">{hint}</p>}
    </div>
  );
}
