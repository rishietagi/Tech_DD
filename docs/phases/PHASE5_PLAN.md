# Phase 5 — Assess (business process automation)

**Status: BUILT** for Procure to Pay, Order to Cash and Plan to Make. Hire to Retire and
Record to Report are named and listed with no questionnaire behind them.

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

`procure_to_pay`, `order_to_cash` and `plan_to_make` are defined. `hire_to_retire` and
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

## Order to Cash — the second process (2026-09-09)

`docs/reference/O2C_AUTOMATION_MODEL.md` defines **eight** L1 steps, not nine. O2C has no
equivalent of P2P's sourcing event, and credit assessment and customer master data are one
decision in practice rather than two.

| # | Step | Weight |
|---|---|---|
| 1 | Customer setup & credit | 10 |
| 2 | Order capture | 13 |
| 3 | Pricing, contracting & configuration | 12 |
| 4 | Fulfilment & delivery confirmation | 10 |
| 5 | Invoicing & billing | 18 |
| 6 | Cash application & remittance | 15 |
| 7 | Collections & dunning | 12 |
| 8 | Disputes, deductions & credit control reporting | 10 |

Invoicing and cash application weigh heaviest: highest transaction volume, and unlike P2P
they are directly **working-capital-bearing**. That is the substantive difference between
the two processes — a manual P2P leaks cost and control slowly, a manual O2C leaks cash
visibly and the customer sees it. `[EXT]`, like the P2P model: **`DD_master.md` has no
order-to-cash process material**, which was checked before the document was written and is
stated in its §7 rather than papered over with page cites it does not have.

`order_to_cash.yaml` carries 28 questions (21 scoring, 7 free-text) and 30 nudges.

### What defining it changed in code

Almost nothing, which was the claim being tested — but not *quite* nothing. `_shape_note`
hardcoded `sn <= 3` / `sn >= 7` and P2P's own vocabulary, so an O2C score would have
carried a note about accounts payable. The prose moved into an optional **`shape` block**
on the questionnaire: front and back step ranges, and the three notes. A questionnaire
without one falls back to the previous behaviour, so P2P is untouched and declares none.

The arithmetic of a shape is process-agnostic; its commercial reading is not. See the
decision entry in `docs/PROJECT_LOG.md`.

**A second fix followed from reading the output**: the model was overwriting the authored
shape note with its own paraphrase, discarding both the judgement and the measured means.
Where a `shape` block exists it now wins, and the model writes prose only.

### Verification

- backend `pytest` 388 (25 new) · `ruff` · `mypy` clean · frontend `tsc` · `eslint` clean
- **generated a real score with the live model** on Project Kiln: 40 answers on a
  front-loaded distributor returned an index of **36.4/100 (Emerging)**, 8 of 8 steps
  assessed, one refinement of −0.3 within the ±1 bound, and a summary built from the
  analyst's own evidence — 78-day DSO against 45-day terms, 8 days of internal DSO before
  the customer is asked to pay, EUR 640k unapplied cash, EUR 900k in dispute, 6,800
  invoices against 5 billing FTEs
- **drove it in a browser**: 5 processes with 3 honest "Not yet defined" badges, 8 step
  sections, 113 options, 42 remarks and evidence boxes, a nudge revealing live on
  selection, the score view with its index, band, authored shape note and 8-row step
  table, and the honest 409 empty state for `plan_to_make`

## Plan to Make — the third process (2026-09-11)

`docs/reference/P2M_AUTOMATION_MODEL.md` defines eight L1 steps.

| # | Step | Weight |
|---|---|---|
| 1 | Demand planning & forecasting | 14 |
| 2 | Sales & operations planning | 10 |
| 3 | Master data: BOMs, routings & parameters | 13 |
| 4 | Material requirements planning | 15 |
| 5 | Production scheduling & capacity | 12 |
| 6 | Shop-floor execution & data capture | 12 |
| 7 | Quality management | 10 |
| 8 | Inventory & warehouse management | 14 |

**Three things make this process different**, and the model document says so rather than
forcing the P2P template onto it:

1. **It is a decision cycle, not a transaction cycle.** P2P and O2C leak FTE cost; a manual
   planning process leaks working capital and service level at the same time.
2. **A high rung is only credible if the output is used.** A configured MRP run whose
   output is exported to Excel, reworked and re-entered scores **2, not 3**. Pinned by
   `test_the_mrp_spreadsheet_rework_option_scores_as_a_two` — scoring it as integrated
   would let a licence stand in for a working process, which is what this module exists to
   catch.
3. **It need not apply in full.** A distributor has no scheduling, shop floor or quality
   process. Those steps are left unanswered and their weight redistributes;
   `test_a_non_manufacturing_target_can_be_scored_on_the_steps_that_apply` covers it.

`[EXT]` — `DD_master.md` has no manufacturing process decomposition, which was checked
before the document was written and is stated in its §7.

**Verification:** pytest 440 (33 new) · ruff · mypy · tsc · eslint clean. A live score on
Kiln returned **37.6 (Emerging)** with planning at 0.7-1.0 against a floor at 2.5-3.7, the
authored shape note intact with its measured means, and an executive summary that used the
analyst's own evidence and correctly attributed a growing obsolescence provision to the
demand-planning weakness rather than to the inventory step.

## Adding the next process — the exact shape to follow

Procure to Pay, Order to Cash and Plan to Make are the worked examples. Defining Hire to
Retire or Record to Report is the **same six artefacts**, in this order:

1. **`docs/reference/<PROCESS>_AUTOMATION_MODEL.md`** — write this FIRST; scoring reads
   from it. It defines the L1 steps, their weights (summing to 100), and what each rung of
   the 0-5 ladder looks like *for that process*, in observable evidence rather than
   adjectives. Mark it `[EXT]` — built for this platform, a calibration to be tuned.
2. **`backend/app/reference/processes/<key>.yaml`** — the questionnaire: steps, weights,
   `single_select` questions with a `score` on every option, `text` questions that capture
   evidence, `nudges` (`when: {equals | in | answered}`), and a **`shape` block** giving
   the front and back step ranges and what a front-loaded, back-loaded or even cycle means
   commercially *for that process*. Without it the score falls back to P2P's nine-step
   split and P2P's wording.
3. **`_registry.yaml`** — flip `defined: false` to `true`.
4. **Tests** in `tests/test_assess.py` — the library ones are parameterised in spirit
   already; add the process to them.
5. **Nothing else.** The ladder (§2), the scoring arithmetic (§4), the banding (§5), the
   API, the scoring prompt, the frontend and the remarks field are **all process-agnostic**
   and need no change. If you find yourself editing `scoring.py` or a route, stop and
   check why — the design intends the new process to be pure content. Defining O2C found
   the one place where that was not yet true and fixed it by moving the prose into YAML;
   there should be no second such place.
6. **Read the generated score**, do not just run the tests. Every real bug in this module
   was found by generating output and reading it.

The startup validation enforces: weights sum to 100, question and nudge ids unique, and
**every nudge fires on an option that actually exists** — a nudge naming a stale label
would silently never appear.

## Deferred, deliberately

**A client-facing export.** The score view is internal-facing by decision — frank,
diagnostic, names weak spots plainly. A PPT/PDF in the KPMG house voice is the obvious next
step and the payload carries everything it needs, but it was not built rather than guessed
at. Same treatment as the shared-drive scanner.

**The other two processes.** Hire to Retire and Record to Report are named only.
