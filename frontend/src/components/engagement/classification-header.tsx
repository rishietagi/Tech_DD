"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import type { Classification } from "@/types/engagement";

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

/** The 0-100 mix, drawn as a position between the two archetypes. */
function MixReadout({ mix }: { mix: number }) {
  return (
    <div className="w-full">
      <div className="mb-1.5 flex justify-between font-sans text-[11px] font-medium text-muted-2">
        <span>Enterprise</span>
        <span>Product</span>
      </div>
      <div className="relative h-2 w-full rounded-full bg-paper-3">
        <div
          className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-kpmg-blue shadow-sm"
          style={{ left: `${mix}%` }}
          aria-hidden
        />
      </div>
      <div className="mt-1.5 text-center font-sans text-[11px] text-muted">
        mix {mix} / 100
      </div>
    </div>
  );
}

export function ClassificationHeader({
  classification,
  generator,
}: {
  classification: Classification;
  generator: string;
}) {
  const [showSignals, setShowSignals] = useState(false);

  const {
    dd_type,
    dd_mix,
    confidence,
    computed_dd_type,
    computed_dd_mix,
    override_applied,
    override_source,
    signals,
    confidence_reasons,
  } = classification;

  const disagrees = override_applied && dd_type !== computed_dd_type;
  const firedSignals = signals.filter((s) => s.effect !== "unknown");
  const unknownSignals = signals.filter((s) => s.effect === "unknown");

  return (
    <section className="mb-8 rounded-2xl border border-line bg-paper-2 p-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
            Classification
          </div>
          <h2 className="font-display text-2xl font-semibold text-text">{DECK_LABEL[dd_type] ?? dd_type}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={CONFIDENCE_TONE[confidence] ?? "neutral"}>{confidence} confidence</Badge>
          {generator.startsWith("rules") && generator !== "rules" && (
            <Badge tone="neutral">prose not tailored</Badge>
          )}
        </div>
      </div>

      <div className="mb-5 max-w-md">
        <MixReadout mix={dd_mix} />
      </div>

      {override_applied && (
        <div
          className={`mb-4 rounded-xl border px-4 py-3 ${
            disagrees ? "border-redline bg-redline-tint" : "border-line bg-paper"
          }`}
        >
          <p className="font-sans text-[13px] text-text">
            <span className="font-semibold">Archetype declared in the intake:</span> {override_source}.
          </p>
          {disagrees && (
            <p className="mt-1 font-sans text-[13px] text-muted">
              The engine derived <strong>{DECK_LABEL[computed_dd_type]}</strong> (mix {computed_dd_mix}) from
              the answers given. The declaration is used for this scope; the disagreement is shown because it
              is informative, not because either is wrong.
            </p>
          )}
        </div>
      )}

      <button
        type="button"
        onClick={() => setShowSignals((open) => !open)}
        aria-expanded={showSignals}
        className="font-sans text-[13px] font-medium text-steel underline underline-offset-2"
      >
        {showSignals ? "Hide" : "Why this classification?"}
      </button>

      {showSignals && (
        <div className="mt-4 space-y-4">
          {confidence_reasons.length > 0 && (
            <div>
              <h3 className="mb-1.5 font-sans text-[11px] font-semibold text-muted-2 uppercase">
                Confidence
              </h3>
              <ul className="space-y-1">
                {confidence_reasons.map((reason) => (
                  <li key={reason} className="font-sans text-[13px] text-muted">
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h3 className="mb-1.5 font-sans text-[11px] font-semibold text-muted-2 uppercase">
              Signals that fired ({firedSignals.length})
            </h3>
            <ul className="space-y-1.5">
              {firedSignals.map((signal) => {
                const delta = signal.detail?.mix_delta as number | undefined;
                return (
                  <li key={signal.code} className="font-sans text-[13px] text-text">
                    <span className="mr-2 font-medium text-kpmg-blue">{signal.code}</span>
                    {signal.label}
                    {typeof delta === "number" && (
                      <span className="ml-2 text-muted">
                        ({delta > 0 ? "+" : ""}
                        {delta} toward {delta > 0 ? "product" : "enterprise"})
                      </span>
                    )}
                    {signal.source_field && (
                      <span className="ml-2 text-muted-2">
                        · {signal.source_field.split(".").pop()} = {signal.source_value}
                      </span>
                    )}
                    {signal.citation && <span className="ml-2 text-muted-2 italic">{signal.citation}</span>}
                  </li>
                );
              })}
            </ul>
          </div>

          {unknownSignals.length > 0 && (
            <div>
              <h3 className="mb-1.5 font-sans text-[11px] font-semibold text-muted-2 uppercase">
                Not captured by this intake ({unknownSignals.length})
              </h3>
              <p className="mb-1.5 font-sans text-[12px] text-muted">
                These rules could not be applied. They are reported rather than scored, so they do not move
                the classification.
              </p>
              <p className="font-sans text-[12px] text-muted-2">
                {unknownSignals.map((s) => s.code).join(", ")}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
