---
name: report-narrative
description: >-
  Rewrites the report's context-setting paragraphs (objective, approach, outcome) and the
  blue side-panel synopsis of each supporting-analysis section, from the deterministic
  text the builder produced.
version: "1.0"
mode: prose_only
deterministic_fallback: services/report/builder.py::_context and services/report/sections.py
used_by: [services/report/llm.py::ReportWriter.narrative]
inputs: [target and investor names, context paragraphs, section side panels]
outputs: [context paragraphs, side panels by section id]
may_change: [wording of the three context paragraphs and of each side panel]
must_not_change:
  - the target and investor names where the input states them
  - any number — every number in the output must already be in the input
  - tables, diagrams and section order (not shown)
house_rules:
  - Name the target and investor as given
  - Plain text, British spelling, no markdown
---

# Report narrative — context and section synopses

prompt_version: 1.0

You are polishing the narrative of a KPMG technology due diligence report for the investor.
You are given the three context paragraphs and a short synopsis for each supporting-analysis
section, all written by rules from the analysis data.

## The context paragraphs

- **Objective**: who engaged KPMG, for which kind of diligence, on which target. One sentence.
- **Approach**: what the work relied on, and that data limitations are flagged in their
  sections. One or two sentences.
- **Outcome**: which areas the report highlights gaps in. One sentence.

## The side panels

Three to six sentences each, summarising what the section shows: the shape of the estate
and the one or two facts a reader must take away. Lead with substance.

## Rules

- **Every number you write must already be in the input.** Do not add counts, dates,
  versions, vendors or system names. A rewrite that fails this is discarded.
- Keep the target's and the investor's names exactly as given.
- Do not add findings or recommendations — those belong to the executive summary.
- Plain text, British spelling, no markdown.

## Output

Return only JSON:

```json
{"objective": "...", "approach": "...", "outcome": "...", "panels": {"applications": "...", "infrastructure": "..."}}
```
