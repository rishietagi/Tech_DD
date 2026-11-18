# Estate assessment model — applications, data & technology, IT budget

**Status:** reference for Phase 6 (`docs/phases/PHASE6_PLAN.md`). Read beside
`DD_master.md`.

**Provenance, stated plainly.** Where a rule or a field traces to the Roehl-Anderson
source it is cited `[p. N]` via `DD_master.md`. The scoring arithmetic, thresholds and the
AI ladder are **[EXT]** — built for this platform, calibrations to be tuned rather than
authorities. The structure (intake → fit quadrant → disposition → technical health →
gap register) is adapted from Rishi's CIL EA tool, which grounds itself in TOGAF 9.1;
**those TOGAF references were not re-verified here** and are not cited.

---

## 1. What each assessment is for

| Assessment | The diligence question | Unit assessed |
|---|---|---|
| Applications | Which systems will carry the plan, which must be replaced or rebuilt, and where is the business still doing by hand what a system should do? [p. 75] | One application |
| Data & technology | Is the data governed well enough to trust, and will the platforms underneath stay supported, recoverable and secure through the hold? [p. 76, p. 167–172] | One data domain, one platform, plus estate-level checks |
| IT budget | Is technology spend planned, approved and controlled — and did it come in where it was planned? [p. 74] | The budgeting process, over the review period |

## 2. Intake vs assessment — who supplies what

**The target supplies facts; the analyst supplies judgement.** The inventory the target
completes is the *"inventory of software applications, including primary business
functionality, version and licenses, customization, platform/architecture, level of
scalability and redundancy, and hosting and support arrangements"* requested verbatim on
[p. 83]. It carries no fit scores: a target asked to rate its own systems rates them well.
The fit, automation and AI questions are asked of the analyst, after management meetings.

## 3. Applications

### 3.1 Inventory fields
Identity (name, description, vendor, version, category, type), ownership (business and IT
owner, users), the processes it supports, hosting and platform, commercial (licence model,
support arrangement, contract end), lifecycle (status, planned retirement), resilience
(redundancy/DR, failover tested in the last 12 months), and four technical-health facts
(customisation, peak-load handling, key-person dependency, known issues). Every field
except name is optional; an unknown vendor is recorded as *TBD*, never guessed.

### 3.2 Analyst questions
- **Business fit** (1–5): functional fit, fit with the investment plan, user satisfaction.
  The source's rationalisation criteria — *"business criticality… applicability to current
  and future processes… operational supportability… vendor viability… usage, maintenance
  and licensing cost"* [p. 64] — and its scoring model on *functionality, supportability
  and cost* [p. 196].
- **Technical fit** (1–5): technology currency, integration readiness, security and
  compliance, supportability. **[EXT]** split.
- **Automation level** (0–5): the same ladder as the business processes — Manual,
  Recorded, Standardised, Integrated, Automated, Optimised — so an application's number and
  a process's number mean the same thing.
- **AI level** (0–5) **[EXT]**: None · Available, unused · Piloted · In production ·
  AI-led with oversight · Agentic within guardrails.
- **Business criticality** (1–5) — asked here rather than in the intake for the same
  reason as the fit scores.

### 3.3 Disposition
Business fit = mean of the answered business-fit questions; technical fit likewise.
Threshold **3.0**:

| | Technical fit ≥ 3 | Technical fit < 3 |
|---|---|---|
| **Business fit ≥ 3** | Invest | Modernise |
| **Business fit < 3** | Retain | Replace |

Then, in order: **end of life within 24 months** turns Invest or Retain into Modernise;
**duplication** (two or more in-scope applications of the same category) turns every one
but the survivor into Consolidate — survivor is highest business fit, then criticality. An
application with no business-fit or no technical-fit answer is **Not assessed** — never
scored as zero, the same rule as the business processes.

### 3.4 Technical health (from intake, deterministic)
- **Technical debt** 0–100 from customisation, lifecycle and the technical-fit currency
  answer, banded High ≥ 60, Medium ≥ 35. *"Buildup of technical debt"* and *"heavy
  customisation that makes upgrade difficult"* are named common findings [p. 75].
- **Single point of failure** — criticality ≥ 4 with no DR or backup only; any key-person
  dependency; criticality ≥ 4 whose failover has never been tested is a *check*.
- **Scalability** — slows or fails at peak; fixed capacity on a critical system. *"System
  not readily scalable"* [p. 75].

### 3.5 Gaps
Item gaps, one per application, combining every finding: a Modernise / Replace /
Consolidate disposition, high debt, SPOF, scalability risk, end of life within 24 months,
contract ending within 12 months, and manual work around a critical system (automation ≤ 1
on criticality ≥ 4). Severity is the highest finding; criticality ≥ 4 lifts most findings
to High. A disposition subsumes the remediations it makes moot: a Replace or Consolidate
gap's hypothesis is the disposition alone, and Modernise drops "upgrade" and "move off the
ending release". A statement that calls the technology sound carries the single point of
failure or peak-load caveat, so the disposition never contradicts its own row.

Portfolio gaps: duplication by category; **a business process with no supporting system**
(*"are there any areas where system support is lacking (i.e. require manual processes)?"*
[p. 75]); **a business process scored Manual or Emerging despite supporting systems**, the
licence-versus-use gap (High when Manual, Medium when Emerging); key-person concentration
across two or more applications; and an incomplete inventory (vendors or lifecycle unknown
on a third or more of applications). Both process gaps fire only for a process the analyst
has scored on the business tab, since that is the evidence it matters to this target. A
spreadsheet or ad hoc tool is not a supporting system: a process carried only by one has
no supporting system, and the spreadsheet is named.

## 4. Data & technology

### 4.1 Inventories
**Data domains** — name, description, data types, sensitivity, system of record (an
application from the inventory), named business owner, regulatory regimes, volume and
retention. **Platforms** — name, vendor, version, category, hosting location, lifecycle,
vendor end of support, applications hosted. The infrastructure inventory list on [p. 92]
is the source of the category vocabulary.

### 4.2 Analyst questions
- **Per data domain:** ownership and stewardship (*an executive owner and a data steward
  per domain* [p. 167–168]); master data management; data quality (the source's five
  questions — completeness, consistency, duplicates, currency, corruption [p. 170] —
  answered as one 1–5 judgement); lineage; privacy classification and retention.
  Domain score 0–100: ownership 25, master data 20, quality 30, lineage 10, classification
  15. Classification points are granted where the domain holds no personal data.
- **Per platform:** support status, patch currency, recoverability, capacity headroom.
  Each option carries a value from 0 to 1; platform score = mean of the answered values
  × 100.
- **Estate checks** (pass / partial / fail / unknown): resilience (DR for tier-1, tested
  RPO/RTO, restore-tested backups, central monitoring) — *"limited or no disaster recovery
  capability"* is a named common finding [p. 76]; engineering practice **[EXT]**; cyber
  security controls, including access revocation for leavers, which is the mechanism H2R
  assesses. Pass 100, partial 50, fail 0; **unknown is excluded and becomes a
  validate-in-diligence gap**.

### 4.3 Index
Weighted mean of the section scores that have evidence — data 30, platforms 20,
resilience 20, engineering 10, cyber 20 — mapped onto the same five bands as the business
processes. A section with no evidence drops out and its weight is redistributed.

### 4.4 Gaps
Item gaps per domain (personal data unclassified — High; no owner; score < 60), per
platform (out of support or end of life within 24 months — High; ageing; lifecycle
unknown), per check (fail High, partial Medium, unknown Low; an engineering fail is
Medium except security testing). A check gap carries the consultant's remark as part of its
finding. A domain's ownership is the analyst's answer where there is one, and the target's
intake field only otherwise. A facility (a data centre) gets a capacity and recovery
hypothesis, not a "supported release" one. Portfolio gaps: data ownership not established
across two or more domains; **applications hosted on platforms out of support** (joins the
two inventories); platform lifecycle unknown on a third or more; two or more domains with
no system of record. The register reads severity first, then item before portfolio.

## 5. IT budget

**The boundary (2026-09-14, restated).** This reviews the **budgeting process** — how the
technology budget is defined, agreed and approved, and reported spend against it. It does
not build, validate or benchmark a cost model, and it shows **no percentage of revenue
and no industry band**. The source supports the restraint: *"the team should utilize
benchmarks with care, as factors unique to each organization's specific situation can
significantly impact a company's actual spending needs"* [p. 81].

**Review period:** three financial years by default [house rule], editable.

**Inputs:** for each year, budget and actual for each line as the target reports it —
operating spend, technology personnel, capital spend, and any further lines the analyst
adds. Each line is classed run or change.

**Computed:** variance per line per year (actual vs budget); lines outside tolerance
(±10%); *"significant variances in the operating budget year-over-year"* [p. 74] —
consecutive-year movement in actual spend beyond 20%; the run/change mix as reported;
lines without a budget. The year's total variance is like-for-like: it compares only lines
carrying both figures, because unbudgeted spend is already its own finding and would
otherwise read as an overrun of the budgeted lines.

**Budgeting-process questions:** how the budget is built, who approves it, how often spend
is reported against it, whether capital spend needs an approved business case, whether
technology spend outside IT is captured, and whether the budget is tied to the technology
plan. Each weak answer raises a finding; none produces a score.

## 6. What was searched for and not found

`DD_master.md` was searched for an application scoring threshold, a data-governance
weighting, an AI-maturity ladder and a variance tolerance. It has none of them. The 3.0
threshold, the domain weights, the AI ladder, the ±10% / 20% tolerances and the section
weights are **[EXT]** and should be tuned against real engagements.
