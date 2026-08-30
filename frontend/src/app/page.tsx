import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { engagementsApi } from "@/lib/api/engagements";
import type { EngagementSummary } from "@/types/engagement";

async function getRecentEngagements(): Promise<EngagementSummary[] | null> {
  try {
    const response = await engagementsApi.list({ limit: 4 });
    return response.items;
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const recent = await getRecentEngagements();

  return (
    <main className="mx-auto max-w-[920px] px-8 pt-16 pb-24">
      <div className="mb-3 font-sans text-xs font-semibold tracking-[0.14em] text-kpmg-blue uppercase">
        Technology Due Diligence
      </div>
      <h1 className="mb-5 max-w-[18ch] font-display text-[clamp(32px,5vw,48px)] leading-[1.15] font-semibold tracking-[-0.01em] text-text">
        Put the deal on the record.
      </h1>
      <p className="mb-10 max-w-[56ch] font-sans text-[17px] leading-[1.6] text-muted">
        Capture the transaction, and let the intake become the cover sheet for the technical diligence file. What you
        answer shapes which workstreams the desk opens next.
      </p>

      <div className="mb-16 flex flex-wrap gap-3">
        <Link
          href="/intake/new"
          className="rounded-full bg-kpmg-blue px-7 py-3.5 font-sans text-[14px] font-medium text-white transition-colors hover:bg-kpmg-blue-dark"
        >
          Start an intake
        </Link>
        <Link
          href="/engagements"
          className="rounded-full border border-line-strong bg-transparent px-7 py-3.5 font-sans text-[14px] font-medium text-text transition-colors hover:bg-paper-2"
        >
          View engagements
        </Link>
        <Link
          href="/about/methodology"
          className="rounded-full border border-transparent bg-transparent px-7 py-3.5 font-sans text-[14px] font-medium text-muted transition-colors hover:text-text"
        >
          Read the methodology
        </Link>
      </div>

      <section aria-labelledby="recent-heading" className="border-t border-line pt-8">
        <h2 id="recent-heading" className="mb-4 font-sans text-xs font-semibold tracking-[0.1em] text-muted uppercase">
          Recent engagements
        </h2>

        {recent === null && (
          <EmptyState
            title="Can't reach the API right now"
            description="Start the backend (uvicorn app.main:app --reload) to see recent engagements here."
          />
        )}

        {recent !== null && recent.length === 0 && (
          <EmptyState title="No engagements yet" description="Start an intake to create the first one." />
        )}

        {recent !== null && recent.length > 0 && (
          <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {recent.map((engagement) => (
              <li key={engagement.id}>
                <Link
                  href={`/engagements/${engagement.id}`}
                  className="block rounded-2xl border border-line bg-paper-2 px-5 py-4 transition-colors hover:bg-paper-3"
                >
                  <div className="mb-1.5 flex items-center justify-between gap-2">
                    <span className="font-sans text-[15px] font-semibold">{engagement.deal_name}</span>
                    <Badge tone={engagement.status === "filed" || engagement.status === "scoped" ? "steel" : "neutral"}>
                      {engagement.status}
                    </Badge>
                  </div>
                  <span className="font-sans text-[13px] text-muted italic">
                    {engagement.denorm?.company_name ?? "Target not yet named"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
