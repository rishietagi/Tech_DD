# Phase 5 — Assess (business process automation)

**Status: BUILT** for Procure to Pay. The other four processes are named and listed with
no questionnaire behind them, by instruction.

## What this phase adds

Phases 1–4 planned the diligence: what we will cover, what is publicly known, what to ask
for, what has arrived. **Assess is where the diligence is actually performed** — the first
module whose content originates with the analyst in the data room rather than being
derived from the intake.

```
Intake → Scope → Research → IRL → Checklist → Assess
                                              (what we found when we looked)
```

The first question a tech DD asks of an operating business is **"what is the level of
automation in the business processes?"** — because licences reveal what was bought and
process automation reveals what is used. The gap between the two is where findings live.

## The five processes

`procure_to_pay` is defined. `order_to_cash`, `plan_to_make`, `hire_to_retire` and
`record_to_report` are registered with `defined: false` — **listed rather than hidden**, so
the shape of the module is visible, and returning **409 `process_not_defined`** rather than
404, which would wrongly imply the process does not exist.

Defining one is: a `<key>.yaml` questionnaire, a reference document for its step
decomposition, and flipping `defined` to true. The maturity ladder, the scoring arithmetic
and the banding are process-agnostic and carry over unchanged.

## The evaluation reference

`docs/reference/P2P_AUTOMATION_MODEL.md` — the domain authority, sitting alongside
`DD_master.md`. It defines nine L1 steps, weighted by transaction volume and financial
exposure (summing to 100), and a 0–5 maturity ladder whose levels are defined by
**observable evidence** rather than adjectives, so two analysts land on the same number.

| # | Step | Weight |
|---|---|---|
| 1 | Requisition & demand capture | 10 |
| 2 | Approval workflow | 12 |
| 3 | Sourcing, RFx & negotiation | 8 |
| 4 | Supplier onboarding & master data | 10 |
| 5 | Purchase order issuance | 13 |
| 6 | Goods & service receipt | 10 |
| 7 | Invoice capture & matching | 17 |
| 8 | Exception & dispute handling | 10 |
| 9 | Payment run & reconciliation | 10 |

Invoice matching and PO issuance weigh heaviest: they carry the most transactions and the
most leakage. The document is marked `[EXT]` — built for this platform, not from
Roehl-Anderson, and explicitly a calibration to be tuned against real engagements.

## The questionnaire and its nudges

`backend/app/reference/processes/procure_to_pay.yaml` — 26 questions and **31 nudges**
across the 9 steps, 20 of them scoring. A practitioner edits it without a developer.

A **nudge** is a conditional follow-up declared as data (`when: {equals | in | answered}`),
evaluated **client-side** so it appears the instant the analyst picks an option. Nudges
never score — they exist to make the evidence behind a score defensible, and one that
scored would double-count its parent.

Validated at startup: weights sum to 100, ids are unique, and **every nudge fires on an
option that actually exists** — a nudge naming a stale label would silently never appear.

## Data model

| Table | Holds | Versioned? |
|---|---|---|
| `process_answer` | one analyst answer to one question or nudge | no |
| `process_custom_question` | a question the analyst added | no |
| `process_assessment_score` | one scoring run | **yes** |

Answers are working notes — one current set, edited continuously. Scores are generated
deliverables, versioned like every other one. The questionnaire itself is **never stored**:
it is assembled on read from YAML plus the engagement's own custom questions, so a
corrected question reaches every engagement at once.

Migration `0005_add_process_assessment`.

## Scoring

Deterministic and reproducible from the answers. Two rules stop the score inventing
findings:

1. **An unanswered question is excluded from the denominator, never scored as zero.** A
   blank is an absence of evidence, not evidence of manual working.
2. **A step with no answered scoring questions is `not_assessed`** and drops out of the
   index, its weight redistributed across the steps that were assessed.

`index = (Σ score×weight / Σ weight) × 20`, banded Manual / Emerging / Standardised /
Integrated / Optimised. The **shape** is reported alongside the number — front-loaded,
back-loaded or even — because a front-loaded 52 and a uniform 52 imply remediation costs an
order of magnitude apart.

## The LLM's role — a recorded exception

Every other module lets the model write prose only. **Here it may also refine step
scores**, on Rishi's explicit instruction (2026-09-02), because the multiple-choice answers
alone cannot see that an analyst chose "configured 3-way matching" and then noted the
tolerances make it meaningless.

The trade is real: a refined index is no longer perfectly reproducible. The cost is
contained rather than accepted wholesale:

- the **deterministic score is always computed and always stored**, on the payload and on
  every step, so a reader can always put the rules number back;
- an adjustment may move a step by **at most ±1** and must carry a reason ≥20 characters;
- adjustments to unassessed steps, or beyond the bound, are **rejected individually** — one
  bad refinement does not discard a good summary;
- refining **more than three steps drops all of them**, since that is second-guessing the
  ladder rather than reading evidence.

## API

```
GET   /engagements/{id}/assess/processes                    the five processes + progress
GET   /engagements/{id}/assess/{key}                        questionnaire + answers   409 not defined
PATCH /engagements/{id}/assess/{key}/answers/{qid}          save one answer
POST  /engagements/{id}/assess/{key}/questions              add a custom question
POST  /engagements/{id}/assess/{key}/score                  score it
GET   /engagements/{id}/assess/{key}/score                  latest                    404 no_score
GET   /engagements/{id}/assess/{key}/score/versions         version list
```

`/processes` is declared **before** `/{process_key}` — FastAPI matches in declaration
order, the trap already recorded for `export.pdf`.

## Frontend

| Route | What it is |
|---|---|
| `/engagements/[id]/assess` | the five processes, four badged "Not yet defined" |
| `/engagements/[id]/assess/[processKey]` | questionnaire and score, as two tabs |

Nav gained **Assess** in the Engagement section, after Checklist — a prefix match, not
exact, so it stays lit inside a process sub-route.

No new colour tokens: the five bands reuse the existing priority/status ramp, low maturity
reading as the problem colour and high as the green already reserved for "arrived".

## Verification

- backend `pytest` 337 (37 new) · `ruff` · `mypy` clean (82 files)
- frontend `tsc` · `eslint` · `next build` clean, both routes present
- **generated a real score with the live model**: 25 answers on a seeded industrial
  distributor returned `generator: llm`, an index of 34.0/100 (Emerging), and an executive
  summary that used the analyst's actual evidence — 4,200 invoices, 9 AP FTEs, the missing
  callback verification, the unlogged payment file — and derived 466 invoices per FTE per
  month, the metric the questionnaire's nudge was written to elicit
- **drove it in a browser**: 5 processes with 4 honest "Not yet defined" badges, 9 step
  sections, 108 options, 20 answers restored after reload, a nudge revealing live on
  selection (14→15 follow-ups), the custom question tagged "Added", the score table with 9
  rows and 7 pointers, and the honest 409 empty state for an undefined process

## Deferred, deliberately

**A client-facing export.** The score view is internal-facing by decision — frank,
diagnostic, names weak spots plainly. A PPT/PDF in the KPMG house voice is the obvious next
step and the payload carries everything it needs, but it was not built rather than guessed
at. Same treatment as the shared-drive scanner.

**The other four processes.** Named only, by instruction.
