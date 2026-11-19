"use client";

import { LadderMeter } from "@/components/engagement/band-badge";
import {
  PointersExplain,
  ProcessIndexExplain,
  RefinementExplain,
  StepScoreExplain,
  StepWeightExplain,
} from "@/components/engagement/explain";
import { GapRegister } from "@/components/estate/gap-register";
import { ScoreSummary } from "@/components/estate/score-summary";
import { ExportLink } from "@/components/ui/export-link";
import { HowItWorks, InfoTip } from "@/components/ui/info-tip";
import { findingsApi } from "@/lib/api/assess";
import type { AssessmentScoreRead, PointerKind } from "@/types/assess";
import type { GapEdit } from "@/types/estate";

const POINTER_LABELS: Record<PointerKind, string> = {
  gap: "Gap",
  strength: "Strength",
  probe: "Probe next",
};

/**
 * A process's score, in the same order as every other Assess tab (Rishi, 2026-11-19):
 * the score, then the findings right below it, then the step-level detail. Pointers, the
 * cycle shape and the coverage sit in a "Notes" drop-down so the page stays light.
 *
 * Internal-facing by decision (2026-09-02); the findings export carries what a client
 * file needs.
 */
export function ProcessScore({
  score,
  engagementId,
  onEdit,
  onRevert,
}: {
  score: AssessmentScoreRead;
  engagementId: string;
  onEdit: (key: string, edit: GapEdit) => Promise<void>;
  onRevert: (key: string) => Promise<void>;
}) {
  const payload = score.payload;
  const refined = payload.steps.filter((step) => step.refined);

  return (
    <div className="max-w-[1100px]">
      <ScoreSummary
        label="Automation index"
        explain={<ProcessIndexExplain />}
        index={payload.index}
        band={payload.band}
        bandMeaning={payload.band_meaning}
        summary={payload.executive_summary}
        note={
          payload.index !== payload.deterministic_index
            ? `Rules alone scored ${payload.deterministic_index.toFixed(1)}; ${refined.length} step${refined.length === 1 ? "" : "s"} adjusted with evidence`
            : null
        }
        meta={`Version ${score.version}`}
      />

      <GapRegister
        gaps={score.gaps}
        onEdit={onEdit}
        onRevert={onRevert}
        empty="No findings: no step is weak enough, and the cycle is even."
        actions={
          <ExportLink
            href={findingsApi.exportUrl(engagementId, "business")}
            label="Export"
          />
        }
      />

      <h3 className="mb-4 font-display text-[20px] font-semibold text-ink">
        Step scores
      </h3>
      <div className="mb-6 overflow-x-auto rounded-xl border border-line">
        <table className="w-full min-w-[720px] border-collapse">
          <thead>
            <tr className="border-b border-line text-left font-sans text-[12px] font-medium text-muted">
              <th className="px-5 py-3">Step</th>
              <th className="w-[100px] px-5 py-3">
                <span className="inline-flex items-center">
                  Weight
                  <InfoTip label="a step weight" title="Step weight">
                    <StepWeightExplain />
                  </InfoTip>
                </span>
              </th>
              <th className="w-[160px] px-5 py-3">
                <span className="inline-flex items-center">
                  Score
                  <InfoTip label="a step score" title="Step score">
                    <StepScoreExplain />
                  </InfoTip>
                </span>
              </th>
              <th className="px-5 py-3">Basis</th>
            </tr>
          </thead>
          <tbody>
            {payload.steps.map((step) => (
              <tr
                key={step.key}
                className="border-b border-line last:border-b-0"
              >
                <td className="px-5 py-3.5 align-top">
                  <span className="mr-2 font-mono text-[12px] text-muted-2">
                    {String(step.sn).padStart(2, "0")}
                  </span>
                  <span
                    className={`font-sans text-[14px] ${step.assessed ? "text-text" : "text-muted-2"}`}
                  >
                    {step.title}
                  </span>
                </td>
                <td className="px-5 py-3.5 align-top font-sans text-[13px] text-muted tabular-nums">
                  {step.weight}%
                </td>
                <td className="px-5 py-3.5 align-top">
                  <LadderMeter score={step.score} />
                  {step.assessed && step.level_label && (
                    <span className="mt-0.5 block font-sans text-[12px] text-muted">
                      {step.level_label}
                    </span>
                  )}
                </td>
                <td className="px-5 py-3.5 align-top font-sans text-[13px] leading-relaxed text-muted">
                  {step.reason}
                  {step.refined && step.refinement_reason && (
                    <span className="mt-1.5 block text-[12.5px] text-text">
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

      <HowItWorks title="Notes — cycle shape, pointers, coverage">
        {payload.shape_note && (
          <p>
            <strong>Cycle shape. </strong>
            {payload.shape_note}
          </p>
        )}
        {payload.pointers.length > 0 && (
          <div>
            <p className="flex items-center">
              <strong>Pointers</strong>
              <InfoTip label="the pointers" title="How pointers are chosen">
                <PointersExplain />
              </InfoTip>
            </p>
            <ul className="mt-1 list-disc space-y-1 pl-5">
              {payload.pointers.map((pointer, i) => (
                <li key={`${pointer.kind}-${i}`}>
                  <span className="font-medium text-text">
                    {POINTER_LABELS[pointer.kind]}:{" "}
                  </span>
                  {pointer.text}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p>{payload.coverage_note}</p>
        <p className="text-[12px] text-muted-2">
          {payload.disclaimer} Generator: {payload.generator} · questionnaire v
          {payload.questionnaire_version} · model {payload.model_ref}.
        </p>
      </HowItWorks>
    </div>
  );
}
