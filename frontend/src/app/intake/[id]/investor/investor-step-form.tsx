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
import { INVESTOR_TECH_CAPABILITY, INVESTOR_TYPE } from "@/lib/schemas/enums";
import { investorSchema, type InvestorValues } from "@/lib/schemas/intake";
import { useIntakeStore } from "@/lib/store/intake-store";

export function InvestorStepForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const draft = useIntakeStore((s) => s.draft);
  const { saveDebounced, saveNow, isSaving } = useAutosaveSection(engagementId, "investor");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitted },
  } = useForm<InvestorValues>({
    resolver: zodResolver(investorSchema),
    mode: "onBlur",
  });

  const hasHydrated = useRef(false);
  useEffect(() => {
    if (!hasHydrated.current && draft?.investor) {
      hasHydrated.current = true;
      reset(draft.investor as InvestorValues);
    }
  }, [draft?.investor, reset]);

  useEffect(() => {
    const subscription = watch((values) => saveDebounced(values as InvestorValues));
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
        <SectionHeader num="04" title="Investor" hint="Who is behind the deal, and what does their own tech capability mean for how prescriptive the scope should be." />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Firm name" error={errors.firm_name?.message}>
            {(id) => <TextInput id={id} invalid={!!errors.firm_name} {...register("firm_name")} />}
          </Field>
          <Field label="Investor type" error={errors.investor_type?.message}>
            {(id) => (
              <Select
                id={id}
                invalid={!!errors.investor_type}
                placeholder="Select type"
                options={INVESTOR_TYPE.map((v) => ({ value: v, label: v }))}
                {...register("investor_type")}
              />
            )}
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Deal lead name" error={errors.deal_lead_name?.message}>
            {(id) => <TextInput id={id} invalid={!!errors.deal_lead_name} {...register("deal_lead_name")} />}
          </Field>
          <Field label="Deal lead email" error={errors.deal_lead_email?.message}>
            {(id) => (
              <TextInput
                id={id}
                type="email"
                invalid={!!errors.deal_lead_email}
                {...register("deal_lead_email")}
              />
            )}
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Check size" optional>
            {(id) => <TextInput id={id} {...register("check_size")} />}
          </Field>
          <Field label="Enterprise value" optional>
            {(id) => <TextInput id={id} {...register("enterprise_value")} />}
          </Field>
        </div>

        <Field label="Existing portfolio overlap" optional>
          {(id) => <TextArea id={id} {...register("existing_portfolio_overlap")} />}
        </Field>

        <Field label="Investor tech capability" optional>
          {(id) => (
            <Select
              id={id}
              placeholder="Select capability"
              options={INVESTOR_TECH_CAPABILITY.map((v) => ({ value: v, label: v }))}
              {...register("investor_tech_capability")}
            />
          )}
        </Field>
      </div>

      {isSubmitted && Object.keys(errors).length > 0 && (
        <p role="alert" className="mb-4 font-mono text-xs text-redline">
          Fix the highlighted fields before continuing.
        </p>
      )}

      <StepFooter backHref={`/intake/${engagementId}/structure`} isSubmitting={isSaving} />
    </form>
  );
}
