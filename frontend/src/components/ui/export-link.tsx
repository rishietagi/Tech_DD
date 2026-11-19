/**
 * A download, styled as a quiet button. Everything exportable in the platform is edited in
 * place first, so the file always carries the edits (Rishi, 2026-11-19).
 */
export function ExportLink({
  href,
  label,
  primary = false,
}: {
  href: string;
  label: string;
  primary?: boolean;
}) {
  return (
    <a
      href={href}
      download
      className={`inline-flex items-center gap-2 rounded-full px-4 py-2 font-sans text-[13px] font-medium whitespace-nowrap transition-colors ${
        primary
          ? "bg-ink text-paper-on-ink hover:bg-ink-2"
          : "border border-line-strong text-text hover:border-ink"
      }`}
    >
      <svg aria-hidden viewBox="0 0 16 16" className="h-3.5 w-3.5">
        <path
          d="M8 2v8m0 0 3-3m-3 3L5 7M3 12.5h10"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {label}
    </a>
  );
}
