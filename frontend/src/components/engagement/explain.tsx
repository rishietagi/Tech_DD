/**
 * What every computed number means and how it is derived — the text behind the ⓘ icons
 * (Rishi, 2026-11-19: "more explainability in the whole app").
 *
 * Kept in one file so the wording stays consistent and a reviewer can check it against the
 * backend in one sitting. Each block names the rule as the code implements it:
 *   process index      services/assess/scoring.py
 *   estate indices     services/estate/{applications,data_tech,judgement,strategy_projects}.py
 *   themes / severity  services/estate/gaps.py
 *   request priority   services/checklist/ranking.py
 *   archetype mix      services/scope/scoring.py + reference/scope_rules.yaml
 *   report risk        services/report/{findings,service}.py
 * Where a weight or threshold lives in YAML and the payload carries it, the component
 * shows the live value rather than repeating it here.
 */
import { Formula, Scale } from "@/components/ui/info-tip";

export const AUTOMATION_BANDS: [string, string][] = [
  ["0–20", "Manual — people and spreadsheets"],
  ["21–40", "Emerging — systems exist, the work is still human"],
  ["41–60", "Standardised — system-mediated, with real gaps"],
  ["61–80", "Integrated — end to end, exceptions by hand"],
  ["81–100", "Optimised — automated, people handle exceptions"],
];

export const MATURITY_BANDS: [string, string][] = [
  ["0–20", "Initial"],
  ["21–40", "Developing"],
  ["41–60", "Defined"],
  ["61–80", "Managed"],
  ["81–100", "Optimised"],
];

export const LADDER: [string, string][] = [
  ["0", "Manual"],
  ["1", "Recorded"],
  ["2", "Standardised"],
  ["3", "Integrated"],
  ["4", "Automated"],
  ["5", "Optimised"],
];

/* ------------------------------------------------------------- business processes */

export function ProcessIndexExplain() {
  return (
    <>
      <p>
        Each step is scored 0–5 as the{" "}
        <strong>mean of its answered scoring questions</strong>. The index is
        the weighted mean of the assessed steps, scaled to 100.
      </p>
      <Formula>
        index = Σ(step score × step weight) ÷ Σ(weights of assessed steps) × 20
      </Formula>
      <p>
        An unanswered question is left out, not scored as zero. A step with no
        answers is &ldquo;not assessed&rdquo; and its weight is shared across
        the rest, so a half-finished questionnaire cannot produce a confident
        low number.
      </p>
      <Scale rows={AUTOMATION_BANDS} />
    </>
  );
}

export function StepWeightExplain() {
  return (
    <p>
      The step&rsquo;s share of the process, from its automation model: what the
      step carries in volume, financial exposure or what breaks when it is
      manual. Weights sum to 100% across the process.
    </p>
  );
}

export function StepScoreExplain() {
  return (
    <>
      <p>
        The mean of the option scores (0–5) of the step&rsquo;s answered scoring
        questions, to one decimal. Fewer than half answered is flagged as thin
        coverage.
      </p>
      <Scale rows={LADDER} />
    </>
  );
}

export function RefinementExplain() {
  return (
    <p>
      With AI on, the model may move a step by <strong>at most ±1</strong>, and
      only with a stated reason drawn from the recorded evidence. The rules
      score is always kept beside it. This is the only place in the platform
      where the model may change a number.
    </p>
  );
}

export function PointersExplain() {
  return (
    <Scale
      rows={[
        ["Gap", "an assessed step at 2.0/5 or below, heaviest weight first"],
        ["Strength", "a step at 3.5/5 or above"],
        [
          "Probe next",
          "unassessed steps, heaviest first, and steps answered on under half their questions",
        ],
      ]}
    />
  );
}

/* ------------------------------------------------------------- estate indices */

export function ApplicationsIndexExplain() {
  return (
    <>
      <p>
        Each application&rsquo;s automation level (0–5) weighted by its
        criticality (1–5), scaled to 100. Critical systems count more: a manual
        ERP matters more than a manual intranet.
      </p>
      <Formula>
        index = Σ(automation × criticality) ÷ Σ(criticality) × 20
      </Formula>
      <p>
        An application with no criticality counts as 3. One with no automation
        level is left out. Spreadsheets do not count as supporting systems.
      </p>
      <Scale rows={AUTOMATION_BANDS} />
    </>
  );
}

export function AiIndexExplain() {
  return (
    <>
      <p>
        The same arithmetic as the automation index, on the AI level of each
        application.
      </p>
      <Formula>
        AI index = Σ(AI level × criticality) ÷ Σ(criticality) × 20
      </Formula>
    </>
  );
}

export function DataTechIndexExplain() {
  return (
    <>
      <p>
        A weighted mean of five sections. The weights are shown on each section
        card.
      </p>
      <Scale
        rows={[
          ["Data", "mean of the data-domain scores"],
          ["Platforms", "mean of the infrastructure-platform scores"],
          [
            "Checks",
            "resilience, engineering, cyber: pass 100, partial 50, fail 0",
          ],
        ]}
      />
      <Formula>
        index = Σ(section × weight) ÷ Σ(weights of sections with evidence)
      </Formula>
      <p>
        &ldquo;Unknown&rdquo; is left out of the score: it is a data limitation,
        not a finding. A section with no evidence drops out and the rest are
        re-weighted.
      </p>
      <Scale rows={MATURITY_BANDS} />
    </>
  );
}

export function QuestionnaireIndexExplain({
  extra,
}: {
  extra?: React.ReactNode;
}) {
  return (
    <>
      <p>
        Each answer option carries a value from 0 to 1. A section is the
        weighted mean of its answered questions, on 0–100. The index is the
        weighted mean of the sections.
      </p>
      <Formula>
        section = Σ(option value × question weight) ÷ Σ(weights answered) × 100
      </Formula>
      <Formula>
        index = Σ(section × section weight) ÷ Σ(weights of sections answered)
      </Formula>
      {extra}
      <p>Unanswered questions are left out; a section with none drops out.</p>
      <Scale rows={MATURITY_BANDS} />
    </>
  );
}

export function TeamIndexExplain() {
  return (
    <QuestionnaireIndexExplain
      extra={
        <p>
          The people facts (headcount, sole holders, single-supporter
          applications) do not move the index. They raise findings directly. The
          product-engineering section is asked on Product and Blended deals
          only.
        </p>
      }
    />
  );
}

export function StrategyIndexExplain() {
  return (
    <QuestionnaireIndexExplain
      extra={
        <p>
          <strong>Project delivery</strong> is the share of in-flight projects
          with none of Over budget, Late, Spend ahead of delivery or Off track.
          It is added as a section when projects are in flight. The AI
          data-rights questions are asked only where AI is material.
        </p>
      }
    />
  );
}

export function SectionsExplain() {
  return (
    <p>
      Each card is one section on 0–100. Its weight is how much it counts
      towards the index. A section with no evidence is excluded and the others
      are re-weighted, rather than being scored as zero.
    </p>
  );
}

export function DomainScoreExplain() {
  return (
    <p>
      The weighted share of the best answer earned across the domain&rsquo;s
      answered questions (ownership, quality, classification and so on), on
      0–100. &ldquo;Not applicable&rdquo; earns full marks.
    </p>
  );
}

export function PlatformScoreExplain() {
  return (
    <p>
      The mean of the platform&rsquo;s answered question values (support,
      recovery, capacity and so on), on 0–100. &ldquo;Not applicable&rdquo;
      earns full marks.
    </p>
  );
}

export function ChecksExplain() {
  return (
    <>
      <Scale
        rows={[
          ["Pass", "100 — in place and evidenced"],
          ["Partial", "50 — raises a Medium observation"],
          [
            "Fail",
            "0 — raises a High observation (Medium for most engineering checks)",
          ],
          ["Unknown", "left out of the score, reported as a data limitation"],
        ]}
      />
      <p>
        <strong>A tool is not a control.</strong> A cyber tool the target says
        it lacks fails its check until the analyst answers. A tool it has passes
        nothing: it is evidence only.
      </p>
    </>
  );
}

/* ------------------------------------------------------------- facts and flags */

export function CriticalityExplain() {
  return (
    <p>
      1–5, the analyst&rsquo;s judgement of how much the business depends on the
      system. 4 or above counts as business-critical. It weights the automation
      and AI indices.
    </p>
  );
}

export function AutomationLevelExplain() {
  return (
    <>
      <p>
        How much of the work the system does without a person, on the same
        ladder as the business processes.
      </p>
      <Scale rows={LADDER} />
    </>
  );
}

export function AppFlagsExplain() {
  return (
    <Scale
      rows={[
        ["End of life", "vendor support ends within 24 months"],
        ["High customisation", "customisation reported as High"],
        ["Manual re-keying", "data moves between systems by hand"],
        ["Spreadsheet", "the ‘application’ is a spreadsheet"],
        ["Key person", "only one person can support it"],
        ["Weak recovery", "no DR, or backup only"],
        ["Fails at peak", "does not hold at peak load"],
      ]}
    />
  );
}

export function CriticalManualExplain() {
  return (
    <p>
      Applications with criticality 4 or 5 and an automation level of 1 or
      below: business-critical work still done by hand around the system.
    </p>
  );
}

export function ProjectFlagsExplain() {
  return (
    <Scale
      rows={[
        ["Over budget", "capex used is above the allocation"],
        ["Late", "past the planned date and not complete, or re-planned later"],
        [
          "Spend ahead of delivery",
          "% of allocation spent minus % complete above 25 points",
        ],
        ["Off track", "the analyst's delivery confidence"],
        ["No budget", "in flight or planned with no allocation"],
        ["No business case", "the target says none was approved"],
        ["Stop candidate", "triaged as a candidate to stop or defer"],
      ]}
    />
  );
}

export function TriageExplain() {
  return (
    <p>
      The analyst&rsquo;s triage of each project for the deal (Roehl-Anderson
      pp. 8, 148): Day-1 critical, enables the plan, business as usual, or a
      candidate to stop or defer.
    </p>
  );
}

export function ReconciliationExplain() {
  return (
    <>
      <p>
        The roadmap is checked against the change budget on the IT budget tab.
        This is arithmetic on the target&rsquo;s own figures, not a cost model.
      </p>
      <Formula>
        remaining = Σ max(allocated − used, 0) over in-flight and planned
        projects
      </Formula>
      <Formula>
        short by = remaining − latest change budget (scaled by its unit)
      </Formula>
      <p>
        If the budget&rsquo;s unit (thousand, lakh, million, crore, billion)
        cannot be read, no comparison is made.
      </p>
    </>
  );
}

export function KeyPersonExplain() {
  return (
    <p>
      From the IT team sheet: roles held by exactly one person, and
      business-critical applications (criticality 4+) that only one person
      supports. Either one raises a key-person finding, and a critical
      application raises it as High.
    </p>
  );
}

export function OutsourcedExplain() {
  return (
    <Formula>
      (outsourced + contractor + parent-shared roles) ÷ all roles × 100
    </Formula>
  );
}

/* ------------------------------------------------------------- findings */

export function ThemesExplain() {
  return (
    <>
      <p>
        Rules fire on single applications, platforms, roles, projects and
        answers. These are
        <strong> observations</strong>. Observations are grouped into{" "}
        <strong>themes</strong>, and only themes are reported, so the register
        reads as strategic findings rather than one gap per system.
      </p>
      <p>
        A theme&rsquo;s severity is the{" "}
        <strong>highest of its observations</strong>. Its action names the
        subjects of the worst ones. Edits survive re-scoring, and the rules
        version is kept beside yours.
      </p>
    </>
  );
}

export function SeverityExplain() {
  return (
    <Scale
      rows={[
        [
          "High",
          "threatens continuity of a critical operation, regulatory exposure, or an unfunded investment the plan depends on",
        ],
        ["Medium", "constrains the plan or adds cost"],
        ["Low", "an improvement"],
      ]}
    />
  );
}

export function ImpactExplain() {
  return (
    <>
      <p>
        How the finding could move the value of the deal (Roehl-Anderson p. 70):
      </p>
      <Scale
        rows={[
          ["One-off investment", "a capital cost, usually off the price"],
          ["Run cost", "recurring cost, which hits the multiple"],
          ["Plan risk", "the value-creation plan may not deliver"],
          ["Continuity", "operations could stop"],
          ["Compliance", "regulatory or contractual exposure"],
          ["Integration", "a dependency to separate or integrate"],
        ]}
      />
    </>
  );
}

/* ------------------------------------------------------------- IT budget */

export function BudgetVarianceExplain({
  tolerance,
  movement,
}: {
  tolerance: number;
  movement: number;
}) {
  return (
    <>
      <Formula>variance % = (actual − budget) ÷ budget × 100</Formula>
      <p>
        Beyond ±{tolerance}% is flagged: Low, or Medium beyond ±{tolerance * 2}
        %. Year-on-year movement in actual spend beyond {movement}% is flagged
        for management to explain.
      </p>
      <p>
        Totals compare only the lines with both a budget and an actual. There is
        no share of revenue and no benchmark: this reviews the budgeting
        process, not a cost model.
      </p>
    </>
  );
}

/* ------------------------------------------------------------- requests */

export function PriorityExplain() {
  return (
    <>
      <p>
        Each request inherits its importance from the scope area that asked for
        it:
      </p>
      <Scale
        rows={[
          [
            "Critical",
            "security, privacy or regulatory evidence, at any depth",
          ],
          ["High", "seeds a deep-dive area, or a legal / finance request"],
          ["Medium", "seeds an assessed area"],
          ["Low", "seeds a screened area, or supporting context"],
        ]}
      />
      <p>Hover a priority badge to see the reason for that request.</p>
    </>
  );
}

export function CollectedExplain() {
  return (
    <>
      <Formula>
        collected = tracked requests received in full ÷ all tracked requests ×
        100
      </Formula>
      <p>
        Partial arrivals are counted separately and do not count towards the
        percentage. &ldquo;Answered&rdquo; counts requests with a written
        response. &ldquo;Follow-ups&rdquo; are the questions the shared-drive
        scan raised where a file only partly covers a request.
      </p>
      <p>
        Statuses come from the analyst or the shared-drive scan. The scan never
        overwrites a status a person set.
      </p>
    </>
  );
}

/* ------------------------------------------------------------- scope */

export function MixExplain() {
  return (
    <>
      <p>
        0 is a pure Enterprise DD and 100 a pure Product DD. Each archetype rule
        that fires adds or subtracts points from a start of 50, damped and
        clamped.
      </p>
      <Formula>mix = clamp(50 + round(Σ rule deltas × 0.55), 0, 100)</Formula>
      <Scale
        rows={[
          ["0–34", "Enterprise"],
          ["35–65", "Blended"],
          ["66–100", "Product"],
        ]}
      />
      <p>
        A declared DD type on the intake decides which deck ships. The computed
        mix stays visible, so any disagreement can be seen.
      </p>
    </>
  );
}

export function ConfidenceExplain() {
  return (
    <p>
      How much the computed mix can be trusted. It rises with the number of
      archetype rules that fired and their combined weight. It drops a level
      when strong rules pull towards both archetypes. Inputs the intake does not
      capture are reported, not penalised.
    </p>
  );
}

/* ------------------------------------------------------------- report */

export function ReportRiskExplain() {
  return (
    <>
      <p>
        A finding&rsquo;s risk is its theme&rsquo;s severity. For a business
        process it comes from the automation band: Manual is High, Emerging is
        Medium. An area&rsquo;s risk is the highest of its findings, and it
        follows any edit you make to a finding.
      </p>
      <p>
        An assessed area with no findings shows Low; an area with no evidence
        shows &ldquo;Not assessed&rdquo;.
      </p>
    </>
  );
}

export function InvestmentExplain() {
  return (
    <p>
      Left as XXX on purpose. Investment impact is the engagement team&rsquo;s
      estimate. The platform does not size costs: the IT financials boundary
      rules out a cost model.
    </p>
  );
}
