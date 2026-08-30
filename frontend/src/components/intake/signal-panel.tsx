"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { scopeApi } from "@/lib/api/engagements";
import { useIntakeStore } from "@/lib/store/intake-store";

const DECK_LABEL: Record<string, string> = {
  product: "Product Tech DD",
  enterprise: "Enterprise IT DD",
  blended: "Blended",
};

const CONFIDENCE_TONE: Record<string, "steel" | "neutral" | "redline"> = {
  high: "steel",
  medium: "neutral",
  low: "redline",
};

/**
 * The forming Enterprise/Product leaning, live from the engine.
 *
 * Reads /scope/preview, which tolerates an incomplete intake by design — so this
 * updates as the user answers rather than waiting for a filed engagement.
 */
export function SignalPanel({ engagementId }: { engagementId: string }) {
  const draft = useIntakeStore((s) => s.draft);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["scope-preview", engagementId, draft],
    queryFn: () => scopeApi.preview(engagementId),
    enabled: !!engagementId,
    staleTime: 2_000,
    retry: false,
  });

  if (isLoading) {
    return (
      <aside className="rounded-2xl border border-line bg-paper-2 p-5">
        <h3 className="mb-2 font-sans text-[13px] font-semibold text-text">Enterprise / Product signal</h3>
        <p className="font-sans text-[13px] text-muted">Reading the intake…</p>
      </aside>
    );
  }

  if (isError || !data) {
    return (
      <aside className="rounded-2xl border border-line bg-paper-2 p-5">
        <h3 className="mb-2 font-sans text-[13px] font-semibold text-text">Enterprise / Product signal</h3>
        <p className="font-sans text-[13px] text-muted">
          The signal preview is unavailable right now. It does not affect your answers.
        </p>
      </aside>
    );
  }

  const { classification, row_count } = data;
  const fired = classification.signals.filter((s) => s.effect !== "unknown" && s.detail?.mix_delta);
  const topSignals = [...fired]
    .sort((a, b) => Math.abs(Number(b.detail.mix_delta)) - Math.abs(Number(a.detail.mix_delta)))
    .slice(0, 3);

  return (
    <aside className="rounded-2xl border border-line bg-paper-2 p-5">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="font-sans text-[13px] font-semibold text-text">Enterprise / Product signal</h3>
        <Badge tone={CONFIDENCE_TONE[classification.confidence] ?? "neutral"}>
          {classification.confidence}
        </Badge>
      </div>

      <p className="mb-1 font-display text-lg font-semibold text-text">
        {DECK_LABEL[classification.dd_type] ?? classification.dd_type}
      </p>

      <div className="mb-3">
        <div className="mb-1 flex justify-between font-sans text-[10.5px] font-medium text-muted-2">
          <span>Enterprise</span>
          <span>Product</span>
        </div>
        <div className="relative h-1.5 w-full rounded-full bg-paper-3">
          <div
            className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-kpmg-blue"
            style={{ left: `${classification.dd_mix}%` }}
            aria-hidden
          />
        </div>
      </div>

      {classification.override_applied && (
        <p className="mb-3 font-sans text-[12.5px] text-muted">
          You declared this engagement. The engine reads the answers as{" "}
          <strong className="text-text">{DECK_LABEL[classification.computed_dd_type]}</strong>.
        </p>
      )}

      {topSignals.length > 0 ? (
        <>
          <h4 className="mb-1.5 font-sans text-[11px] font-semibold text-muted-2 uppercase">
            Strongest signals
          </h4>
          <ul className="mb-3 space-y-1">
            {topSignals.map((signal) => {
              const delta = Number(signal.detail.mix_delta);
              return (
                <li key={signal.code} className="font-sans text-[12.5px] text-text">
                  <span className="mr-1.5 font-medium text-kpmg-blue">{signal.code}</span>
                  {signal.label}
                  <span className="ml-1.5 text-muted-2">
                    ({delta > 0 ? "+" : ""}
                    {delta})
                  </span>
                </li>
              );
            })}
          </ul>
        </>
      ) : (
        <p className="mb-3 font-sans text-[12.5px] text-muted">
          No archetype signals yet. Answer the technology and target steps to see the leaning form.
        </p>
      )}

      <p className="border-t border-line pt-2.5 font-sans text-[12px] text-muted-2">
        {row_count} scope area{row_count === 1 ? "" : "s"} would open
        {!data.is_complete && " · preview from a partial intake"}
      </p>
    </aside>
  );
}
