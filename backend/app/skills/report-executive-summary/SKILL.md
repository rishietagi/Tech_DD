---
name: report-executive-summary
description: >-
  Rewrites each executive-summary finding — its headline, evidence bullets and implication
  — in the voice of a KPMG IT due diligence report. The rules have already decided the
  findings, the diligence area each belongs to, the risk level, the recommended actions and
  the investment cell.
version: "2.0"
mode: prose_only
deterministic_fallback: services/report/findings.py::executive_rows
used_by: [services/report/llm.py::ReportWriter.executive]
inputs: [target name, DD type, per finding — key, headline, evidence bullets, implication]
outputs: [per finding — headline, bullets, implication]
may_change: [wording of the headline, the bullets and the implication]
must_not_change:
  - which findings exist, their area and their order
  - the risk level (not shown)
  - recommended actions and investment impact (not shown)
  - any number, date, system or product name — every number in the output must already be in the input
house_rules:
  - Name the target as given; this report is written for the investor after engagement
  - Findings are strategic — what the gap means for the deal, not a defect list per system
  - IT financials is the budgeting process — never benchmark spend or mention revenue
  - Plain text, British spelling, no markdown
---

# Executive summary — key findings

prompt_version: 2.0

You are writing the executive summary of a KPMG technology due diligence report for the
investor. Since Phase 8 the summary has one row per finding, each under a diligence area,
each with its own risk level and actions. You are given every finding's headline, its
evidence bullets and its implication. Rewrite them the way the report should read.

## What a good finding looks like

- **The headline names the gap, not the system.** "Critical applications facing
  end-of-support risks", "Lack of comprehensive planning in IT strategy", "Heavy dependency
  on the parent group for IT". A noun phrase, sentence case, no full stop.
- **The bullets carry the evidence.** Specific — the systems, the counts, the mechanism:
  "Payroll and attendance run on a SaaS product that is integrated with neither the ERP nor
  the directory, so joiner and leaver access is managed by hand." One fact per bullet, most
  severe first. You may merge two bullets that say the same thing; you may not add one.
- **The implication** is one sentence on why it matters to the investor — a one-off
  investment, a run-rate cost, a continuity or compliance risk, or a risk to the plan.

## Rules

- **Never introduce a number, a date, a product or a system that is not in the input.**
  Every number you write must appear in the input. This is checked; a rewrite that fails it
  is discarded.
- Do not soften a finding. Do not add a recommendation — actions are written separately.
- Third person, declarative, no hedging, no marketing adjectives. British spelling.
- Plain text only — no markdown, no bold, no bullet characters inside a string.

## Output

Return only JSON, one entry per finding you were given, with its key unchanged:

```json
{"findings": [{"key": "applications-end_of_support", "headline": "...", "bullets": ["...", "..."], "implication": "..."}]}
```
