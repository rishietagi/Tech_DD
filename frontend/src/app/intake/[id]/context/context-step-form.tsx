"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";

import { StepFooter } from "@/components/intake/step-footer";
import { Field } from "@/components/ui/field";
import { SectionHeader } from "@/components/ui/section-header";
import { Select } from "@/components/ui/select";
import { TextArea } from "@/components/ui/text-area";
import { TextInput } from "@/components/ui/text-input";
import { useAutosaveSection } from "@/lib/hooks/use-autosave-section";
import { DEAL_STAGE, PROCESS_TYPE } from "@/lib/schemas/enums";
import { dealContextSchema, type DealContextValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

export function ContextStepForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const draft = useIntakeStore((s) => s.draft);
  const { saveDebounced, saveNow, isSaving } = useAutosaveSection(engagementId, "context");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitted },
  } = useForm<DealContextValues>({
    resolver: zodResolver(dealContextSchema),
    mode: "onBlur",
  });

  const hasHydrated = useRef(false);
  useEffect(() => {
    if (!hasHydrated.current && draft?.context) {
      hasHydrated.current = true;
      reset(draft.context as DealContextValues);
    }
  }, [draft?.context, reset]);

  useEffect(() => {
    const subscription = watch((values) => saveDebounced(values as DealContextValues));
    return () => subscription.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch]);

  const onSubmit = handleSubmit(async (values) => {
    await saveNow(values);
    router.push(`/intake/${engagementId}/rationale`);
  });

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="border-t border-line-strong py-8">
        <SectionHeader
          num="01"
          title="Deal Context"
          hint="What is happening, and why now? This becomes the opening line of the diligence file."
        />

        <Field label="Deal codename" hint="Titles the scope document and its export filename." error={errors.deal_name?.message}>
          {(id) => <TextInput id={id} invalid={!!errors.deal_name} {...register("deal_name")} />}
        </Field>

        <Field label="Context" hint="Free text passed to the model. Shapes the engagement summary that opens the scope." error={errors.context_narrative?.message}>
          {(id) => <TextArea id={id} invalid={!!errors.context_narrative} {...register("context_narrative")} />}
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Deal stage" hint="Rules D6/D7 — exploratory and bid situations cap depth to a red-flag screen; exclusivity allows confirmatory work." error={errors.deal_stage?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.deal_stage}
                placeholder="Select stage"
                options={DEAL_STAGE.map((v) => ({ value: v, label: v }))}
                {...register("deal_stage")}
              />
            )}
          </Field>
          <Field label="Process type" hint="Context for how competitive the process is. Not currently a scoring rule." error={errors.process_type?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.process_type}
                placeholder="Select process"
                options={PROCESS_TYPE.map((v) => ({ value: v, label: v }))}
                {...register("process_type")}
              />
            )}
          </Field>
        </div>

        <Field label="Source of deal" hint="Context only. Not currently a scoring rule.">
          {(id) => <TextInput id={id} {...register("source_of_deal")} />}
        </Field>

        <Field label="Investor / firm name" hint="Names the investor in the document. Note: investor type (VC, growth equity) would drive rule A7, but that field is not captured.">
          {(id) => <TextInput id={id} {...register("investor_firm_name")} />}
        </Field>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-sans text-xs font-medium text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter isSubmitting={isSaving} />
    </form>
  );
}
