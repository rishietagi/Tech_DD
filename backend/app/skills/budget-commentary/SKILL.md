---
name: budget-commentary
description: >-
  Writes the IT budget section's synopsis from the budget-versus-actual table and the
  budgeting-process findings. Reviews the budgeting process; never models or benchmarks
  cost.
version: "1.0"
mode: prose_only
deterministic_fallback: services/report/sections.py::budget
used_by: [services/report/llm.py::ReportWriter.budget]
inputs: [the rules synopsis, budget and actual by year, run/change mix, process findings]
outputs: [the section synopsis]
may_change: [wording of the synopsis]
must_not_change:
  - any figure — every number in the output must already be in the input
  - the boundary — no share of revenue, no benchmark, no view of what spend should be
house_rules:
  - IT financials is the budgeting process, never a cost model (2026-09-14)
  - Plain text, British spelling, no markdown
---

# IT budget — section synopsis

prompt_version: 1.0

You are writing the synopsis of the IT budget section of a technology due diligence
report. You are given budget and actual technology spend by year as the target reported
it, the run versus change mix, and the findings on how the budget is built, approved and
controlled.

Write three to five sentences: whether spend lands where it was budgeted, which years or
lines moved and by how much, and what the budgeting process does and does not control.

## Rules

- **Review the process, not the cost.** Never express spend as a share of revenue, never
  compare it with a benchmark or with other companies, and never say what the target
  should spend. Any of these is discarded.
- **Every number you write must already be in the input.**
- Plain text, British spelling, no markdown.

## Output

Return only JSON:

```json
{"panels": {"budget": "..."}}
```
