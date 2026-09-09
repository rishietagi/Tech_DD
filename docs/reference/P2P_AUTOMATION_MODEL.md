# docs/reference/P2P_AUTOMATION_MODEL.md — Procure to Pay automation maturity

**The evaluation reference for the Assess module.** This document defines what
"level of automation" means for the Procure to Pay (P2P) process, how each step is
scored, and how the step scores roll up into one index. The scoring code reads this
model; the questionnaire is written to elicit exactly what the model needs.

It sits alongside `DD_master.md` as a domain authority. `DD_master.md` governs *what a
technology due diligence covers*; this document governs *how one business process is
graded once the team is inside the data room*.

---

## 1. Why process automation is the first question

In an operating business, the technology question a buyer actually needs answered is
not "what software do they own" but **"how much of the work still needs a person?"**
Licences reveal what was bought. Process automation reveals what is used.

The gap between the two is where diligence findings live. A target can run SAP and
still key invoices by hand into it. A target can run no ERP at all and have a
straight-through payment cycle. The licence register cannot tell these apart; the
process assessment can.

This matters commercially in three ways a deal team can price:

1. **Cost.** Manual steps carry FTE cost that scales with volume. A buyer underwriting
   2x revenue growth on a manual P2P cycle is underwriting a proportional headcount
   increase in accounts payable.
2. **Control.** Manual approval and matching steps are where duplicate payments,
   maverick spend and fraud enter. These are audit findings waiting to happen.
3. **Integration.** A carve-out or bolt-on has to migrate whatever the process actually
   is. An undocumented, spreadsheet-mediated process is materially harder to move than
   a configured, system-enforced one.

**Scope note.** This model grades *automation maturity*, not process design quality,
commercial performance, or ERP fitness. A process can be highly automated and badly
designed. Where an answer reveals a design problem rather than an automation gap, it
belongs in the findings, not in this score.

---

## 2. The maturity ladder

Every step is scored **0–5** on one ladder. The levels are defined by *observable
evidence*, not by adjectives, so two analysts looking at the same data room land on
the same number.

| Score | Level | What is true at this level |
|---|---|---|
| **0** | **Manual** | No system involvement. Paper, email, phone or a local spreadsheet is the system of record for this step. Nothing is captured in an application until later in the cycle, if at all. |
| **1** | **Recorded** | A system holds the outcome, but a person performs the work and keys the result in after the fact. The system is a ledger, not a participant. Spreadsheets sit between the people and the system. |
| **2** | **Standardised** | The step is performed inside a system with a defined path. Rules exist but are enforced by convention rather than configuration; a determined person can route around them. Data is re-keyed between systems. |
| **3** | **Integrated** | The system enforces the rules and the step is connected to the ones either side of it. Data flows without re-keying. Exceptions are visible. A person still reviews or releases most transactions. |
| **4** | **Automated** | The routine majority of transactions complete without human touch. People handle exceptions, not volume. Rules are configured, measured and reported on. Straight-through rates are known and tracked. |
| **5** | **Optimised** | Touchless by design, with the exception path itself instrumented and improving. Machine-assisted handling of what used to be exceptions. The process is measured against benchmarks and the measurement drives change. |

**A note on 4 vs 5.** Level 5 is genuinely rare in mid-market targets and should not be
awarded for ambition, roadmap or vendor marketing. If the evidence is a plan rather than
a running rate, the step is not a 5. Most well-run private companies top out at 3–4.

**A note on 0 vs 1.** The distinction is whether a system holds the record at all. This
matters more than it looks: a step at 0 leaves no data to migrate, no audit trail to
rely on, and nothing to measure a baseline against.

---

## 3. The nine steps of Procure to Pay

The cycle is decomposed into nine L1 steps. Each is scored independently, because
automation is rarely uniform across a cycle — the classic mid-market shape is a modern
front end (requisition, approval) bolted onto a manual back end (matching, payment).

Weights reflect **transaction volume and financial exposure**, not effort to assess.
Invoice matching and PO issuance carry the most weight because they carry the most
transactions and the most leakage. They sum to 100.

| # | Step | Weight | What it covers | Why it carries this weight |
|---|---|---|---|---|
| 1 | **Requisition & demand capture** | 10 | How a need becomes a formal request: catalogues, punch-out, free-text forms, email | The entry point sets the data quality for everything downstream, but volume is moderate |
| 2 | **Approval workflow** | 12 | Delegation of authority, routing, escalation, audit trail of who approved what | Control-critical; the first place duplicate and maverick spend is stopped |
| 3 | **Sourcing, RFx & negotiation** | 8 | Competitive events, bid comparison, award, contract creation | Lower transaction volume; high value per event but episodic |
| 4 | **Supplier onboarding & master data** | 10 | Vendor creation, verification, bank detail changes, deduplication, ongoing stewardship | Master data quality gates the whole cycle; bank-detail change is the classic fraud vector |
| 5 | **Purchase order issuance** | 13 | Requisition-to-PO conversion, transmission, acknowledgement, change orders, % PO-backed spend | High volume; non-PO spend is the single biggest driver of downstream manual effort |
| 6 | **Goods & service receipt** | 10 | GRN capture, service confirmation, mobile/scanned receipt, three-way match readiness | Without reliable receipt the match cannot be automated, whatever the invoice tooling |
| 7 | **Invoice capture & matching** | 17 | Receipt channel, OCR/e-invoicing, 2-way and 3-way match, tolerance rules, auto-match rate | Highest volume and highest manual-effort concentration in the entire cycle |
| 8 | **Exception & dispute handling** | 10 | Routing of mismatches, query management, ageing and escalation, root-cause tracking | Determines whether automation elsewhere actually converts into saved effort |
| 9 | **Payment run & reconciliation** | 10 | Run scheduling, approval, bank integration, remittance, auto-reconciliation | Control-critical and the last place errors can be caught before cash leaves |

### 3.1 What each score looks like, step by step

The scoring rules below are what the questionnaire is written to elicit. Each step names
the evidence that distinguishes its levels.

**1. Requisition & demand capture**
- *0* — requests arrive by email, phone or paper; no structured form
- *1* — a form or spreadsheet template is filled, then keyed into a system by someone else
- *2* — requisitions are raised directly in a system, mostly free-text
- *3* — catalogue-based requisitioning for common categories; free-text is the exception and is routed for review
- *4* — punch-out or hosted catalogues cover the majority of spend; guided buying steers users to preferred suppliers and contracted prices
- *5* — demand is anticipated from consumption or planning data; reordering is triggered automatically within agreed parameters

**2. Approval workflow**
- *0* — verbal or email approval, no retained record
- *1* — email approvals attached to a record after the fact
- *2* — approvals in-system but the delegation of authority is a document people consult, not a configuration
- *3* — DOA is configured and enforced; routing is automatic and the audit trail is complete
- *4* — risk-based routing (value, category, supplier, budget availability); auto-approval within defined low-risk thresholds; SLA-tracked
- *5* — continuous control monitoring on approval behaviour; anomalies detected and escalated automatically

**3. Sourcing, RFx & negotiation**
- *0* — sourcing is ad hoc, by phone and email, with no retained comparison
- *1* — bids are collected by email and compared in a spreadsheet
- *2* — a sourcing tool is used for some events; templates exist
- *3* — e-sourcing is standard above a threshold, with structured bid comparison and an auditable award decision, feeding a contract repository
- *4* — sourcing is linked to pipeline and contract expiry; award terms flow into catalogue and contract records without re-keying
- *5* — analytics-driven sourcing with automated event triggers and continuous supplier market monitoring

**4. Supplier onboarding & master data**
- *0* — suppliers are created on request with no verification; duplicates are common and unmeasured
- *1* — a manual onboarding form and checklist; verification is a person's judgement
- *2* — a defined onboarding process in-system with mandatory fields
- *3* — a supplier portal for self-registration, systematic duplicate checking, and controlled bank-detail change with independent verification
- *4* — automated verification against external sources (registry, tax, sanctions), scheduled data quality monitoring, measured duplicate rates
- *5* — continuous supplier risk monitoring feeding the sourcing and payment decisions

**5. Purchase order issuance**
- *0* — no POs, or POs raised after the invoice arrives to satisfy finance
- *1* — POs typed manually from approved requisitions and sent by email
- *2* — POs generated in-system, transmitted manually, no acknowledgement tracked
- *3* — automatic requisition-to-PO conversion; electronic transmission; acknowledgement and change orders tracked; PO-backed spend measured and majority
- *4* — high PO coverage of addressable spend with automated release strategies and contract-price enforcement at PO creation
- *5* — self-service and system-triggered ordering against agreements, with minimal human involvement in routine issuance

**6. Goods & service receipt**
- *0* — receipt is not recorded, or is confirmed verbally to accounts payable
- *1* — paper GRN or delivery note filed, keyed later
- *2* — receipt entered in-system by the receiving team, often in a batch after the fact
- *3* — timely in-system receipting including service confirmation, sufficient to support three-way matching
- *4* — mobile, scanned or barcode receipt at the point of delivery; service entry sheets workflow-approved; exceptions flagged at capture
- *5* — receipt confirmed automatically from sensor, logistics or milestone data with human confirmation by exception

**7. Invoice capture & matching**
- *0* — paper or PDF invoices keyed manually in full; matching is a person comparing documents
- *1* — invoices scanned and stored, but data entry and matching remain manual
- *2* — OCR extraction with substantial manual correction; system-assisted matching that a person completes
- *3* — reliable automated capture across most volume with configured 2-way and 3-way matching and defined tolerances; auto-match rate known
- *4* — e-invoicing or EDI for the majority of volume; high straight-through match rate; tolerance and duplicate rules configured and monitored
- *5* — touchless processing as the norm, with machine-learning-assisted coding and continuous tuning of tolerance and exception rules

**8. Exception & dispute handling**
- *0* — exceptions live in individual inboxes; no list of what is outstanding exists
- *1* — a spreadsheet or shared mailbox tracks queries
- *2* — exceptions are visible in-system but assignment and chasing are manual
- *3* — automatic routing by exception type with ownership, ageing and escalation; supplier queries handled through a defined channel
- *4* — SLA-managed with root-cause analysis feeding process change; supplier self-service on status; exception volumes trending down
- *5* — predictive prevention — exceptions anticipated and intercepted before the invoice blocks

**9. Payment run & reconciliation**
- *0* — payments prepared manually, individually, from documents
- *1* — a payment file assembled in a spreadsheet and uploaded to the bank
- *2* — scheduled payment runs from the system, manually approved and manually uploaded
- *3* — integrated bank connectivity with segregated approval, automated remittance advice, and regular automated bank reconciliation
- *4* — payment-term and discount optimisation, positive pay or equivalent fraud controls, largely automated reconciliation with exception-only review
- *5* — dynamic discounting and continuous cash optimisation, with reconciliation effectively exception-free

---

## 4. From answers to a step score

The questionnaire asks, for each step, a small number of questions whose answers map
onto the ladder. Scoring is **deterministic and stated**:

1. Each scoring question carries an explicit `score` on each of its options — the
   ladder level that answer evidences.
2. A step's score is the **weighted mean of its answered scoring questions**, rounded to
   one decimal.
3. **Unanswered questions are excluded from the denominator, never scored as zero.**
   A blank is an absence of evidence, not evidence of manual working. Scoring a blank
   as 0 would manufacture a finding out of an analyst not having got there yet.
4. Coverage is reported alongside the score — "scored on 24 of 31 questions" — so a
   reader can tell a confident 3.4 from a thin one.
5. A step with **no answered scoring questions is `not_assessed`**, and is excluded from
   the index with its weight redistributed across the steps that were assessed.

Free-text questions do not score. They exist to capture the evidence, the volumes and
the caveats that make the number defensible, and they are what the exec summary draws on.

---

## 5. The index

The **P2P Automation Index** is the weighted mean of the assessed step scores,
normalised to 0–100:

```
index = ( Σ (step_score × step_weight) / Σ (step_weight) ) × 20
```

where both sums run over assessed steps only. The ×20 converts the 0–5 ladder to 0–100.

| Index | Band | What it means for the deal |
|---|---|---|
| **0–20** | **Manual** | The process runs on people and spreadsheets. Headcount scales with volume. Expect control findings and a material systems investment in the plan. |
| **21–40** | **Emerging** | Systems exist but the work is still human. Islands of automation with manual bridges between them. Integration cost is the story. |
| **41–60** | **Standardised** | A defined, system-mediated process with real gaps. The usual mid-market shape. Improvement is available without replatforming. |
| **61–80** | **Integrated** | Connected end to end with measured straight-through rates. Remaining gains are optimisation, not transformation. |
| **81–100** | **Optimised** | Touchless by design. Rare. Verify the running rates before accepting it. |

**The index is a summary, not the finding.** The step scores are what a deal team acts
on: an index of 52 built from a strong front end and a manual back end tells a
completely different story from a uniform 52, and the remediation cost differs by an
order of magnitude. Report the shape, not just the number.

---

## 6. Reading the shape

Three patterns recur often enough to be worth naming, because each implies a different
remediation cost:

- **Front-loaded** (steps 1–3 strong, 6–9 weak). Someone bought a procurement tool and
  never finished the programme. The invoice and payment end still carries the FTE cost,
  and the buyer's synergy case usually assumes otherwise. Common, and commonly missed.
- **Back-loaded** (7–9 strong, 1–5 weak). Finance modernised what it controlled. Spend
  is not being influenced before it is committed, so savings cases built on category
  management will underdeliver.
- **Uniformly low with a modern ERP.** The licence is not the process. This is the
  clearest signal that the last implementation stopped at go-live, and it usually
  predicts the same outcome for the buyer's own integration plan.

---

## 7. Provenance and status of this model

`[EXT]` — this model is **not** taken from Roehl-Anderson (2013), which predates modern
P2P automation and does not decompose business processes this way. It is built for this
platform from standard process taxonomy (the APQC-style L1/L2 decomposition in common
use) and from the maturity-ladder pattern that CMMI popularised and every major firm's
process assessments now use in some form.

It is therefore **a calibration, not an authority**, and should be tuned against real
engagements exactly as `DD_master.md` §15.1 says of the scope engine's mix weights. The
golden-case tests are what make that tuning safe: change a weight, and the case that
breaks tells you what you broke.

The weights in §3 and the bands in §5 are the two things most likely to need adjustment
once this has been run against real targets. Both live in
`backend/app/reference/processes/procure_to_pay.yaml`, editable by a practitioner
without a developer.

**Order to Cash is now defined** — see `O2C_AUTOMATION_MODEL.md`, which follows this
document's structure and shares its ladder and banding unchanged.

**Not yet defined:** Plan to Make, Hire to Retire, Record to Report. They appear in the
product as named processes with no questionnaire behind them. Each needs its own version
of §3 — the step decomposition, the weights and the per-level evidence — before it can be
assessed. The ladder in §2, the scoring arithmetic in §4 and the banding in §5 are
process-agnostic and carry over unchanged; the **shape** in §6 is not, and is declared per
process in its questionnaire YAML.
