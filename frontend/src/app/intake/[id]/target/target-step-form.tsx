"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { Controller, useForm } from "react-hook-form";

import { StepFooter } from "@/components/intake/step-footer";
import { Field } from "@/components/ui/field";
import { MultiSelect } from "@/components/ui/multi-select";
import { NumberInput } from "@/components/ui/number-input";
import { SectionHeader } from "@/components/ui/section-header";
import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import { useAutosaveSection } from "@/lib/hooks/use-autosave-section";
import {
  BUSINESS_MODEL,
  CUSTOMER_CONCENTRATION,
  DIGITAL_MATURITY,
  REVENUE_MODEL,
  REVENUE_STAGE,
  SECTOR,
} from "@/lib/schemas/enums";
import { targetCompanySchema, type TargetCompanyValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

export function TargetStepForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const draft = useIntakeStore((s) => s.draft);
  const { saveDebounced, saveNow, isSaving } = useAutosaveSection(engagementId, "target");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    control,
    formState: { errors, isSubmitted },
  } = useForm<TargetCompanyValues>({
    resolver: zodResolver(targetCompanySchema),
    mode: "onBlur",
    defaultValues: { revenue_model: [] },
  });

  const hasHydrated = useRef(false);
  useEffect(() => {
    if (!hasHydrated.current && draft?.target) {
      hasHydrated.current = true;
      reset(draft.target as TargetCompanyValues);
    }
  }, [draft?.target, reset]);

  useEffect(() => {
    const subscription = watch((values) => saveDebounced(values as TargetCompanyValues));
    return () => subscription.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch]);

  const onSubmit = handleSubmit(async (values) => {
    await saveNow(values);
    router.push(`/intake/${engagementId}/technology`);
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="border-t border-line-strong py-8">
        <SectionHeader num="05" title="Target Company" hint="What the company actually sells, to whom, and how it makes money." />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Company name" error={errors.company_name?.message}>
            {(id) => <TextInput id={id} invalid={!!errors.company_name} {...register("company_name")} />}
          </Field>
          <Field label="Website" optional>
            {(id) => <TextInput id={id} {...register("website")} />}
          </Field>
        </div>

        <Field label="Line of business" error={errors.line_of_business?.message}>
          {(id) => <TextArea id={id} invalid={!!errors.line_of_business} {...register("line_of_business")} />}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Sector" error={errors.sector?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.sector}
                placeholder="Select sector"
                options={SECTOR.map((v) => ({ value: v, label: v }))}
                {...register("sector")}
              />
            )}
          </Field>
          <Field label="Business model" error={errors.business_model?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.business_model}
                placeholder="Select model"
                options={BUSINESS_MODEL.map((v) => ({ value: v, label: v }))}
                {...register("business_model")}
              />
            )}
          </Field>
        </div>

        <Field label="Revenue model" error={errors.revenue_model?.message}>
          {() => (
            <Controller
              name="revenue_model"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="revenue_model"
                  options={REVENUE_MODEL.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Digital maturity" error={errors.digital_maturity?.message}>
          {(id) => (
            <Select
              id={id}
              invalid={!!errors.digital_maturity}
              placeholder="Select maturity"
              options={DIGITAL_MATURITY.map((v) => ({ value: v, label: v }))}
              {...register("digital_maturity")}
            />
          )}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Headcount" error={errors.headcount?.message}>
            {(id) => (
              <Controller
                name="headcount"
                control={control}
                render={({ field }) => (
                  <NumberInput id={id} invalid={!!errors.headcount} value={field.value} onValueChange={field.onChange} min={0} />
                )}
              />
            )}
          </Field>
          <Field label="Revenue stage" error={errors.revenue_stage?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.revenue_stage}
                placeholder="Select stage"
                options={REVENUE_STAGE.map((v) => ({ value: v, label: v }))}
                {...register("revenue_stage")}
              />
            )}
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="HQ location" error={errors.hq_location?.message}>
            {(id) => <TextInput id={id} invalid={!!errors.hq_location} {...register("hq_location")} />}
          </Field>
          <Field label="Founded year" optional>
            {(id) => (
              <Controller
                name="founded_year"
                control={control}
                render={({ field }) => (
                  <NumberInput id={id} value={field.value} onValueChange={field.onChange} min={1800} max={2100} />
                )}
              />
            )}
          </Field>
        </div>

        <Field label="Customer concentration" optional>
          {(id) => (
            <Select
              id={id}
              placeholder="Select concentration"
              options={CUSTOMER_CONCENTRATION.map((v) => ({ value: v, label: v }))}
              {...register("customer_concentration")}
            />
          )}
        </Field>

        <Field label="M&A history" optional hint="Prior acquisitions, unintegrated estates">
          {(id) => <TextArea id={id} {...register("ma_history")} />}
        </Field>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-mono text-xs text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/investor`} isSubmitting={isSaving} />
    </form>
  );
}
