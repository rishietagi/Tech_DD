"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { BandBadge } from "@/components/engagement/band-badge";
import { EstateAssessment } from "@/components/estate/estate-assessment";
import { ItBudgetPage } from "@/app/engagements/[id]/it-budget/it-budget-page";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { assessApi } from "@/lib/api/assess";
import { estateApi } from "@/lib/api/estate";
import type { ProcessSummary } from "@/types/assess";
import type { EstateSummaryEntry } from "@/types/estate";

type Tab =
  | "business"
  | "applications"
  | "data_tech"
  | "team_governance"
  | "strategy_projects"
  | "budget";

const TABS: { key: Tab; label: string; blurb: string }[] = [
  {
    key: "business",
    label: "Business processes",
    blurb:
      "How much of the work still needs a person. Licences reveal what was bought; process automation reveals what is used, and the gap between the two is where diligence findings live. Each process is assessed step by step and scored on a 0–100 automation index.",
  },
  {
    key: "applications",
    label: "Applications",
    blurb:
      "Each inventoried application rated for criticality, automation and AI, and four questions on the landscape as a whole. The findings are about what the landscape means for the deal — end-of-support exposure, integration, overlap, unused capability — not a verdict on each system.",
  },
  {
    key: "data_tech",
    label: "Data & infrastructure",
    blurb:
      "Whether the data is governed well enough to trust, and whether the infrastructure underneath stays supported, recoverable and secure through the hold — per data domain, per platform, and across the estate. The cyber tools checklist sits beside the checks as evidence; a tool is not a control.",
  },
  {
    key: "team_governance",
    label: "Team & governance",
    blurb:
      "Who runs IT and how it is governed: leadership and accountability, decision forums, capacity against the plan, and what breaks if one person leaves. Key-person dependencies are counted from the IT team sheet; the rest is the analyst's judgement from the management interview.",
  },
  {
    key: "strategy_projects",
    label: "Strategy & projects",
    blurb:
      "Is there a technology strategy, is it funded, and are the projects in flight delivering it? Projects are measured on the target's own figures — spend against allocation, progress, dates — and the roadmap is reconciled against the change budget. AI strategy and governance sit here too.",
  },
  {
    key: "budget",
    label: "IT budget",
    blurb:
      "How the technology budget is built, approved and controlled, and where reported spend landed against it over the review period. A budgeting-process review — it does not build, validate or benchmark a cost model, and it shows no share of revenue.",
  },
];

const ESTATE_TABS = new Set<Tab>([
  "applications",
  "data_tech",
  "team_governance",
  "strategy_projects",
]);

function TabMeta({ entry }: { entry: EstateSummaryEntry | undefined }) {
  if (!entry) return null;
  if (entry.has_score && entry.index !== null) {
    return (
      <span className="ml-2 font-mono text-[11px] opacity-70">
        {entry.index.toFixed(0)} · {entry.gap_count} findings
      </span>
    );
  }
  return (
    <span className="ml-2 font-mono text-[11px] opacity-60">{entry.items}</span>
  );
}

function ProcessCard({
  engagementId,
  process,
}: {
  engagementId: string;
  process: ProcessSummary;
}) {
  const progress =
    process.question_count > 0
      ? Math.round((process.answered_count / process.question_count) * 100)
      : 0;

  // A process with no questionnaire is shown, not hidden — the shape of the module
  // should be visible — but it is plainly not a link and says why.
  if (!process.defined) {
    return (
      <div className="rounded-2xl border border-dashed border-line-strong bg-paper-2 p-6">
        <div className="mb-2 flex items-baseline gap-3">
          <span className="font-mono text-[12px] text-muted-2">
            {process.short_name}
          </span>
          <h2 className="font-serif text-[20px] text-muted">{process.name}</h2>
        </div>
        <p className="mb-4 max-w-[52ch] font-sans text-[14px] leading-relaxed text-muted-2">
          {process.description}
        </p>
        <span className="rounded-full border border-line-strong px-3 py-1 font-mono text-[10px] uppercase tracking-wide text-muted-2">
          Not yet defined
        </span>
      </div>
    );
  }

  return (
    <Link
      href={`/engagements/${engagementId}/assess/${process.key}`}
      className="block rounded-2xl border border-line-strong bg-paper p-6 transition-colors hover:border-ink focus:outline-none focus-visible:border-steel"
    >
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-[12px] text-muted-2">
            {process.short_name}
          </span>
          <h2 className="font-serif text-[20px] text-ink">{process.name}</h2>
        </div>
        {process.has_score && process.band && process.index !== null && (
          <div className="flex items-center gap-3">
            <span className="font-mono text-[13px] text-text">
              {process.index.toFixed(1)}/100
            </span>
            <BandBadge band={process.band} />
          </div>
        )}
      </div>

      <p className="mb-5 max-w-[52ch] font-sans text-[14px] leading-relaxed text-muted">
        {process.description}
      </p>

      <div className="flex items-center gap-3">
        <div
          className="h-1.5 flex-1 overflow-hidden rounded-full bg-paper-3"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${process.name} questionnaire progress`}
        >
          <div
            className="h-full rounded-full bg-ink"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="font-mono text-[11px] uppercase text-muted-2">
          {process.answered_count}/{process.question_count} answered
        </span>
      </div>
    </Link>
  );
}

export function AssessIndexPage({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const raw = params.get("tab");
  const tab: Tab = TABS.some((t) => t.key === raw) ? (raw as Tab) : "business";
  const setTab = (next: Tab) => {
    // The tab lives in the URL so a link, a refresh or the back button lands on it.
    router.replace(next === "business" ? pathname : `${pathname}?tab=${next}`, {
      scroll: false,
    });
  };

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["assess-processes", engagementId],
    queryFn: () => assessApi.listProcesses(engagementId),
  });
  const summary = useQuery({
    queryKey: ["estate-summary", engagementId],
    queryFn: () => estateApi.summary(engagementId),
  });

  if (isLoading) {
    return (
      <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  if (isError || !data) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState
          title="Could not load the processes"
          description={error instanceof Error ? error.message : undefined}
          action={
            <button
              type="button"
              onClick={() => void refetch()}
              className="rounded-full border border-ink px-5 py-2.5 font-sans text-[13px] text-text"
            >
              Try again
            </button>
          }
        />
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
      <header className="mb-7 border-b border-line-strong pb-7">
        <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-muted">
          Assess
        </p>
        <h1 className="mb-3 font-serif text-[34px] leading-tight text-ink">
          {TABS.find((t) => t.key === tab)?.label}
        </h1>
        <p className="max-w-[80ch] font-sans text-[15px] leading-relaxed text-muted">
          {TABS.find((t) => t.key === tab)?.blurb}
        </p>
      </header>

      <div
        role="tablist"
        aria-label="Assessments"
        className="mb-8 flex flex-wrap gap-1 rounded-full border border-line-strong bg-paper-2 p-1"
      >
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-full px-4 py-2 font-sans text-[13px] font-medium transition-colors ${
              tab === t.key
                ? "bg-ink text-paper-on-ink"
                : "text-muted hover:text-text"
            }`}
          >
            {t.label}
            {t.key === "business" && (
              <span className="ml-2 font-mono text-[11px] opacity-60">
                {data.processes.filter((p) => p.has_score).length}/
                {data.processes.length}
              </span>
            )}
            {t.key !== "business" && t.key !== "budget" && (
              <TabMeta entry={summary.data?.[t.key]} />
            )}
          </button>
        ))}
      </div>

      {tab === "business" && (
        <div className="grid gap-5 lg:grid-cols-2">
          {data.processes.map((process) => (
            <ProcessCard
              key={process.key}
              engagementId={engagementId}
              process={process}
            />
          ))}
        </div>
      )}
      {tab !== "business" && tab !== "budget" && ESTATE_TABS.has(tab) && (
        <EstateAssessment key={tab} engagementId={engagementId} domain={tab} />
      )}
      {tab === "budget" && (
        <ItBudgetPage engagementId={engagementId} embedded />
      )}
    </main>
  );
}
