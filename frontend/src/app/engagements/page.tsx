import Link from "next/link";

import { EngagementTable } from "@/components/engagement/engagement-table";

export default function EngagementsPage() {
  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <div className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">Engagements</div>
          <h1 className="font-display font-semibold text-3xl">The desk&apos;s open files</h1>
        </div>
        <Link
          href="/intake/new"
          className="rounded-full border border-kpmg-blue bg-kpmg-blue px-5 py-3 font-sans text-[13px] font-medium text-white transition-colors hover:border-kpmg-blue-dark hover:bg-kpmg-blue-dark"
        >
          Start an intake
        </Link>
      </div>

      <EngagementTable />
    </main>
  );
}
