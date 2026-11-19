import { BandBadge, LadderMeter } from "@/components/engagement/band-badge";
import {
  PointersExplain,
  ProcessIndexExplain,
  RefinementExplain,
  StepScoreExplain,
  StepWeightExplain,
} from "@/components/engagement/explain";
import { InfoTip } from "@/components/ui/info-tip";
import { ScoreRing } from "@/components/ui/score-ring";
import type {
  AssessmentScorePayload,
  PointerKind,
  ScorePointer,
} from "@/types/assess";

const POINTER_LABELS: Record<PointerKind, string> = {
  gap: "Gap",
  strength: "Strength",
  probe: "Probe next",
};

const POINTER_CLASSES: Record<PointerKind, string> = {
  gap: "border-priority-critical text-priority-critical",
  strength: "border-status-received text-status-received",
  probe: "border-steel text-steel",
};

function PointerRow({ pointer }: { pointer: ScorePointer }) {
  return (
    <li className="flex gap-4 border-t border-line py-3.5 first:border-t-0">
      <span
        className={`mt-0.5 h-fit flex-none rounded-full border px-2.5 py-0.5 font-sans text-[10px] font-semibold uppercase ${POINTER_CLASSES[pointer.kind]}`}
      >
        {POINTER_LABELS[pointer.kind]}
      </span>
      <p className="font-sans text-[14px] leading-relaxed text-text">
        {pointer.text}
      </p>
    </li>
  );
}

/**
 * The exec summary view.
 *
 * Internal-facing by decision (2026-09-02): frank, diagnostic, names weak spots plainly.
 * The export seam for a client-facing version is deliberately left open rather than
 * built — the same treatment the shared-drive scanner got.
 */
export function ProcessScore({ payload }: { payload: AssessmentScorePayload }) {
  const refinedSteps = payload.steps.filter((step) => step.refined);

  // A document measure, not a dashboard width. Prose past ~90ch is hard to track back
  // to the next line, and letting the table run wider than the summary gave the page
  // two competing right edges. Found by looking at the rendered page, not by a test.
  return (
    <div className="max-w-[1000px]">
      {/* The index, the band, and what the band means. */}
      <section className="card mb-8 overflow-hidden bg-gradient-to-br from-kpmg-blue-tint-strong via-kpmg-blue-tint to-paper p-7">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div>
            <p className="mb-3 flex items-center font-sans text-[11px] font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
              Automation index
              <InfoTip label="the automation index">
                <ProcessIndexExplain />
              </InfoTip>
            </p>
            <div className="flex items-center gap-5">
              <ScoreRing
                value={payload.index}
                size={124}
                label={`Automation index ${payload.index.toFixed(1)} of 100`}
              />
              <div>
                <p className="font-display text-[20px] font-semibold text-ink tabular-nums">
                  {payload.index.toFixed(1)}
                  <span className="text-[14px] font-normal text-muted-2">
                    {" "}
                    / 100
                  </span>
                </p>
                <div className="mt-1.5">
                  <BandBadge band={payload.band} />
                </div>
              </div>
            </div>
            {payload.index !== payload.deterministic_index && (
              <p className="mt-3 max-w-[60ch] font-sans text-[12px] text-muted">
                Rules alone scored {payload.deterministic_index.toFixed(1)}. The
                recorded evidence moved {refinedSteps.length} step
                {refinedSteps.length === 1 ? "" : "s"}; each adjustment and its
                reason is shown in the table below.
              </p>
            )}
          </div>
          <p className="max-w-[46ch] border-l-2 border-kpmg-blue-light pl-4 font-sans text-[14px] leading-relaxed text-muted">
            {payload.band_meaning}
          </p>
        </div>
      </section>

      {/* Executive summary. */}
      <section className="mb-8">
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wide text-muted">
          Executive summary
        </h2>
        <p className="max-w-[78ch] font-sans text-[16px] leading-[1.7] text-text">
          {payload.executive_summary}
        </p>
        {payload.shape_note && (
          <p className="mt-4 max-w-[72ch] border-l-2 border-steel pl-4 font-sans text-[14px] leading-relaxed text-muted">
            {payload.shape_note}
          </p>
        )}
      </section>

      {/* Per-step scores. The shape of the cycle is the finding; the index is a summary. */}
      <section className="mb-8">
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wide text-muted">
          Step scores
        </h2>
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse">
            <thead>
              <tr className="border-b border-line-strong">
                <th className="px-5 py-3 text-left font-mono text-[11px] uppercase text-muted">
                  Step
                </th>
                <th className="w-[100px] px-5 py-3 text-left font-mono text-[11px] uppercase text-muted">
                  <span className="inline-flex items-center">
                    Weight
                    <InfoTip label="a step weight" title="Step weight">
                      <StepWeightExplain />
                    </InfoTip>
                  </span>
                </th>
                <th className="w-[170px] px-5 py-3 text-left font-mono text-[11px] uppercase text-muted">
                  <span className="inline-flex items-center">
                    Score
                    <InfoTip label="a step score" title="Step score">
                      <StepScoreExplain />
                    </InfoTip>
                  </span>
                </th>
                <th className="px-5 py-3 text-left font-mono text-[11px] uppercase text-muted">
                  Basis
                </th>
              </tr>
            </thead>
            <tbody>
              {payload.steps.map((step) => (
                <tr
                  key={step.key}
                  className="border-b border-line last:border-b-0"
                >
                  <td className="px-5 py-4 align-top">
                    <span className="mr-2 font-mono text-[12px] text-muted-2">
                      {String(step.sn).padStart(2, "0")}
                    </span>
                    <span
                      className={`font-sans text-[14px] ${
                        step.assessed ? "text-text" : "text-muted-2"
                      }`}
                    >
                      {step.title}
                    </span>
                  </td>
                  <td className="px-5 py-4 align-top font-mono text-[13px] text-muted">
                    {step.weight}%
                  </td>
                  <td className="px-5 py-4 align-top">
                    <LadderMeter score={step.score} />
                    {step.assessed && step.level_label && (
                      <span className="mt-1 block font-sans text-[12px] text-muted">
                        {step.level_label}
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-4 align-top">
                    <span className="font-sans text-[13px] leading-relaxed text-muted">
                      {step.reason}
                    </span>
                    {step.refined && step.refinement_reason && (
                      <span className="mt-2 block border-l-2 border-steel pl-3 font-sans text-[12px] leading-relaxed text-steel">
                        Adjusted from {step.deterministic_score}/5:{" "}
                        {step.refinement_reason}
                        <InfoTip
                          label="an AI adjustment"
                          title="AI adjustment (±1)"
                        >
                          <RefinementExplain />
                        </InfoTip>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 max-w-[80ch] font-sans text-[12px] leading-relaxed text-muted">
          {payload.coverage_note}
        </p>
      </section>

      {/* Pointers. */}
      <section className="mb-8">
        <h2 className="mb-3 flex items-center font-mono text-[11px] uppercase tracking-wide text-muted">
          Pointers
          <InfoTip label="the pointers" title="How pointers are chosen">
            <PointersExplain />
          </InfoTip>
        </h2>
        <ul className="card px-5 py-2">
          {payload.pointers.map((pointer, index) => (
            <PointerRow key={`${pointer.kind}-${index}`} pointer={pointer} />
          ))}
        </ul>
      </section>

      <footer className="border-t border-line pt-5">
        <p className="max-w-[80ch] font-sans text-[12px] leading-relaxed text-muted">
          {payload.disclaimer}
        </p>
        <p className="mt-2 font-mono text-[11px] uppercase text-muted-2">
          Generator: {payload.generator} · Questionnaire v
          {payload.questionnaire_version} · Model: {payload.model_ref}
        </p>
      </footer>
    </div>
  );
}
