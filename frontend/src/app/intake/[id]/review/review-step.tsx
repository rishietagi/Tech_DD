"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { CoverSheet } from "@/components/intake/cover-sheet";
import { SignalPanel } from "@/components/intake/signal-panel";
import { ValidationSummary } from "@/components/intake/validation-summary";
import { ErrorState } from "@/components/ui/error-state";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, type FieldError } from "@/lib/api/client";
import { engagementsApi } from "@/lib/api/engagements";

export function ReviewStep({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { show } = useToast();
  const [fieldErrors, setFieldErrors] = useState<FieldError[]>([]);

  const { data: engagement, isLoading, isError } = useQuery({
    queryKey: ["engagement", engagementId],
    queryFn: () => engagementsApi.get(engagementId),
  });

  const submitMutation = useMutation({
    mutationFn: () => engagementsApi.submit(engagementId),
    onSuccess: (updated) => {
      setFieldErrors([]);
      queryClient.setQueryData(["engagement", engagementId], updated);
      show("Engagement filed");
      router.push(`/engagements/${engagementId}`);
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError) {
        setFieldErrors(error.fieldErrors);
        show(error.fieldErrors.length > 0 ? "Some required fields are missing" : error.message, "error");
      } else {
        show("Could not file this engagement", "error");
      }
    },
  });

  if (isLoading) {
    return (
      <div className="border-t border-line-strong py-8">
        <Skeleton className="mb-6 h-8 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !engagement) {
    return (
      <div className="py-8">
        <ErrorState title="Couldn't load this engagement" />
      </div>
    );
  }

  const alreadyFiled = engagement.status !== "draft";

  return (
    <div className="border-t border-line-strong py-8">
      <SectionHeader
        num="07"
        title="Review & File"
        hint="A cover sheet of everything on file. File the engagement once it's ready for the desk."
      />

      <ValidationSummary engagementId={engagementId} fieldErrors={fieldErrors} />

      <div className="mb-8 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_280px]">
        <CoverSheet engagementId={engagementId} intake={engagement.intake} />
        <SignalPanel />
      </div>

      <div className="flex items-center justify-between border-t border-line pt-6">
        <a
          href={`/intake/${engagementId}/objectives`}
          className="font-sans text-[14px] font-medium text-muted transition-colors hover:text-text"
        >
          ← Back
        </a>
        {alreadyFiled ? (
          <span className="font-sans text-[13px] font-medium text-steel">
            Already filed — status: {engagement.status}
          </span>
        ) : (
          <button
            type="button"
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending}
            className="rounded-full border border-ink bg-ink px-7 py-3.5 font-sans text-[14px] font-medium text-paper-on-ink transition-colors hover:border-kpmg-blue-dark hover:bg-kpmg-blue-dark disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitMutation.isPending ? "Filing…" : "File engagement"}
          </button>
        )}
      </div>
    </div>
  );
}
