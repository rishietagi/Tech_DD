import Link from "next/link";

export function Masthead({ right }: { right?: React.ReactNode }) {
  return (
    <header className="sticky top-0 z-40 flex items-center justify-between bg-ink px-7 py-4 text-paper-on-ink">
      <Link href="/" className="font-mono text-xs uppercase tracking-[0.14em]">
        <b>Tech Diligence</b> <span className="opacity-70">/ Desk</span>
      </Link>
      <nav className="flex items-center gap-6 font-mono text-xs uppercase tracking-[0.1em]">
        <Link href="/engagements" className="opacity-80 transition-opacity hover:opacity-100">
          Engagements
        </Link>
        <Link href="/about/methodology" className="opacity-80 transition-opacity hover:opacity-100">
          Methodology
        </Link>
        {right}
      </nav>
    </header>
  );
}
