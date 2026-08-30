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
  AI_ML_DEPENDENCE,
  BUILD_VS_BUY,
  CLOUD_PROVIDER,
  COMPLIANCE_REGIME,
  CORE_SYSTEM,
  DATA_SENSITIVITY,
  HOSTING_MODEL,
  OUTSOURCING_RELIANCE,
} from "@/lib/schemas/enums";
import { technologyProfileSchema, type TechnologyProfileValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

export function TechnologyStepForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const draft = useIntakeStore((s) => s.draft);
  const { saveDebounced, saveNow, isSaving } = useAutosaveSection(engagementId, "technology");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    control,
    formState: { errors, isSubmitted },
  } = useForm<TechnologyProfileValues>({
    resolver: zodResolver(technologyProfileSchema),
    mode: "onBlur",
  });

  const hasHydrated = useRef(false);
  useEffect(() => {
    if (!hasHydrated.current && draft?.technology) {
      hasHydrated.current = true;
      reset(draft.technology as TechnologyProfileValues);
    }
  }, [draft?.technology, reset]);

  useEffect(() => {
    const subscription = watch((values) => saveDebounced(values as TechnologyProfileValues));
    return () => subscription.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch]);

  const onSubmit = handleSubmit(async (values) => {
    await saveNow(values);
    router.push(`/intake/${engagementId}/objectives`);
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="border-t border-line-strong py-8">
        <SectionHeader
          num="05"
          title="Technology Profile"
          hint="The shape of the estate. These answers weight the Enterprise/Product mix; the archetype itself is declared in step 06."
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Build vs buy">
            {(id) => (
              <Select
                id={id}
                placeholder="Select"
                options={BUILD_VS_BUY.map((v) => ({ value: v, label: v }))}
                {...register("build_vs_buy")}
              />
            )}
          </Field>
          <Field label="Hosting model">
            {(id) => (
              <Select
                id={id}
                placeholder="Select"
                options={HOSTING_MODEL.map((v) => ({ value: v, label: v }))}
                {...register("hosting_model")}
              />
            )}
          </Field>
        </div>

        <Field label="Core systems">
          {() => (
            <Controller
              name="core_systems"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="core_systems"
                  options={CORE_SYSTEM.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Cloud providers">
          {() => (
            <Controller
              name="cloud_providers"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="cloud_providers"
                  options={CLOUD_PROVIDER.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Known tech stack">
          {(id) => <TextInput id={id} {...register("known_tech_stack")} />}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Engineering headcount">
            {(id) => (
              <Controller
                name="engineering_headcount"
                control={control}
                render={({ field }) => <NumberInput id={id} value={field.value} onValueChange={field.onChange} min={0} />}
              />
            )}
          </Field>
          <Field label="Engineering share of headcount (%)">
            {(id) => (
              <Controller
                name="engineering_share_pct"
                control={control}
                render={({ field }) => (
                  <NumberInput id={id} value={field.value} onValueChange={field.onChange} min={0} max={100} />
                )}
              />
            )}
          </Field>
        </div>

        <Field label="Outsourcing reliance">
          {(id) => (
            <Select
              id={id}
              placeholder="Select"
              options={OUTSOURCING_RELIANCE.map((v) => ({ value: v, label: v }))}
              {...register("outsourcing_reliance")}
            />
          )}
        </Field>

        <Field label="AI/ML dependence">
          {(id) => (
            <Select
              id={id}
              placeholder="Select"
              options={AI_ML_DEPENDENCE.map((v) => ({ value: v, label: v }))}
              {...register("ai_ml_dependence")}
            />
          )}
        </Field>

        <Field label="Data sensitivity">
          {() => (
            <Controller
              name="data_sensitivity"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="data_sensitivity"
                  options={DATA_SENSITIVITY.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Compliance regimes">
          {() => (
            <Controller
              name="compliance_regimes"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  name="compliance_regimes"
                  options={COMPLIANCE_REGIME.map((v) => ({ value: v, label: v }))}
                  value={field.value ?? []}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Known incidents" hint="Outages, breaches, audit findings">
          {(id) => <TextArea id={id} {...register("known_incidents")} />}
        </Field>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-sans text-xs font-medium text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/target`} isSubmitting={isSaving} />
    </form>
  );
}
