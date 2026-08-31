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
          <Field label="Build vs buy" hint="Rules A4/A5 — predominantly in-house pulls the mix toward Product (+15); COTS/packaged pulls toward Enterprise (-20).">
            {(id) => (
              <Select
                id={id}
                placeholder="Select"
                options={BUILD_VS_BUY.map((v) => ({ value: v, label: v }))}
                {...register("build_vs_buy")}
              />
            )}
          </Field>
          <Field label="Hosting model" hint="Rules A10/C6 — a predominantly on-premise estate pulls toward Enterprise (-10) and opens data-centre and DR scope.">
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

        <Field label="Core systems" hint="Rules A4/C5 — naming SAP, Oracle, Dynamics, NetSuite or Workday marks an ERP-heavy estate and injects the note that ERP is roughly 80% of integration cost.">
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

        <Field label="Cloud providers" hint="Context for the infrastructure and cloud-cost areas. Passed to the model.">
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

        <Field label="Known tech stack" hint="Free text passed to the model. This is what lets scope lines name the actual languages, frameworks and datastores instead of saying &quot;the technology stack&quot;.">
          {(id) => <TextInput id={id} {...register("known_tech_stack")} />}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Engineering headcount" hint="Read against total headcount in step 04 to gauge how engineering-weighted the business is.">
            {(id) => (
              <Controller
                name="engineering_headcount"
                control={control}
                render={({ field }) => <NumberInput id={id} value={field.value} onValueChange={field.onChange} min={0} />}
              />
            )}
          </Field>
          <Field label="Engineering share of headcount (%)" hint="Rule A6 — 30% or more pulls the mix toward Product (+10).">
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

        <Field label="Outsourcing reliance" hint="Context for key-person and vendor-dependency risk. Passed to the model.">
          {(id) => (
            <Select
              id={id}
              placeholder="Select"
              options={OUTSOURCING_RELIANCE.map((v) => ({ value: v, label: v }))}
              {...register("outsourcing_reliance")}
            />
          )}
        </Field>

        <Field label="AI/ML dependence" hint="Rules A11/C9 — embedded or core AI pulls toward Product (+10) and opens model governance, data rights and inference-cost scope.">
          {(id) => (
            <Select
              id={id}
              placeholder="Select"
              options={AI_ML_DEPENDENCE.map((v) => ({ value: v, label: v }))}
              {...register("ai_ml_dependence")}
            />
          )}
        </Field>

        <Field label="Data sensitivity" hint="Rule M2 — any regulated data (PII, PHI, PCI, financial) makes security and data governance mandatory at Tier 2 or deeper, whatever the archetype.">
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

        <Field label="Compliance regimes" hint="Rule M3 — naming any regime makes the regulatory workstream mandatory at Tier 2 or deeper.">
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

        <Field label="Known incidents" hint="Outages, breaches and audit findings. Passed to the model so the scope can address them by name.">
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
