# docs/reference/R2R_AUTOMATION_MODEL.md — Record to Report automation maturity

**The evaluation reference for the Assess module's fifth process.** This document
defines what "level of automation" means for Record to Report (R2R), how each step is
scored, and how the step scores roll up into one index. The scoring code reads this
model; `backend/app/reference/processes/record_to_report.yaml` is written to elicit
exactly what the model needs.

It shares the **maturity ladder (§2), the scoring arithmetic (§4) and the banding (§5)**
with the other four models, because those three are process-agnostic. §1, §3 and §6 are
its own, and §6 in particular departs from the pattern the other four follow — see the
judgement recorded there.

---

## 1. What kind of process this is, and why that changes the assessment

P2P and O2C are transaction cycles. Plan to Make is a decision cycle. Hire to Retire is
an identity lifecycle. **Record to Report is a periodic close**, and it is the first
process in this module where the word "volume" barely applies.

A close does not process a stream of similar events. It is **a bounded, repeating
project with a deadline**: the same work, performed by the same people, in the same
sequence, five or twelve or thirteen times a year, against a date that does not move. A
target might run its entire month-end with 40 people and produce a few hundred journals
— trivial by transaction count, and the process can still consume a fortnight of the
finance function's month and be the reason the business cannot tell you what it earned
until the 19th.

So the natural currency of this assessment is not transactions per FTE. It is:

- **days to close** — working days from period end to a reported, reviewed group result,
  and the single most comparable number in the process;
- **manual journal count** — how many entries are keyed rather than generated, which is
  both an effort measure and a misstatement-risk measure, since a manual journal is the
  entry an auditor and a fraudster are both most interested in;
- **reconciliation backlog** — how many balance-sheet accounts are unreconciled, aged, or
  reconciled only at year end, which is where an unpleasant surprise sits if there is one.

**Weights follow what consumes the close and where misstatement risk sits**, not volume.
Reconciliations carry the heaviest weight in this model despite producing almost no
"transactions": they are the largest single consumer of close effort in most mid-market
finance functions and the place an error survives undetected for longest. Journals and
close task management come next, because they are simultaneously the effort and the risk.
Tax carries a light weight not because it is unimportant but because it is usually
outsourced or annual, and so is mostly outside the mechanism this model grades.

Three commercial readings a deal team can price:

1. **Reporting latency is a governance cost, and it is the one the buyer feels first.**
   A twenty-day close means the new owner's board sees January's numbers in late
   February, and every management action in the first hundred days is taken on stale
   information. It also delays the buyer's own group reporting, which for a corporate
   acquirer is a hard constraint rather than an inconvenience — a listed parent has a
   filing calendar the target must now fit inside. **This is the most common reason a
   buyer funds a finance systems programme post-close**, and it is usually not in the
   deal model.
2. **Manual close effort is real cost, but it is concentrated and seasonal.** It shows up
   as a finance function sized for the close rather than for the business, and as
   sustained overtime in the first ten working days of every month. The FTE saving from
   automating it is genuine but smaller than vendors claim, because the people are not
   redeployed — they are already doing other work for the other three weeks.
3. **Control and misstatement risk.** Spreadsheet-mediated consolidation, unreviewed
   manual journals and unreconciled balance-sheet accounts are the classic mechanism of
   both error and fraud. For a buyer this is a diligence risk before it is an operating
   one: if the mechanism is weak, the historical numbers being underwritten were produced
   by that weak mechanism.

**The boundary with the quality-of-earnings work, stated plainly.** The QoE team is
already on this process from the other side, and the two must not be confused. **This
assessment grades the automation of the mechanism, not the correctness of the
accounting.** A target can produce accurate, well-judged financial statements through a
mechanism made entirely of spreadsheets — plenty do, at the cost of a fortnight and a
key person. It can equally run a consolidation system beautifully and make the wrong
judgement about an accrual.

The line is the same one `O2C_AUTOMATION_MODEL.md` §1 draws about revenue recognition,
and it runs in both directions:

- **Out of scope here:** whether a provision is adequate, whether revenue was recognised
  in the right period, whether the adjustments in the QoE bridge are justified, whether
  the accounting policy is appropriate. Those are the QoE and audit teams' questions, and
  answering them from a process questionnaire would be both wrong and out of our
  competence.
- **In scope here, and useful to them:** how the number was produced, how many hands it
  passed through, how much of it was assembled outside a system, whether an audit trail
  survives, and how long it took. **Where the QoE team finds a number they cannot tie
  out, this assessment frequently explains why** — an unreconciled intercompany position
  or a consolidation worked in a spreadsheet is a process fact, not an accounting one.

The most useful thing this module can do for a deal team is therefore not the index. It
is to say, in evidence, **how much of the reported result is assembled by hand** — because
that is the measure of how much reliance the historical numbers can bear, and it is a
question nobody else on the deal is asking in these terms.

**Scope note.** As with the other models, this grades *automation maturity*, not the
correctness of the accounting, the adequacy of the control environment as an auditor
would assess it, or the competence of the finance team. Where an answer reveals a
control or accounting problem rather than an automation gap, it belongs in the findings —
and should be handed to the QoE team — not in this score.

**A note on applicability.** Steps 4 and 5 (intercompany and consolidation) do not exist
in a single-entity target, and step 6 (external reporting and disclosure) is minimal in
a small private company with no listed debt and no statutory audit. Leave them unanswered
rather than scoring them as manual: the scoring redistributes their weight, and marking a
process manual because it does not exist manufactures a finding. **A single-entity target
assessed on the six steps that apply produces a defensible index.** Note also that a
carve-out changes this materially — an entity that has never consolidated or reported
standalone will need to, and the absence of the step is then a Day 1 cost rather than a
non-applicability.

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
a running rate, the step is not a 5. Most well-run private companies top out at 3–4. In
R2R specifically, a **continuous or "virtual" close is the level-5 claim** and it is
almost never true as stated — ask which sub-ledgers are actually closed daily and what
the last hard close took.

**A note on 0 vs 1.** The distinction is whether a system holds the record at all. In
R2R this is the difference between a control that can be evidenced and one that can only
be asserted: a reconciliation performed in a workbook on someone's drive and never
reviewed is a 0, not a 1, however carefully it was done, because nothing durable records
that it happened.

**One R2R-specific caution, and it is the one that most often produces a wrong score.**
Finance functions are good at closing on time through effort. **A fast close is not
evidence of an automated close.** A target that reports on working day five with a team
that worked three consecutive weekends has bought the deadline with people, and the
number that looks best in this assessment is the one concealing the largest key-person
and burnout risk. Always read days-to-close next to the manual journal count and the
close-effort evidence — a five-day close with 400 manual journals is a worse finding than
a ten-day close with 40, because the first cannot survive either growth or the departure
of the financial controller.

---

## 3. The eight steps of Record to Report

The close is decomposed into eight L1 steps, in the order the close actually runs. Each
is scored independently. Unlike the transaction cycles, these steps are **sequentially
dependent within each period**: the consolidation cannot start until the sub-ledgers are
closed, so a delay early in the sequence propagates mechanically to everything after it.
That dependency is what §6 is about.

**Weights reflect close effort and misstatement risk**, not transaction volume. They sum
to 100.

| # | Step | Weight | What it covers | Why it carries this weight |
|---|---|---|---|---|
| 1 | **Sub-ledger close & cut-off** | 12 | Closing AP, AR, inventory, fixed assets and payroll to the general ledger, accruals and prepayments, cut-off discipline, the interfaces that post sub-ledger activity | The gate on everything after it; a sub-ledger that closes late or posts in summary makes every later step slower and less traceable, and cut-off is where most period-end error originates |
| 2 | **Reconciliations** | 16 | Balance-sheet account reconciliation, bank reconciliation, sub-ledger-to-GL agreement, preparation and independent review, ageing and open-item clearance | The heaviest step: the largest single consumer of close effort in a mid-market finance function, and the control most likely to be performed in a workbook nobody reviews — an unreconciled balance is where an error survives longest |
| 3 | **Journal entries & close task management** | 15 | Manual and recurring journals, supporting documentation, preparer/reviewer segregation, the close calendar and task tracking, status visibility across the team | Effort and risk at once: the manual journal count is the best single proxy for how much of the result is assembled by hand, and an uncontrolled journal is the classic misstatement mechanism |
| 4 | **Intercompany** | 11 | Intercompany transactions and balances, matching and agreement between entities, settlement, elimination, transfer pricing postings, disputes between entities | Consumes disproportionate close time in any group and is the most common cause of a consolidation that will not balance; near-zero in a single-entity target, which is why it is left unanswered there |
| 5 | **Consolidation & group close** | 14 | Aggregation of entity results, currency translation, eliminations, minority interests, group adjustments and topside entries, the group trial balance | Where a spreadsheet does the most damage: a consolidation worked outside a system has no audit trail, breaks when the structure changes, and is usually held by one person |
| 6 | **External reporting & disclosure** | 10 | Statutory accounts, group and lender reporting, disclosure preparation and tie-out, audit support and the audit file, filing | Consequential and deadline-bound, but performed a few times a year and often with adviser support, so it consumes less of the recurring close than its visibility suggests |
| 7 | **Tax accounting & compliance** | 8 | Current and deferred tax computation, tax provision and its posting, indirect tax returns, filings and their supporting data | Important but largely annual, and usually outsourced or adviser-led in a mid-market target, so much of it sits outside the mechanism this model grades; weight it higher for a target with material in-house indirect tax volume |
| 8 | **Management reporting & analytics** | 14 | The management pack, budget and forecast comparison, entity and segment reporting, the definition and maintenance of KPIs, self-service access to the numbers | Where the close becomes useful; a target whose pack is rebuilt by hand each month has an analyst cost, a latency problem and a single point of failure, and it is the step a buyer notices immediately after close |

### 3.1 What each score looks like, step by step

The scoring rules below are what the questionnaire is written to elicit. Each step names
the evidence that distinguishes its levels.

**1. Sub-ledger close & cut-off**
- *0* — there are no real sub-ledgers; balances are assembled from spreadsheets and summary journals at period end
- *1* — sub-ledgers exist but are closed by manual posting of summary entries into the general ledger, keyed by hand
- *2* — sub-ledgers post to the GL through defined interfaces, run and checked manually, with cut-off enforced by instruction rather than by the system
- *3* — automated, detailed posting from each sub-ledger with periods locked in sequence by the system and interface exceptions visible and worked
- *4* — sub-ledger close is scheduled, monitored and largely exception-based, with accruals systematically calculated and cut-off controls configured
- *5* — continuous sub-ledger close with balances available on demand and period-end a reporting event rather than a process

**2. Reconciliations**
- *0* — balance-sheet accounts are not reconciled, or only at year end under audit pressure
- *1* — reconciliations prepared in individual spreadsheets, stored on a shared drive, with review evidenced by an initial if at all
- *2* — a standard template and a checklist of accounts, prepared manually, with review tracked outside the system
- *3* — a reconciliation tool or module with prepared/reviewed workflow, ageing visible, and a defined policy on which accounts are reconciled at what frequency
- *4* — automated matching for high-volume accounts including bank, with risk-rated reconciliation frequency, exception-only review and measured ageing
- *5* — continuous reconciliation with auto-certification of low-risk accounts and analytics directing effort at the accounts that move

**3. Journal entries & close task management**
- *0* — journals are posted from emails and notes with no consistent support, and there is no close calendar — people know what to do
- *1* — a spreadsheet close checklist and journals posted directly by preparers, with supporting files kept separately
- *2* — a defined journal form and approval convention with support attached, and a close calendar maintained manually and circulated
- *3* — journals raised in-system with mandatory support, enforced preparer/reviewer segregation, recurring journals templated, and a tracked close task list with owners and dependencies
- *4* — the manual journal count is measured and being reduced, materiality-based approval routing, close status visible in real time, with cycle time reported per task
- *5* — journal creation largely automated from source events, with analytics identifying anomalous entries before posting

**4. Intercompany**
- *0* — intercompany balances are agreed by email between finance teams and adjusted at consolidation
- *1* — a spreadsheet matrix reconciled manually each period, with differences resolved by negotiation
- *2* — intercompany transactions flagged in the ledger and matched manually against a counterparty schedule
- *3* — systematic intercompany matching with a defined difference threshold, a dispute process with owners, and routine settlement
- *4* — automated matching and elimination with netting or settlement runs, ageing reported and differences trending down
- *5* — real-time intercompany posting with automatic counterparty entries, so differences cannot arise in the ordinary course

**5. Consolidation & group close**
- *0* — the group result is built in a spreadsheet model maintained by one person
- *1* — entity trial balances collected by email and consolidated in a workbook with manual eliminations and translation
- *2* — a consolidation template collected from entities and loaded into a tool, with adjustments and eliminations still worked outside it
- *3* — a consolidation system fed from entity ledgers with translation, eliminations and the group structure configured, and topside entries controlled and auditable
- *4* — largely automated consolidation with validation rules on submission, a maintained group structure, measured close cycle and a full audit trail from group figure to entity detail
- *5* — continuous consolidation with the group position available on demand and scenario or structure changes modelled without rebuilding

**6. External reporting & disclosure**
- *0* — statutory accounts are prepared entirely by an adviser from a trial balance handed over at year end
- *1* — statements drafted in a document with figures typed in from the consolidation and checked by eye
- *2* — a standard reporting template populated manually, with a tie-out performed by hand
- *3* — disclosures generated from the consolidation with linked figures, a controlled review cycle, and an audit file assembled to a defined structure
- *4* — a disclosure management tool with automatic tie-out across statements and notes, version control, and audit requests served from a maintained evidence set
- *5* — reporting fully linked to the ledger with tagging and filing automated, and the reporting calendar managed as a tracked process

**7. Tax accounting & compliance**
- *0* — tax is dealt with once a year by an adviser with no in-house computation or provision process
- *1* — provisions and returns prepared in spreadsheets from extracts assembled by hand
- *2* — a defined tax data extract and a documented computation, still spreadsheet-based, posted manually
- *3* — tax-sensitised data available from the ledger with the provision computed on a standard model and posted on a controlled cycle; indirect tax returns produced from system reports
- *4* — tax engine or configured determination for indirect tax, automated provision calculation and posting, and filings produced from system data with reconciliation to the ledger
- *5* — real-time tax determination and continuous compliance monitoring across jurisdictions

**8. Management reporting & analytics**
- *0* — there is no regular management pack; numbers are produced when someone asks
- *1* — a pack rebuilt by hand each month in spreadsheets from ledger exports, by one or two people
- *2* — standard ledger reports assembled into a pack manually, with commentary added and some figures re-keyed
- *3* — a reporting layer or BI tool fed from the ledger with a defined KPI set, actual-to-budget comparison built in, and the pack produced from it
- *4* — self-service reporting on governed definitions with drill-down to transaction detail, automated distribution, and pack production a review rather than a build
- *5* — analytics integrated with planning and forecasting, with variance analysis and driver-based insight generated rather than assembled

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
draws on. In R2R the three numbers worth having above all others are the ones §1 names —
**working days to close, the manual journal count per period, and the number of
unreconciled or aged balance-sheet accounts** — together with the finance headcount
involved in the close and the number of ledgers and entities. A score reported without
days-to-close beside it is missing the one figure every reader will ask for first.

---

## 5. The index

The **R2R Automation Index** is the weighted mean of the assessed step scores,
normalised to 0–100, on the same formula and the same bands as the other processes:

```
index = ( Σ (step_score × step_weight) / Σ (step_weight) ) × 20
```

where both sums run over assessed steps only.

| Index | Band | What it means for the deal |
|---|---|---|
| **0–20** | **Manual** | The result is assembled by hand. The close is long, the audit trail is thin, and the numbers being underwritten were produced by a mechanism that cannot be re-performed. Expect control findings, a key-person dependency, and a finance systems investment in the plan. |
| **21–40** | **Emerging** | A ledger exists and the close runs, but reconciliation, consolidation and the management pack are spreadsheet work. Close latency is a governance problem for the buyer from month one. |
| **41–60** | **Standardised** | A defined, system-mediated close with real gaps — usually reconciliations and the management pack. The usual mid-market shape; days-to-close can be improved without replacing the ERP. |
| **61–80** | **Integrated** | Connected from sub-ledger to group report with the close managed as a tracked process and cycle time measured. Remaining gains are cycle time and self-service. |
| **81–100** | **Optimised** | Close as a continuous process rather than an event. Rare. Verify which sub-ledgers actually close daily before accepting it. |

**The index is a summary, not the finding.** In R2R the index should always be read next
to **days to close** and the **manual journal count**, for the reason §2 gives: a fast
close bought with overtime scores well here and is a risk, not a strength. A 48 closing
in eight days with a stable team and a 48 closing in eight days on three weekends of
overtime are describing different businesses, and only the evidence fields can tell them
apart.

---

## 6. Reading the shape

**A judgement recorded here rather than a pattern asserted.** The other four models name
a front-loaded and a back-loaded shape and attach a confident commercial reading to each.
That template does not transfer cleanly to a close, and this section says so rather than
inventing a narrative to fill it.

The reason is the one §3 gives: **the steps of a close are sequentially dependent within
a single period**, whereas the ends of P2P, O2C or H2R are weeks or years apart and
genuinely independent. In a transaction cycle a strong front end and a weak back end
means two different investment decisions taken at two different times, which is exactly
what makes the gap informative. In a close, a weak step 1 does not sit beside a strong
step 8 — it *causes* step 8 to be late, every period, mechanically. A gap between the
ends is therefore a weaker signal here, and a genuinely even profile is both the most
common result and an unremarkable one.

The shape is still worth reporting, because the two lopsided cases do each carry a real
reading. They are simply narrower claims than in the other processes, and the wording in
`record_to_report.yaml` under `shape` reflects that — including the even note, which says
plainly that an even close is the ordinary case and directs the reader to days-to-close
instead of implying a finding. The front end is steps 1–3 (sub-ledger close,
reconciliations, journals) and the back end is steps 6–8 (external reporting, tax,
management reporting).

- **Front-loaded** (steps 1–3 strong, 6–8 weak). The ledger mechanics are in order —
  reconciliations are controlled, journals are governed, sub-ledgers close cleanly — and
  what is built on top is manual. The group report, the statutory disclosures and the
  management pack are assembled in spreadsheets from a perfectly good ledger. The reading
  is favourable and specific: **the expensive, risky part is already right**, and the
  remediation is a reporting layer rather than a finance transformation. Because the
  underlying data is trustworthy, this is one of the cheaper findings in this module to
  fix, and the buyer's latency problem is solvable without touching the ERP.
- **Back-loaded** (steps 6–8 strong, 1–3 weak). A polished management pack and a
  presentable set of statutory accounts sitting on reconciliations that are not done and
  journals that are not controlled. **This is the more serious of the two**, and the one
  that deserves a paragraph in the report: the outputs look credible precisely because
  effort has been spent on presentation, while the mechanism underneath cannot be
  re-performed. It is also the shape most likely to surprise a QoE team late, because
  the pack ties and the ledger does not — hand this one to them explicitly.
- **Uniformly low with a modern ERP.** The licence is not the process. As in the other
  four, the clearest signal that the last implementation stopped at go-live. In R2R the
  specific implication is that the close and consolidation modules are almost certainly
  licensed and unconfigured, so a meaningful reduction in days-to-close may be available
  without new software — a change-management investment rather than a capital one.

Watch also for what the shape cannot see, and it is the same caution as §2: **a fast
close that is fast because of people.** Every step can score moderately, the cycle time
can look competitive, and the whole thing can rest on two individuals and a workbook.
Only the manual journal count, the close-effort evidence and the key-person question will
surface it.

---

## 7. Provenance and status of this model

`[EXT]` — this model is **not** taken from Roehl-Anderson (2013). `DD_master.md` was
searched for financial close, month-end, consolidation, general ledger, reconciliation,
journal, sub-ledger, statutory and management reporting content before this document was
written. It contains **no record-to-report process decomposition**, and the search is
actively misleading unless read carefully:

- **"Financial close" in the source means deal close, not accounting close** [p. 5, 253,
  1332 of the reference index] — "Day 1 (deal closed) — financial close; execution
  begins". This is the completion of the transaction. It is not the period-end process
  and must not be cited as though it were; the phrase collision is the single most likely
  way this model could be given false provenance.
- **"Consolidated financial reporting"** appears at p. 115 in a Day 1 readiness list, and
  **"consolidation reporting"** at p. 303 as the scope floor under a preservation
  integration model. Both concern what a *buyer* must be able to produce after
  acquisition, not how a target closes its books.
- **"Finance separation" as a Day 1 area with critical IT dependencies** [p. 253–254].
  Relevant context for a carve-out — and cited in §1's applicability note for exactly
  that — but not a process model.

None of these is a decomposition of the close and none is cited above as though it were.
The QoE boundary in §1 and the caution about a fast close in §2 are the platform's own.

This document is therefore built for this platform, from the same two sources as the
other four models: standard process taxonomy (the APQC-style L1/L2 decomposition in
common use) and the maturity-ladder pattern that CMMI popularised and every major firm's
process assessments now use in some form.

It is **a calibration, not an authority**, and should be tuned against real engagements
exactly as `DD_master.md` §15.1 says of the scope engine's mix weights. The tests are
what make that tuning safe: change a weight, and the case that breaks tells you what you
broke.

Two weights are deliberately contestable and are argued in §3: **tax at 8 is low**,
justified by its being annual and usually adviser-led, and it should be raised for a
target with material in-house indirect tax operations; and **management reporting at 14
is high** for a step that is not part of the statutory close at all, justified by its
being what the buyer experiences from month one. Both live in
`backend/app/reference/processes/record_to_report.yaml`, editable by a practitioner
without a developer. The bands in §5 are shared with the other processes and should not
be moved for one process alone.

**This is the fifth and last of the processes named in the Assess module.** With Hire to
Retire (`H2R_AUTOMATION_MODEL.md`) and this document, all five are defined: Procure to
Pay, Order to Cash, Plan to Make, Hire to Retire and Record to Report. There is no
remaining named-but-undefined process.
