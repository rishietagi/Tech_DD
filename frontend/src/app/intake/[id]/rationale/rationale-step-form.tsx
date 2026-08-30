"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { Controller, useForm } from "react-hook-form";

import { StepFooter } from "@/components/intake/step-footer";
import { Field } from "@/components/ui/field";
import { MultiSelect } from "@/components/ui/multi-select";
import { SectionHeader } from "@/components/ui/section-header";
import { TextArea } from "@/components/ui/text-area";
import { useAutosaveSection } from "@/lib/hooks/use-autosave-section";
import { VALUE_CREATION_LEVER } from "@/lib/schemas/enums";
import { rationaleSchema, type RationaleValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

export function RationaleStepForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const draft = useIntakeStore((s) => s.draft);
  const { saveDebounced, saveNow, isSaving } = useAutosaveSection(engagementId, "rationale");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    control,
    formState: { errors, isSubmitted },
  } = useForm<RationaleValues>({
    resolver: zodResolver(rationaleSchema),
    mode: "onBlur",
  });

  const hasHydrated = useRef(false);
  useEffect(() => {
    if (!hasHydrated.current && draft?.rationale) {
      hasHydrated.current = true;
      reset(draft.rationale as RationaleValues);
    }
  }, [draft?.rationale, reset]);

  useEffect(() => {
    const subscription = watch((values) => saveDebounced(values as RationaleValues));
    return () => subscription.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch]);

  const onSubmit = handleSubmit(async (values) => {
    await saveNow(values);
    router.push(`/intake/${engagementId}/structure`);
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="border-t border-line-strong py-8">
        <SectionHeader
          num="02"
          title="Rationale"
          hint="The thesis in plain terms — what does the buyer believe, and what would prove it wrong?"
        />

        <Field label="Rationale">
          {(id) => <TextArea id={id} {...register("rationale_narrative")} />}
        </Field>

        <Field label="Value creation levers">
          {() => (
            <Controller
              name="value_creation_levers"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="value_creation_levers"
                  options={VALUE_CREATION_LEVER.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Deal breakers">
          {(id) => <TextArea id={id} {...register("deal_breakers")} />}
        </Field>

        <Field
          label="Focus areas"
          hint="What should the diligence broadly cover, and how deep should it go? These questions shape what the team investigates and how much depth each area gets."
        >
          {(id) => <TextArea id={id} {...register("focus_areas")} />}
        </Field>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-sans text-xs font-medium text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/context`} isSubmitting={isSaving} />
    </form>
  );
}
