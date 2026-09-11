# docs/reference/O2C_AUTOMATION_MODEL.md — Order to Cash automation maturity

**The evaluation reference for the Assess module's second process.** This document
defines what "level of automation" means for Order to Cash (O2C), how each step is
scored, and how the step scores roll up into one index. The scoring code reads this
model; `backend/app/reference/processes/order_to_cash.yaml` is written to elicit
exactly what the model needs.

It is the sibling of `P2P_AUTOMATION_MODEL.md` and follows it deliberately: the
**maturity ladder (§2), the scoring arithmetic (§4) and the banding (§5) are identical
and process-agnostic**. Only the steps, their weights, the per-level evidence and the
shapes are specific to Order to Cash. A reader who knows the P2P model can read a
score for either process without relearning anything.

---

## 1. Why Order to Cash is assessed differently from Procure to Pay

Both are transaction cycles, and the automation question is the same one: **how much of
the work still needs a person?** But the commercial consequence of a manual O2C is not
the mirror image of a manual P2P, and a deal team reads the two for different things.

P2P leaks money slowly, through cost and control. **O2C leaks money visibly, through
working capital and the customer.** Three consequences a buyer can price:

1. **Cash, not just cost.** A manual O2C shows up in days sales outstanding before it
   shows up in headcount. Every day of avoidable DSO is cash trapped in the balance
   sheet at the moment of acquisition, and DSO improvement is one of the few value
   levers a buyer can pull without touching the product or the customer.
2. **Revenue integrity.** Manual pricing, manual order entry and manual billing produce
   under-billing, missed escalations and revenue that was earned and never invoiced.
   Unlike a duplicate payment, this leakage is usually never discovered, so it does not
   appear in any register the data room contains. It has to be inferred from the process.
3. **The customer sees it.** P2P failures are internal. O2C failures reach the customer
   as a wrong invoice, a chased payment that was already made, or a credit block on a
   good account. In a growth thesis this is a churn and scalability question, not only
   a finance one.

There is a fourth consideration specific to diligence: **O2C is where the quality of
earnings work and the technology work meet.** The QoE team is already testing revenue
recognition and the receivables ledger. The technology assessment explains *why* the
numbers behave as they do — whether an ageing debtor book is a credit problem or a
billing-accuracy problem is a process answer, not an accounting one. Where this
assessment touches revenue recognition, it grades the **automation of the mechanism**,
not the correctness of the policy.

**Scope note.** As with P2P, this model grades *automation maturity*, not process
design quality, commercial performance or the appropriateness of the revenue policy. A
target can bill entirely touchlessly and bill the wrong thing. Where an answer reveals
a design or a policy problem rather than an automation gap, it belongs in the findings,
not in this score.

---

## 2. The maturity ladder

Identical to `P2P_AUTOMATION_MODEL.md` §2, and repeated here so this document stands on
its own. Every step is scored **0–5** on one ladder, defined by *observable evidence*
rather than adjectives, so two analysts looking at the same data room land on the same
number.

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

**A note on 0 vs 1.** The distinction is whether a system holds the record at all. In
O2C this matters even more than in P2P: a step at 0 leaves no order, no billing event
and no receivable to trace, which is exactly the condition under which earned revenue
goes uninvoiced.

**One O2C-specific caution.** A step can look highly automated because it is *simple*
rather than because it is *well built*. A target with one product, one price and one
payment method will automate billing easily; a target with the same tooling and a
contracted, usage-based, multi-currency book will not. Record the complexity alongside
the level, because the buyer is usually underwriting the second case.

---

## 3. The eight steps of Order to Cash

The cycle is decomposed into eight L1 steps — one fewer than P2P, because O2C has no
equivalent of the sourcing event, and because credit assessment and customer master
data are one decision in practice rather than two. Each step is scored independently:
automation is rarely uniform across a cycle, and the recurring mid-market shape here is
a modern selling front end bolted onto a manual billing and collections back end.

Weights reflect **transaction volume and financial exposure**, not effort to assess.
Invoicing and cash application carry the most weight because they carry the most
transactions and the most working capital. They sum to 100.

| # | Step | Weight | What it covers | Why it carries this weight |
|---|---|---|---|---|
| 1 | **Customer setup & credit** | 10 | Customer master creation and stewardship, credit assessment and limits, credit blocks and their release, ongoing exposure monitoring | Master data quality gates the whole cycle and the credit decision is the one control that sits ahead of the risk, but volume is low relative to transactions |
| 2 | **Order capture** | 13 | Channels an order arrives through — portal, EDI, API, email, phone — order entry, validation, and acknowledgement to the customer | High volume; the entry point sets the data quality for everything downstream, and re-keyed orders are the origin of most billing errors |
| 3 | **Pricing, contracting & configuration** | 12 | Price derivation, discount approval, contracted and customer-specific rates, quote-to-order conversion, entitlement and configuration for what was actually sold | Directly determines what is billable; manual pricing is the largest single source of silent revenue leakage |
| 4 | **Fulfilment & delivery confirmation** | 10 | Order release, allocation, shipping or service delivery, proof of delivery, and the confirmation event that makes the order billable | Without a reliable billable-event signal, invoicing cannot be automated however good the billing tool is |
| 5 | **Invoicing & billing** | 18 | Invoice generation, timing, accuracy, delivery channel to the customer, e-invoicing and tax compliance, credit notes and rebilling | Highest volume and the largest concentration of manual effort and error in the cycle; billing accuracy governs both DSO and disputes |
| 6 | **Cash application & remittance** | 15 | Receipt of payment, matching cash to invoices, handling of remittance advice, unapplied cash, partial and short payments | Very high volume and directly working-capital-bearing; unapplied cash is a hidden receivable that ages while nobody chases it |
| 7 | **Collections & dunning** | 12 | Ageing visibility, chase strategy and prioritisation, reminder automation, escalation and hand-off, promise-to-pay tracking | Where DSO is actually won or lost, and the step most commonly run entirely on spreadsheets in a mid-market target |
| 8 | **Disputes, deductions & credit control reporting** | 10 | Logging and routing of disputes and deductions, root-cause tracking, write-off and credit-note authority, receivables and DSO reporting | Determines whether automation elsewhere converts into collected cash; unresolved disputes are the most common cause of an aged debtor book |

### 3.1 What each score looks like, step by step

The scoring rules below are what the questionnaire is written to elicit. Each step names
the evidence that distinguishes its levels.

**1. Customer setup & credit**
- *0* — customers are created on request with no credit assessment; no limits exist, or they exist only in someone's head
- *1* — a manual onboarding form and a credit check performed by judgement; limits recorded in a spreadsheet
- *2* — a defined in-system process with mandatory fields and recorded limits, but blocks are advisory and routinely overridden by convention
- *3* — credit limits configured and enforced by the system, blocks require a documented release, duplicate checking is systematic, exposure is visible
- *4* — automated credit scoring from bureau or trade data with scheduled limit review, portfolio exposure monitored and reported
- *5* — continuous credit risk monitoring feeding order release and collections prioritisation automatically

**2. Order capture**
- *0* — orders arrive by phone, email or fax and are worked from the message itself; no structured order record until later
- *1* — orders are re-keyed from email or a PDF into the system by an order-entry team
- *2* — orders are entered directly into a system by internal staff, with validation applied by the person rather than the system
- *3* — customer-facing portal or EDI covers a meaningful share of volume; orders validate automatically against master data and entitlement; acknowledgements are systematic
- *4* — the majority of order volume arrives electronically (EDI, API, portal, e-commerce) and posts straight through, with people handling exceptions rather than volume; touchless order rate is measured
- *5* — order capture is touchless by design, with exception patterns instrumented and fed back into validation rules

**3. Pricing, contracting & configuration**
- *0* — prices are agreed case by case and held outside any system; nobody can state a customer's contracted price without asking a person
- *1* — a price list in a spreadsheet, applied manually at order entry
- *2* — prices held in the system but overridden freely at order entry, with discount approval by convention
- *3* — contracted and customer-specific pricing configured in the system and applied automatically, with discount approval workflow enforced by delegation of authority
- *4* — pricing, entitlement and configuration derive automatically from the contract, with margin or discount guardrails enforced at order and exceptions reported
- *5* — pricing governed centrally with automated compliance monitoring and analytics on realised versus contracted price

**4. Fulfilment & delivery confirmation**
- *0* — delivery or service completion is not systematically recorded; billing is triggered by someone remembering
- *1* — proof of delivery or a completion note is captured on paper or by email and filed, keyed later
- *2* — fulfilment is confirmed in-system, often in a batch after the fact, with a lag before it becomes billable
- *3* — timely in-system confirmation — despatch, proof of delivery, milestone or timesheet — reliably triggering the billable event
- *4* — confirmation is automated from logistics, scanning, usage metering or project systems, with exceptions flagged at capture and unbilled fulfilment reported
- *5* — the billable event is generated by the fulfilment system itself with human confirmation by exception only

**5. Invoicing & billing**
- *0* — invoices are prepared manually, one at a time, from source documents and sent by post or as an attachment
- *1* — invoices are produced from a spreadsheet or a template and keyed into the ledger afterwards
- *2* — invoices generate in-system but require substantial manual preparation, checking or correction before release
- *3* — invoices generate automatically from the order or the confirmed fulfilment event, on a defined cycle, delivered electronically; billing errors are logged
- *4* — high straight-through billing across most volume including complex constructs (usage, milestone, recurring, rebate), e-invoicing and tax determination automated, first-time-right rate measured
- *5* — touchless billing as the norm, with billing-error root causes instrumented and continuously reduced

**6. Cash application & remittance**
- *0* — receipts are identified by a person reading the bank statement and applied by hand
- *1* — a spreadsheet reconciles receipts to invoices before they are keyed into the ledger
- *2* — cash is applied in-system, manually, with remittance advice chased by email
- *3* — bank statements are imported and auto-matched on a defined rule set, with exception-only manual application; unapplied cash is visible and worked
- *4* — high auto-match rate across most receipts including partial and consolidated payments, remittance ingested from multiple channels, auto-application rate measured and reported
- *5* — machine-assisted matching that learns from analyst corrections, with unapplied cash effectively transient

**7. Collections & dunning**
- *0* — chasing happens when someone notices; there is no ageing report anyone works from
- *1* — an aged debtors spreadsheet is worked down by one or two people
- *2* — ageing is visible in-system but chase activity, correspondence and notes are manual and personal
- *3* — a collections worklist prioritised by system rules, automated reminders on a defined dunning ladder, contact and promise-to-pay recorded against the account
- *4* — risk- or value-based prioritisation with segmented strategies, automated escalation, self-service payment and statement access, collections effectiveness measured
- *5* — predictive prioritisation on payment behaviour, with strategy tuned continuously against realised DSO

**8. Disputes, deductions & credit control reporting**
- *0* — disputes live in individual inboxes; no list of what is in query exists, and its value is unknown
- *1* — a spreadsheet or shared mailbox tracks queries and deductions
- *2* — disputes are recorded in-system but assignment, chasing and resolution are manual
- *3* — disputes logged with a reason code, routed automatically to an owner, aged and escalated; write-off and credit-note authority is enforced
- *4* — SLA-managed resolution with root-cause analysis feeding billing and fulfilment change, dispute value trending down, DSO and ageing reported as standard management information
- *5* — dispute causes intercepted before invoicing, with credit-control reporting driving process change rather than describing it

---

## 4. From answers to a step score

Identical to `P2P_AUTOMATION_MODEL.md` §4 — the arithmetic is process-agnostic and is
repeated here so this document stands alone.

1. Each scoring question carries an explicit `score` on each of its options — the
   ladder level that answer evidences.
2. A step's score is the **mean of its answered scoring questions**, rounded to one
   decimal.
3. **Unanswered questions are excluded from the denominator, never scored as zero.**
   A blank is an absence of evidence, not evidence of manual working.
4. Coverage is reported alongside the score, so a reader can tell a confident 3.4 from
   a thin one.
5. A step with **no answered scoring questions is `not_assessed`**, and is excluded from
   the index with its weight redistributed across the steps that were assessed.

Free-text questions do not score. They exist to capture the evidence, the volumes and
the caveats that make the number defensible, and they are what the executive summary
draws on. In O2C the numbers most worth capturing are **DSO, the aged debtor profile,
monthly invoice and order volume, the auto-cash-application rate, and the value
currently in dispute or unapplied** — a score without at least DSO and invoice volume
beside it is hard to act on.

---

## 5. The index

The **O2C Automation Index** is the weighted mean of the assessed step scores,
normalised to 0–100, on the same formula and the same bands as P2P:

```
index = ( Σ (step_score × step_weight) / Σ (step_weight) ) × 20
```

where both sums run over assessed steps only.

| Index | Band | What it means for the deal |
|---|---|---|
| **0–20** | **Manual** | Order, billing and collection all run on people and spreadsheets. Working capital is being lost to process rather than to customers. Expect revenue-leakage and control findings and a material systems investment in the plan. |
| **21–40** | **Emerging** | Systems exist but the cash cycle is still human. Islands of automation with manual bridges. DSO improvement is available but requires integration spend to get it. |
| **41–60** | **Standardised** | A defined, system-mediated cycle with real gaps. The usual mid-market shape. Working capital improvement is available without replatforming. |
| **61–80** | **Integrated** | Connected end to end with measured straight-through billing and cash-application rates. Remaining gains are optimisation, not transformation. |
| **81–100** | **Optimised** | Touchless by design. Rare. Verify the running rates — and the complexity of the book they run against — before accepting it. |

**The index is a summary, not the finding.** The step scores are what a deal team acts
on, and in O2C the index should always be read next to DSO. A 55 with a 45-day DSO and
a 55 with a 95-day DSO are describing different businesses: in the first the process is
adequate for the book, in the second the process is the reason the cash is late.

---

## 6. Reading the shape

Three patterns recur often enough to be worth naming, because each implies a different
remediation cost and a different commercial reading. The step ranges and the wording are
declared in `order_to_cash.yaml` under `shape`, so the note the product prints is content
rather than code.

- **Front-loaded** (steps 1–3 strong, 6–8 weak). The classic O2C signature, and the most
  commonly missed. Someone bought or built a modern selling front end — a portal, a CPQ
  tool, an e-commerce channel — and the cash end still runs on a spreadsheet. Orders
  arrive faster than they can be billed and collected, so **the working capital problem
  gets worse as revenue grows**. A buyer underwriting growth on this shape is
  underwriting a rising receivables balance and more collections headcount, usually
  without having priced either.
- **Back-loaded** (steps 6–8 strong, 1–3 weak). Finance modernised what it controls:
  cash application and collections work, but orders and pricing are manual upstream. The
  effect is that billing is accurate about the wrong thing — disputes and credit notes
  stay high because the error is created at order entry, and collections effort is being
  spent recovering from an upstream defect. Automating collections further will not fix
  it.
- **Uniformly low with a modern ERP or billing platform.** The licence is not the
  process. As in P2P, this is the clearest signal that the last implementation stopped at
  go-live, and it usually predicts the same outcome for the buyer's own integration plan.
  In O2C it carries an extra implication: if the platform can bill and nobody configured
  it to, the revenue-recognition mechanism is likely manual too, which is a quality-of-
  earnings question as much as a technology one.

A fourth pattern is worth watching for even though it is not named by the shape note: a
**strong middle with weak ends** — competent billing sitting between manual order capture
and manual collections. It reads as a moderate index but behaves like a manual process,
because the one automated step is fed and drained by hand.

---

## 7. Provenance and status of this model

`[EXT]` — this model is **not** taken from Roehl-Anderson (2013). `DD_master.md` was
searched for order-to-cash, revenue, billing, collections and credit content before this
document was written: it contains **no order-to-cash process decomposition**. Its only
adjacent material is incidental — customer terms, customer-specific pricing and revenue
recognition policy appear at p. 519 in the list of data elements requiring Day 1
protection, and "take orders, invoice customers, deliver product" appears at §3 as an
example of keeping the business running. Neither is a process model, and neither is
cited below as though it were.

This document is therefore built for this platform, from the same two sources as the P2P
model: standard process taxonomy (the APQC-style L1/L2 decomposition in common use) and
the maturity-ladder pattern that CMMI popularised and every major firm's process
assessments now use in some form.

It is **a calibration, not an authority**, and should be tuned against real engagements
exactly as `DD_master.md` §15.1 says of the scope engine's mix weights. The tests are
what make that tuning safe: change a weight, and the case that breaks tells you what you
broke.

The weights in §3 and the shape thresholds in §6 are the two things most likely to need
adjustment once this has been run against real targets. Both live in
`backend/app/reference/processes/order_to_cash.yaml`, editable by a practitioner without
a developer. The bands in §5 are shared with P2P and should not be moved for one process
alone.

**Still not defined:** Hire to Retire, Record to Report. Plan to Make was defined on
2026-09-11 - see `P2M_AUTOMATION_MODEL.md`. They appear in the
product as named processes with no questionnaire behind them. Each needs its own version
of §3 — the step decomposition, the weights and the per-level evidence — before it can be
assessed. The ladder in §2, the scoring arithmetic in §4 and the banding in §5 are
process-agnostic and carry over unchanged.
