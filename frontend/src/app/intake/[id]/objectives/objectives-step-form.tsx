"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { Controller, useForm } from "react-hook-form";

import { StepFooter } from "@/components/intake/step-footer";
import { DateInput } from "@/components/ui/date-input";
import { Field } from "@/components/ui/field";
import { MultiSelect } from "@/components/ui/multi-select";
import { NumberInput } from "@/components/ui/number-input";
import { SectionHeader } from "@/components/ui/section-header";
import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/text-area";
import { useAutosaveSection } from "@/lib/hooks/use-autosave-section";
import {
  ACCESS_LEVEL,
  BUDGET_BAND,
  CODE_ACCESS,
  DD_OBJECTIVE,
  DD_TYPE_PREFERENCE,
  DELIVERABLE_FORMAT,
} from "@/lib/schemas/enums";
import { diligenceObjectivesSchema, type DiligenceObjectivesValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

export function ObjectivesStepForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const draft = useIntakeStore((s) => s.draft);
  const { saveDebounced, saveNow, isSaving } = useAutosaveSection(engagementId, "objectives");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    control,
    formState: { errors, isSubmitted },
  } = useForm<DiligenceObjectivesValues>({
    resolver: zodResolver(diligenceObjectivesSchema),
    mode: "onBlur",
    defaultValues: { dd_objectives: [], deliverable_format: [], dd_type_preference: "Let the platform decide" },
  });

  const hasHydrated = useRef(false);
  useEffect(() => {
    if (!hasHydrated.current && draft?.objectives) {
      hasHydrated.current = true;
      reset(draft.objectives as DiligenceObjectivesValues);
    }
  }, [draft?.objectives, reset]);

  useEffect(() => {
    const subscription = watch((values) => saveDebounced(values as DiligenceObjectivesValues));
    return () => subscription.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch]);

  const ddTypePreference = watch("dd_type_preference");
  const showOverrideReason = ddTypePreference && ddTypePreference !== "Let the platform decide";

  const onSubmit = handleSubmit(async (values) => {
    await saveNow(values);
    router.push(`/intake/${engagementId}/review`);
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="border-t border-line-strong py-8">
        <SectionHeader
          num="07"
          title="Diligence Objectives & Logistics"
          hint="What the team needs to answer, what access it will have, and how much time it has to do it."
        />

        <Field label="Diligence objectives" error={errors.dd_objectives?.message}>
          {() => (
            <Controller
              name="dd_objectives"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="dd_objectives"
                  options={DD_OBJECTIVE.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Access level" error={errors.access_level?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.access_level}
                placeholder="Select access"
                options={ACCESS_LEVEL.map((v) => ({ value: v, label: v }))}
                {...register("access_level")}
              />
            )}
          </Field>
          <Field label="Code access" error={errors.code_access?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.code_access}
                placeholder="Select code access"
                options={CODE_ACCESS.map((v) => ({ value: v, label: v }))}
                {...register("code_access")}
              />
            )}
          </Field>
        </div>

        <Field label="Deliverable format" error={errors.deliverable_format?.message}>
          {() => (
            <Controller
              name="deliverable_format"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="deliverable_format"
                  options={DELIVERABLE_FORMAT.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Timeline (weeks)" error={errors.timeline_weeks?.message}>
            {(id) => (
              <Controller
                name="timeline_weeks"
                control={control}
                render={({ field }) => (
                  <NumberInput id={id} invalid={!!errors.timeline_weeks} value={field.value} onValueChange={field.onChange} min={1} />
                )}
              />
            )}
          </Field>
          <Field label="Budget band" optional>
            {(id) => (
              <Select
                id={id}
                placeholder="Select band"
                options={BUDGET_BAND.map((v) => ({ value: v, label: v }))}
                {...register("budget_band")}
              />
            )}
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Bid date" optional>
            {(id) => <DateInput id={id} {...register("bid_date")} />}
          </Field>
          <Field label="IC date" optional>
            {(id) => <DateInput id={id} {...register("ic_date")} />}
          </Field>
        </div>

        <Field label="Clean team constraints" optional>
          {(id) => <TextArea id={id} {...register("clean_team_constraints")} />}
        </Field>

        <Field label="DD type preference" error={errors.dd_type_preference?.message}>
          {(id) => (
            <Select
              id={id}
              invalid={!!errors.dd_type_preference}
              options={DD_TYPE_PREFERENCE.map((v) => ({ value: v, label: v }))}
              {...register("dd_type_preference")}
            />
          )}
        </Field>

        {showOverrideReason && (
          <Field label="Reason for override" error={errors.dd_type_override_reason?.message}>
            {(id) => (
              <TextArea id={id} invalid={!!errors.dd_type_override_reason} {...register("dd_type_override_reason")} />
            )}
          </Field>
        )}
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-mono text-xs text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/technology`} isSubmitting={isSaving} nextLabel="Continue to review" />
    </form>
  );
}
