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
import { ToggleCardGroup } from "@/components/ui/toggle-card-group";
import { useAutosaveSection } from "@/lib/hooks/use-autosave-section";
import { ACCESS_LEVEL, BUDGET_BAND, DD_OBJECTIVE, DELIVERABLE_FORMAT } from "@/lib/schemas/enums";
import { diligenceObjectivesSchema, type DiligenceObjectivesValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

const DD_TYPE_OPTIONS = [
  {
    value: "Let the platform decide",
    title: "Let the platform decide",
    description: "The engine classifies the engagement from your answers and picks the deck.",
  },
  {
    value: "Product Tech DD",
    title: "Product Tech DD",
    description: "The software is the asset. Produces the 10-objective product scope.",
  },
  {
    value: "Enterprise IT DD",
    title: "Enterprise IT DD",
    description: "Technology enables the business. Produces the enterprise IT focus areas.",
  },
  {
    value: "Blended",
    title: "Blended",
    description: "Both decks, weighted by how the engagement scores.",
  },
  // PLACEHOLDER (2026-08-31). The choice is captured and persisted, but the engine does
  // not act on it yet: there is no AI-heavy scope library, so generation still produces
  // the product or enterprise deck from the computed mix. See docs/PROJECT_LOG.md.
  {
    value: "AI-heavy Tech DD",
    title: "AI-heavy Tech DD",
    description: "Coming soon — the choice is saved, but the scope content is not yet defined.",
  },
];

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

  const onSubmit = handleSubmit(async (values) => {
    await saveNow(values);
    router.push(`/intake/${engagementId}/review`);
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="border-t border-line-strong py-8">
        <SectionHeader
          num="06"
          title="Diligence Objectives & Logistics"
          hint="What the team needs to answer, what access it will have, and how much time it has to do it."
        />

        <Field
          label="Type of diligence"
          hint="Which scope of work should this engagement produce? This drives the whole document."
        >
          {() => (
            <Controller
              name="dd_type_preference"
              control={control}
              render={({ field }) => (
                <ToggleCardGroup
                  name="dd_type_preference"
                  columns={2}
                  options={DD_TYPE_OPTIONS}
                  value={field.value}
                  onChange={field.onChange}
                />
              )}
            />
          )}
        </Field>

        <Field label="Diligence objectives" hint="Each objective selected raises the tier of the scope areas whose primary workstream it matches, so the areas you care about get more depth.">
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

        <Field label="Access level" hint="Rule D2 — limited or public information alone caps every area at a screen, no matter what else the intake says.">
          {(id) => (
            <Select
              id={id}
              placeholder="Select access"
              options={ACCESS_LEVEL.map((v) => ({ value: v, label: v }))}
              {...register("access_level")}
            />
          )}
        </Field>

        <Field label="Deliverable format" hint="What the engagement produces. Context for the reporting phase.">
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
          <Field label="Timeline (weeks)" hint="Rule D5 — drives the effort budget and the phase split. A short timeline forces areas down to shallower tiers.">
            {(id) => (
              <Controller
                name="timeline_weeks"
                control={control}
                render={({ field }) => (
                  <NumberInput id={id} value={field.value} onValueChange={field.onChange} min={1} />
                )}
              />
            )}
          </Field>
          <Field label="Budget band" hint="Context for team shape and effort. Not currently a scoring rule.">
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
          <Field label="Bid date" hint="Context only. Not currently a scoring rule.">
            {(id) => <DateInput id={id} {...register("bid_date")} />}
          </Field>
          <Field label="IC date" hint="Investment committee date. Context only; not currently a scoring rule.">
            {(id) => <DateInput id={id} {...register("ic_date")} />}
          </Field>
        </div>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-sans text-xs font-medium text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/technology`} isSubmitting={isSaving} nextLabel="Continue to review" />
    </form>
  );
}
