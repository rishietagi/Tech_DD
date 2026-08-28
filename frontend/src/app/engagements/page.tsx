import Link from "next/link";

import { EngagementTable } from "@/components/engagement/engagement-table";

export default function EngagementsPage() {
  return (
    <main className="mx-auto max-w-[1120px] px-7 pt-12 pb-24">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <div className="mb-1 font-mono text-xs tracking-[0.16em] text-redline uppercase">Engagements</div>
          <h1 className="font-serif text-3xl font-medium">The desk&apos;s open files</h1>
        </div>
        <Link
          href="/intake/new"
          className="rounded-[3px] border border-ink bg-ink px-5 py-3 font-mono text-xs tracking-[0.08em] text-paper-on-ink uppercase transition-colors hover:border-redline-dark hover:bg-redline-dark"
        >
          Start an intake
        </Link>
      </div>

      <EngagementTable />
    </main>
  );
}
