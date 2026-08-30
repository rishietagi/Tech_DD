"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { Controller, useForm } from "react-hook-form";

import { StepFooter } from "@/components/intake/step-footer";
import { Field } from "@/components/ui/field";
import { NumberInput } from "@/components/ui/number-input";
import { SectionHeader } from "@/components/ui/section-header";
import { Select } from "@/components/ui/select";
import { ToggleCardGroup } from "@/components/ui/toggle-card-group";
import { useAutosaveSection } from "@/lib/hooks/use-autosave-section";
import { HOLD_PERIOD, POST_CLOSE_INTENT } from "@/lib/schemas/enums";
import { dealStructureSchema, type DealStructureValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

const INVESTMENT_TYPE_OPTIONS = [
  { value: "strategic", title: "Strategic", description: "A corporate or strategic acquirer looking to integrate." },
  { value: "financial", title: "Financial", description: "A financial sponsor pursuing a standalone return." },
];

const STAKE_OPTIONS = [
  { value: "majority", title: "Majority", description: "Control-oriented access: org change, cost takeout, 100-day plan." },
  { value: "minority", title: "Minority", description: "Influence-oriented, lighter, relying more on management." },
];

export function StructureStepForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const draft = useIntakeStore((s) => s.draft);
  const { saveDebounced, saveNow, isSaving } = useAutosaveSection(engagementId, "structure");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    control,
    formState: { errors, isSubmitted },
  } = useForm<DealStructureValues>({
    resolver: zodResolver(dealStructureSchema),
    mode: "onBlur",
  });

  const hasHydrated = useRef(false);
  useEffect(() => {
    if (!hasHydrated.current && draft?.structure) {
      hasHydrated.current = true;
      reset(draft.structure as DealStructureValues);
    }
  }, [draft?.structure, reset]);

  useEffect(() => {
    const subscription = watch((values) => saveDebounced(values as DealStructureValues));
    return () => subscription.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch]);

  const onSubmit = handleSubmit(async (values) => {
    await saveNow(values);
    router.push(`/intake/${engagementId}/target`);
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="border-t border-line-strong py-8">
        <SectionHeader num="03" title="Deal Structure" hint="Strategic vs financial, majority vs minority — the modifiers that set access and depth." />

        <Field label="Investment type" error={errors.investment_type?.message}>
          {() => (
            <Controller
              name="investment_type"
              control={control}
              render={({ field }) => (
                <ToggleCardGroup
                  name="investment_type"
                  options={INVESTMENT_TYPE_OPTIONS}
                  value={field.value}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Stake" error={errors.stake?.message}>
          {() => (
            <Controller
              name="stake"
              control={control}
              render={({ field }) => (
                <ToggleCardGroup name="stake" options={STAKE_OPTIONS} value={field.value} onChange={field.onChange} />
              )}
            />
          )}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Stake percent" error={errors.stake_percent?.message}>
            {(id) => (
              <Controller
                name="stake_percent"
                control={control}
                render={({ field }) => (
                  <NumberInput id={id} value={field.value} onValueChange={field.onChange} min={0} max={100} />
                )}
              />
            )}
          </Field>
          <Field label="Hold period">
            {(id) => (
              <Select
                id={id}
                placeholder="Select hold period"
                options={HOLD_PERIOD.map((v) => ({ value: v, label: v }))}
                {...register("hold_period_years")}
              />
            )}
          </Field>
        </div>

        <Field label="Post-close intent" error={errors.post_close_intent?.message}>
          {(id) => (
            <Select
              id={id}
              invalid={!!errors.post_close_intent}
              placeholder="Select intent"
              options={POST_CLOSE_INTENT.map((v) => ({ value: v, label: v }))}
              {...register("post_close_intent")}
            />
          )}
        </Field>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-sans text-xs font-medium text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/rationale`} isSubmitting={isSaving} />
    </form>
  );
}
