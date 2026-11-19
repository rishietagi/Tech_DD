# DD_ASSESSMENT_FRAMEWORK.md — how the platform assesses, and why

The reference for Phase 8 (2026-11-18): how the four estate assessments — applications, data
& infrastructure, team & governance, strategy & projects — and the IT budget turn evidence
into findings, and where each question comes from. The question text itself lives in
`backend/app/reference/estate/*.yaml`; this file explains the model and cites the sources.

`[EXT]` marks practice added by us rather than taken from the book (`DD_master.md`).
Thresholds and weights are calibrations to tune, not authorities.

---

## 1. A due diligence is not an architecture review

The book defines the job [DD_master §1.1, p. 70]: identify matters that can have a
**material impact on the value of the target** — previously unknown risks, one-time IT
costs, recurring IT costs, and IT-enabled synergies. A deal team acts on findings framed
that way. A defect list per system ("SAP: modernise; WMS: replace") is the output of an
enterprise-architecture review, a different engagement with different time and access.

Rishi's review of Phases 6–7 against a real KPMG Gaps & Risks deck (2026-11-18) found the
platform reading like the second. Phase 8 changed three things:

1. **No dispositions.** Applications are no longer scored on business and technical fit,
   and nothing is labelled Invest / Retain / Modernise / Replace / Consolidate.
2. **Registers hold themes, not items.** Every rule still looks at every application,
   platform, role and project; what it finds is an **observation**. Observations are
   grouped under **themes** — "Critical applications facing end-of-support risks", "IT
   roadmap not funded" — and the theme is the finding. A test pins that no register holds a
   per-item gap.
3. **Two new assessments**, team & governance and strategy & projects, because a diligence
   that looks only at systems misses the people, governance and money that decide whether
   the plan can be delivered.

## 2. The finding model

```
inventory facts ─┐
analyst answers ─┼─► observations ─► themes (one gap each) ─► executive summary
reconciliations ─┘     (evidence)      headline · evidence ·      one row per finding,
                                       implication · impact ·     grouped by diligence area
                                       action · severity
```

A theme (`themes:` in each assessment's YAML) carries:

| Field | What it is |
|---|---|
| `headline` | The finding as a noun phrase, the way the sample deck heads a row |
| `implication` | Why it matters to the deal, in one sentence |
| `impact` | The **deal-impact lens** — one or more of the six below |
| `action` | "Target should…", naming the subjects of the most severe observations |
| `area` | The diligence area of the executive summary (`reference/report/report.yaml › areas`) |
| `severity` | The default for observations that do not state their own |

**The deal-impact lens** makes "strategic" explicit. It is the book's p. 70 list, plus the
two practitioner categories every PE diligence uses (one-off versus recurring cost) [EXT]:

| Lens | Meaning |
|---|---|
| `one_off_investment` | A one-time cost the plan will have to fund — comes off the price |
| `run_cost` | A recurring cost — moves the run-rate, and so the multiple |
| `plan_risk` | Puts the value-creation plan at risk |
| `continuity` | Threatens continuity of operations |
| `compliance` | Regulatory or contractual exposure |
| `integration` | A dependency for integration, separation or Day 1 |

**One severity rule for every theme:** High — threatens continuity of a critical operation,
creates regulatory exposure, or is an unfunded investment the plan depends on. Medium —
constrains the plan or adds cost. Low — an improvement. A theme's severity is the highest
of its observations'.

**Information not provided is a data limitation, not a finding.** An incomplete inventory, a
check marked "unknown", a missing projects list — each goes to the report's Data
Limitations section, routed by workstream, never into a register.

**Facts versus judgement** (Phase 6, carried forward). The target supplies facts on the
Information requests page; the analyst supplies judgement in Assess. A test bans any field
in an inventory that asks the target to rate itself — fit, maturity, criticality, triage.

## 3. Applications

Asked per application: **criticality** (1–5), **automation** (0–5, the business-process
ladder) and **AI level** (0–5). Asked once: four portfolio questions — core-platform
fitness for the plan, integration between core systems, how management reporting is
produced, and application ownership [DD_master §6.6, p. 75].

Themes and what raises them:

| Theme | Raised by |
|---|---|
| Critical applications facing end-of-support risks | lifecycle "End of life within 24 months" (High where business-critical) |
| Core platform requires upgrade to support the plan | AQ1 |
| Fragmented application landscape with functional overlaps | two or more applications in one functional category; AQ4 |
| Heavy customisation constraining upgrades | high customisation on a business-critical application |
| Lack of integration between core systems | AQ2; inventory fact "manual re-keying" |
| Incomplete digitisation of business processes | a scored process with no supporting system; business-critical work on a spreadsheet; automation ≤ 1 on a critical application |
| Licensed system capability not used | a process scored Manual/Emerging while systems claim to support it |
| Limited analytics tool adoption | AQ3; no BI application in an inventory of five or more |
| AI adoption limited to embedded tool features | mean AI level ≤ 1 across three or more rated applications |

The index is the criticality-weighted automation index (unchanged). Key-person and recovery
facts on applications feed the team and infrastructure themes, where they belong.

## 4. Data & infrastructure

Renamed from "Data & technology". Domain and platform questions and the estate checks are
as in Phase 6, plus five checks drawn from the shape of real cyber request lists: IF1 asset
lifecycle and funded refresh; CY9 penetration test in the last 12 months; CY10 awareness
training and phishing simulation; CY11 DLP and MDM; CY12 certification (ISO 27001, SOC 2).

Every check names its theme: recovery, operations, asset lifecycle, engineering, cyber
governance, identity and access, threat management, user-level controls, third-party
security. Domains and platforms raise privacy, data ownership, data quality, infrastructure
support, capacity and recovery. Business-critical applications with weak recovery or that
fail at peak raise recovery and capacity observations here.

**A tool is not a control.** The cyber tools inventory (a checklist of purposes, mapped to
checks in `data_tech.yaml › tool_checks`) is shown beside each check as evidence. A tool the
target says it lacks defaults the check to *fail* until the analyst answers; a tool it has
passes nothing. This is the same licence-versus-use logic the process assessment applies.

## 5. Team & governance

Facts counted from the IT team and IT contracts inventories: headcount, in-house /
outsourced / contractor / parent mix, sole holders, **business-critical applications
supported by exactly one person**, share of the team under a year's service, contracts
ending within 12 months, change-of-control clauses, parent-held contracts.

The questionnaire, by section, with sources:

| Section | Questions | Sources |
|---|---|---|
| Leadership and accountability | dedicated IT leader; security accountability; dependency on parent-group IT | DD_master W-OPS p. 73 ("Is IT leadership capable…", "lack of a dedicated leader"); COBIT 2019 EDM01, APO01, APO13 [EXT]; separation dependencies §6.10 |
| Governance and decision rights | steering committee; review of new technology before adoption; policies; KPI/SLA reporting; governance of outsourced services | COBIT EDM01, APO01, APO10 [EXT]; TOGAF architecture board, as a governance idea only [EXT]; DD_master W-PROC p. 73 ("How often are IT operations metrics reviewed?"), W-VEN p. 73 |
| Organisation and capacity | sized for the plan; skills for the roadmap; attrition | DD_master W-OPS p. 73 ("sufficient to support … expected growth", "mix of staff skills", "abnormally high staff turnover") |
| People risk | cross-training; succession; documentation; retention through the deal | DD_master W-OPS p. 73 ("redundancy or cross-training", "succession plans"); Ch. 20 p. 362; p. 121 on job approaches after announcement |
| Product engineering *(product and blended deals only)* | bus factor on the core codebase; IP in contractor code; product-management ownership | DD_master W-PROD §6.12; practitioner product-DD sources [EXT] |

Where a fact and an answer speak to the same thing, the answer wins: a blank "IT
leadership" row on the target's sheet is weaker evidence than the management interview.

## 6. Strategy & projects

Facts from the projects inventory (the target's in-flight projects template): status,
dates, allocated capex, capex utilised, % complete, delivery model, vendor, applications
affected, business case. Per project, the analyst records **deal relevance** — the book's
triage rule [DD_master p. 8, 148]: Day-1 critical / enables the plan / business as usual /
candidate to stop or defer — and **delivery confidence**.

Computed on the target's own figures (never a cost estimate — 2026-09-14 boundary):

| Rule | Theme |
|---|---|
| capex used > allocated; past the planned date; re-planned later; analyst says off track | In-flight projects over budget or behind schedule |
| share spent − % complete > 25 points [EXT] | Project spend running ahead of delivery |
| remaining allocation on in-flight and planned projects > the latest change budget on the IT budget tab (scaled by the budget's unit); projects with no allocation | IT roadmap not funded |
| projects tagged candidate to stop or defer, with their share of remaining allocation | In-flight spend not aligned to the plan |
| one vendor > 50% of in-flight allocation | Project delivery concentrated on one vendor |
| open projects with no approved business case | No centralised project management office |

The questionnaire: IT strategy (exists and approved; who develops it; alignment; **is it
funded**; roadmap detail; refresh) [DD_master W-STRAT p. 74; COBIT APO02 EXT; Implement];
portfolio governance (prioritisation; PMO and tool; stage-gates; benefits tracking) [COBIT
APO05, BAI01 EXT; Implement]; delivery track record; AI (strategy; governance and
acceptable use; and, where AI is material — scope rule A11 — training-data rights,
third-party model dependency and model monitoring) [PD-12; AI diligence checklists EXT].

## 7. IT budget

Unchanged in substance (budgeting process, never a cost model). Its findings now group
into six themes — process not formalised, no business cases, spend outside IT, budget not
tied to the plan, variance against budget, unexplained movement — so the report treats them
like every other finding. The target can supply budget and actuals on the **IT financials**
sheet (IRL workbook or standalone template); an upload never clears a figure.

## 8. Product, enterprise and AI variants

By rule, not by separate modules. `applies_to` limits a question to DD types; `requires_ai`
to deals where AI is material. Product and blended deals add the engineering-team
questions; AI-material deals add the AI rights and dependency questions. The report's
supporting analysis differs by DD type as in Phase 7, with *IT organisation and governance*,
*IT strategy and project portfolio* and *AI adoption* sections added.

## 9. What was searched for and not found

- **No primary standard defines a tech-DD finding format or severity scale.** The
  categorisations used (deal breaker / red flag / value-creation opportunity; one-off versus
  recurring) come from practitioner and adviser sources, not a standards body. The lens and
  severity rule above are ours [EXT].
- **No published question bank for in-flight project review** was found complete enough to
  adopt. The project rules combine the book's triage rule with Implement's portfolio-health
  dimensions [EXT].
- **The 25-point burn gap, 50% outsourcing and vendor shares, 30% short-tenure share and
  attrition bands are calibrations** with no external source. Tune them per engagement.
- **TOGAF and COBIT** are used for the governance questions they imply, not for maturity
  scoring or architecture modelling, which would be out of place in a diligence.

## Sources

- Roehl-Anderson, *M&A Information Technology Best Practices* (Wiley, 2013), via
  `docs/reference/DD_master.md`.
- ISACA, COBIT 2019 Framework: Governance and Management Objectives (EDM01, APO01, APO02,
  APO05, APO07, APO10, APO13, BAI01).
- The Open Group, TOGAF Standard — architecture governance and the architecture board.
- Implement Consulting Group, IT due diligence framework (strategy, portfolio management,
  people and organisation, IT financials).
- Practitioner tech-DD sources on key-person risk, red-flag categories and one-off versus
  recurring cost.
- AI-in-M&A diligence checklists (Orrick; McCarter & English; Promise Legal; Datasite).
