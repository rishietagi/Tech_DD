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
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import { useAutosaveSection } from "@/lib/hooks/use-autosave-section";
import { BUSINESS_MODEL, CUSTOMER_CONCENTRATION, DIGITAL_MATURITY, REVENUE_STAGE, SECTOR } from "@/lib/schemas/enums";
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
        <SectionHeader
          num="04"
          title="Target Company"
          hint="What the company actually sells, to whom, and how it makes money."
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Company name">
            {(id) => <TextInput id={id} {...register("company_name")} />}
          </Field>
          <Field label="Website">
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
          <Field label="Business model">
            {(id) => (
              <Select
                id={id}
                placeholder="Select model"
                options={BUSINESS_MODEL.map((v) => ({ value: v, label: v }))}
                {...register("business_model")}
              />
            )}
          </Field>
        </div>

        <Field label="Digital maturity" hint="If known — the single strongest signal for what kind of DD this is.">
          {(id) => (
            <Select
              id={id}
              placeholder="Select maturity"
              options={DIGITAL_MATURITY.map((v) => ({ value: v, label: v }))}
              {...register("digital_maturity")}
            />
          )}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Headcount">
            {(id) => (
              <Controller
                name="headcount"
                control={control}
                render={({ field }) => (
                  <NumberInput id={id} value={field.value} onValueChange={field.onChange} min={0} />
                )}
              />
            )}
          </Field>
          <Field label="Revenue stage">
            {(id) => (
              <Select
                id={id}
                placeholder="Select stage"
                options={REVENUE_STAGE.map((v) => ({ value: v, label: v }))}
                {...register("revenue_stage")}
              />
            )}
          </Field>
        </div>

        <Field label="Company revenue">
          {(id) => <TextInput id={id} {...register("company_revenue")} />}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="HQ location">
            {(id) => <TextInput id={id} {...register("hq_location")} />}
          </Field>
          <Field label="Founded year">
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

        <Field label="Office / plant locations" hint="Physical locations of offices, plants or facilities">
          {(id) => <TextInput id={id} {...register("office_locations")} />}
        </Field>

        <Field label="Customer concentration">
          {(id) => (
            <Select
              id={id}
              placeholder="Select concentration"
              options={CUSTOMER_CONCENTRATION.map((v) => ({ value: v, label: v }))}
              {...register("customer_concentration")}
            />
          )}
        </Field>

        <Field label="M&A history" hint="Prior acquisitions, unintegrated estates">
          {(id) => <TextArea id={id} {...register("ma_history")} />}
        </Field>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-sans text-xs font-medium text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/structure`} isSubmitting={isSaving} />
    </form>
  );
}
