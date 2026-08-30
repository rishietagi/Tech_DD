"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { AutosaveIndicator } from "@/components/intake/autosave-indicator";
import { FieldCounter } from "@/components/intake/field-counter";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Stamp, type StampState } from "@/components/ui/stamp";
import { engagementsApi } from "@/lib/api/engagements";
import { useIntakeStore } from "@/lib/store/intake-store";
import { INTAKE_STEPS } from "@/types/intake";

function stampStateFor(status: string, visitedCount: number): StampState {
  if (status === "filed" || status === "scoped") return "filed";
  if (visitedCount === INTAKE_STEPS.length) return "ready-to-file";
  if (visitedCount > 0) return "in-progress";
  return "draft";
}

export function IntakeShell({ engagementId, children }: { engagementId: string; children: React.ReactNode }) {
  const setEngagement = useIntakeStore((s) => s.setEngagement);
  const visitedSteps = useIntakeStore((s) => s.visitedSteps);
  const saveStatus = useIntakeStore((s) => s.saveStatus);
  const lastSavedAt = useIntakeStore((s) => s.lastSavedAt);
  const storeEngagementId = useIntakeStore((s) => s.engagementId);

  const { data: engagement, isLoading, isError, refetch } = useQuery({
    queryKey: ["engagement", engagementId],
    queryFn: () => engagementsApi.get(engagementId),
  });

  useEffect(() => {
    if (engagement) setEngagement(engagement.id, engagement.intake);
  }, [engagement, setEngagement]);

  if (isLoading || storeEngagementId !== engagementId) {
    return (
      <main className="mx-auto w-full max-w-[1600px] px-8 pt-10 pb-24">
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </main>
    );
  }

  if (isError || !engagement) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-8 py-20">
        <ErrorState
          title="Couldn't load this engagement"
          description="It may not exist, or the API may be unreachable."
          action={
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-full border border-line-strong px-5 py-2.5 font-sans text-[13px] font-medium"
            >
              Retry
            </button>
          }
        />
      </main>
    );
  }

  return (
    <div>
      <section className="mx-auto w-full max-w-[1600px] px-8 pt-10 pb-6">
        <div className="mb-3 flex items-start justify-between gap-4">
          <div className="font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">{engagement.deal_name}</div>
          <Stamp state={stampStateFor(engagement.status, visitedSteps.size)} />
        </div>
        <div className="flex items-center justify-between gap-4">
          <FieldCounter filled={visitedSteps.size} total={INTAKE_STEPS.length} />
          <AutosaveIndicator status={saveStatus} lastSavedAt={lastSavedAt} />
        </div>
      </section>

      <main className="mx-auto w-full max-w-[1600px] px-8 pb-24">{children}</main>
    </div>
  );
}
