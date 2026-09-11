# docs/reference/P2M_AUTOMATION_MODEL.md — Plan to Make automation maturity

**The evaluation reference for the Assess module's third process.** This document
defines what "level of automation" means for Plan to Make (P2M), how each step is
scored, and how the step scores roll up into one index. The scoring code reads this
model; `backend/app/reference/processes/plan_to_make.yaml` is written to elicit exactly
what the model needs.

It is the sibling of `P2P_AUTOMATION_MODEL.md` and `O2C_AUTOMATION_MODEL.md` and follows
them deliberately: the **maturity ladder (§2), the scoring arithmetic (§4) and the
banding (§5) are identical and process-agnostic**. Only the steps, their weights, the
per-level evidence and the shapes are specific to Plan to Make. A reader who knows
either of the other two models can read a P2M score without relearning anything.

---

## 1. Why Plan to Make is assessed differently from P2P and O2C

P2P and O2C are transaction cycles: a high volume of similar events, each one small, and
the automation question is how many of them still need a person. **Plan to Make is not a
transaction cycle. It is a decision cycle wrapped around a physical process**, and that
changes what the assessment is looking for.

Three consequences a deal team can price:

1. **The cost of being wrong is inventory, not effort.** A manual P2P leaks FTE cost. A
   manual planning process leaks *working capital and service level simultaneously* —
   too much of the wrong stock and not enough of the right, at the same time. The
   symptom is a balance sheet carrying inventory nobody can justify alongside stockouts
   nobody predicted, and both are visible in the numbers before anyone looks at the
   systems.
2. **Data quality is the whole game.** P2P and O2C can run tolerably on mediocre master
   data. Planning cannot: a bill of materials that is 4% wrong, a lead time that has not
   been reviewed since implementation, or a routing that does not match how the line
   actually runs produces a plan the shop floor ignores. **The most common finding in
   this process is not "there is no planning system" but "there is a planning system and
   nobody trusts its output."** That distinction is invisible from the licence register.
3. **Automation here is often deliberately partial.** Unlike invoice matching, where
   touchless is unambiguously better, a planner overriding the system can be the correct
   behaviour — they know the customer, the machine, the supplier. The assessment must
   distinguish **informed override** (a planner adding judgement the system cannot hold)
   from **systematic override** (the plan is wrong and everyone routes around it). The
   questionnaire asks for the override rate precisely because the number, not the
   practice, is what separates them.

A fourth point specific to diligence: **this process is where an ERP implementation's
real state becomes visible.** A target can run SAP and plan in Excel — and it is very
common. If the planning run is exported to a spreadsheet, worked, and keyed back in, the
ERP is a system of record rather than a system of planning, whatever the licence says.

**Scope note.** As with the other models, this grades *automation maturity*, not process
design quality, operational performance or the appropriateness of the planning strategy.
A target can run a fully automated planning process on a strategy that is wrong for its
business. Where an answer reveals a design problem rather than an automation gap, it
belongs in the findings, not in this score.

**A note on applicability.** This process assumes the target makes something. For a
distributor or a service business, steps 4–6 (production scheduling, execution, quality)
will not apply and should be left unanswered — the scoring excludes unassessed steps and
redistributes their weight, so a distributor scored on planning, procurement and
inventory alone still produces a defensible index. Do not force an answer to make the
questionnaire look complete.

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

**A note on 0 vs 1.** The distinction is whether a system holds the record at all.

**The P2M-specific caution — read this before scoring anything.** In this process the
ladder measures *whether the system does the work*, and a high rung is only credible if
the output is **used**. A target with a configured MRP run whose output is exported to
Excel, reworked and re-entered is **not** a 3, whatever the configuration screen shows:
the system is proposing and a human is deciding, which is a 2 at best. The questions
about override rates and schedule adherence exist to catch exactly this, and where the
answers contradict the tooling, **the behaviour wins over the licence**.

---

## 3. The eight steps of Plan to Make

The cycle is decomposed into eight L1 steps. Each is scored independently: automation is
rarely uniform, and the recurring mid-market shape here is a competent transactional back
end (works orders are recorded, stock is booked) sitting under a planning front end that
runs on spreadsheets and experience.

Weights reflect **the financial exposure the step controls and the volume of decisions it
carries**, not effort to assess. They sum to 100.

| # | Step | Weight | What it covers | Why it carries this weight |
|---|---|---|---|---|
| 1 | **Demand planning & forecasting** | 14 | Forecast generation, statistical method, consensus process, forecast accuracy measurement, new-product and promotional demand | Everything downstream is built on it; a forecast nobody measures is the single most common root cause of both excess stock and stockouts |
| 2 | **Sales & operations planning** | 10 | The monthly cycle that reconciles demand, supply, capacity and finance into one agreed plan, and who owns the decision | Where the plan becomes a commitment; a weak S&OP means the functions are each working to their own numbers |
| 3 | **Master data: BOMs, routings & parameters** | 13 | Bill of materials accuracy, routings, lead times, safety stock, reorder points, and how often they are reviewed | Planning output is only as good as this; the least glamorous step and the most common single cause of a distrusted plan |
| 4 | **Material requirements planning** | 15 | The MRP/DRP run itself: frequency, netting, exception messages, how planners act on them, and the override rate | The heaviest step — the highest volume of decisions in the cycle, and where a licensed capability most often sits unused |
| 5 | **Production scheduling & capacity** | 12 | Finite vs infinite scheduling, sequencing, changeover optimisation, capacity and constraint modelling, schedule stability | Determines whether the plan is executable; an infinite-capacity plan is a wish list and the floor will re-plan it informally |
| 6 | **Shop-floor execution & data capture** | 12 | Works order release, confirmations, labour and machine booking, real-time visibility, MES or paper travellers | Where the plan meets reality; without timely confirmation the system's view of WIP is fiction and nothing upstream can self-correct |
| 7 | **Quality management** | 10 | Inspection plans, in-process checks, non-conformance and CAPA handling, certificates, traceability and recall capability | Control-critical and regulatory-critical; traceability is a deal issue in food, pharma, aerospace and automotive regardless of automation level |
| 8 | **Inventory & warehouse management** | 14 | Stock accuracy, location control, cycle counting, WMS and scanning, goods movement, obsolescence management | Directly working-capital bearing, and stock-record accuracy gates the credibility of every number above it |

### 3.1 What each score looks like, step by step

The scoring rules below are what the questionnaire is written to elicit. Each step names
the evidence that distinguishes its levels.

**1. Demand planning & forecasting**
- *0* — no forecast; production is driven by whatever orders arrive and whoever shouts
- *1* — a forecast built in a spreadsheet by one person, largely from last year plus a percentage
- *2* — a documented forecasting process in a system or a structured model, with sales input collected manually
- *3* — statistical forecasting in a planning system across the main portfolio, with forecast accuracy measured and reported
- *4* — multiple statistical models selected by behaviour, segmented by product class, with accuracy tracked by segment and bias actively managed; promotional and NPI demand handled explicitly
- *5* — machine-learning demand sensing incorporating external signals (POS, weather, market data), continuously retrained and measured against a held-out baseline

**2. Sales & operations planning**
- *0* — no S&OP; sales, operations and finance work to different numbers and reconcile by argument
- *1* — a periodic meeting supported by spreadsheets assembled by hand for each cycle
- *2* — a defined monthly cycle with an agreed pack, but the numbers are compiled manually and the plan is not held in a system
- *3* — S&OP runs on the planning system, scenarios are modelled in-system, and the agreed plan is what drives MRP
- *4* — integrated business planning: the operational plan is reconciled to the financial plan in-system, with scenario and sensitivity analysis and tracked decisions
- *5* — continuous re-planning against live signals rather than a monthly cadence, with automated exception-driven escalation

**3. Master data: BOMs, routings & parameters**
- *0* — BOMs and routings exist informally, on drawings or in people's heads; no single source
- *1* — held in spreadsheets or a legacy system, updated when someone notices a problem
- *2* — held in the ERP, but accuracy is unmeasured and changes are made without a controlled process
- *3* — controlled change process with engineering change orders, BOM accuracy measured, planning parameters reviewed on a defined cycle
- *4* — parameters (lead time, safety stock, lot size) recalculated periodically from actual performance rather than set once; accuracy reported as a KPI
- *5* — continuously tuned parameters with automated anomaly detection on master data, feeding the planning run without human staging

**4. Material requirements planning**
- *0* — no MRP; materials are ordered by eye, by a person who knows the product
- *1* — a spreadsheet netting requirements against stock, re-built each cycle
- *2* — an MRP run exists but its output is exported to a spreadsheet, reworked and re-entered — the licensed capability is not what actually plans
- *3* — MRP runs on a defined cycle, exception messages are worked in-system, and the resulting orders release without re-keying
- *4* — frequent or daily netting with exception-based planning by exception class, planner override rate measured, and supplier schedules transmitted electronically
- *5* — continuous, constraint-aware replenishment with automated action on the routine majority of exception messages

**5. Production scheduling & capacity**
- *0* — the schedule is a whiteboard, a printed list, or the supervisor's judgement each morning
- *1* — a spreadsheet Gantt maintained by one scheduler
- *2* — scheduling in the ERP on infinite capacity, with the real constraint managed informally by the scheduler
- *3* — finite-capacity scheduling against modelled work centres, with sequencing rules and visible constraint loading
- *4* — optimisation against changeover, sequence and constraint rules, schedule adherence measured, and re-scheduling on disruption
- *5* — automated re-optimisation on live events (breakdown, material delay, rush order) with the shop floor seeing the revised sequence directly

**6. Shop-floor execution & data capture**
- *0* — paper travellers; completion is reported verbally or on a clipboard and keyed later, if at all
- *1* — works orders printed from the system, confirmed in a batch at the end of the shift or the week
- *2* — confirmations entered in-system by supervisors, with a lag, often estimated rather than measured
- *3* — timely operator-level confirmation at the workstation — scanning, terminals or an MES — giving a reliable WIP position
- *4* — machine and labour data captured automatically where equipment allows, with real-time OEE and live WIP visibility
- *5* — connected equipment reporting status, output and downtime automatically, feeding scheduling and maintenance without human transcription

**7. Quality management**
- *0* — quality checks happen but are recorded on paper and filed; no analysable record
- *1* — inspection results in spreadsheets; non-conformances tracked in a log or by email
- *2* — a quality module or system holds results, but inspection plans and dispositions are managed manually
- *3* — inspection plans configured against the routing, results captured in-system, non-conformance and CAPA workflow-managed, batch traceability available
- *4* — statistical process control on key characteristics, supplier quality integrated, cost of quality measured, traceability demonstrable end to end within hours
- *5* — in-line automated inspection feeding SPC continuously, with predictive quality signals acted on before defects occur

**8. Inventory & warehouse management**
- *0* — stock is counted when someone needs to know; no perpetual record
- *1* — a perpetual record in the ERP that everyone knows is unreliable; an annual count corrects it
- *2* — location-controlled stock with periodic cycle counting, movements keyed manually
- *3* — barcode or RFID scanning for goods movements with systematic cycle counting and measured stock-record accuracy
- *4* — a WMS directing put-away and picking, accuracy reported as a KPI and sustained above 98%, obsolescence reviewed on a defined cycle
- *5* — automated material handling integrated with the WMS, with continuous accuracy verification rather than counting campaigns

---

## 4. From answers to a step score

Identical to `P2P_AUTOMATION_MODEL.md` §4 — the arithmetic is process-agnostic and is
repeated here so this document stands alone.

1. Each scoring question carries an explicit `score` on each of its options — the
   ladder level that answer evidences.
2. A step's score is the **mean of its answered scoring questions**, rounded to one
   decimal.
3. **Unanswered questions are excluded from the denominator, never scored as zero.**
4. Coverage is reported alongside the score, so a reader can tell a confident 3.4 from
   a thin one.
5. A step with **no answered scoring questions is `not_assessed`**, and is excluded from
   the index with its weight redistributed across the steps that were assessed. This is
   what makes the model usable for a distributor or a service business — see the
   applicability note in §1.

Free-text questions do not score. In P2M the numbers most worth capturing are
**forecast accuracy (MAPE or bias), stock-record accuracy, schedule adherence, the
planner override rate, inventory value and turns, and OEE where measured**. A score
without at least stock accuracy and forecast accuracy beside it is hard to act on.

---

## 5. The index

The **P2M Automation Index** is the weighted mean of the assessed step scores,
normalised to 0–100, on the same formula and the same bands as P2P and O2C:

```
index = ( Σ (step_score × step_weight) / Σ (step_weight) ) × 20
```

where both sums run over assessed steps only.

| Index | Band | What it means for the deal |
|---|---|---|
| **0–20** | **Manual** | The plan lives in spreadsheets and experience. The business runs on a handful of people who know what to make; that is a key-person risk and a scalability ceiling, not just a systems gap. |
| **21–40** | **Emerging** | Systems record what happened but do not decide what to do next. Expect inventory and service-level problems that no amount of expediting fixes. |
| **41–60** | **Standardised** | A defined, system-mediated cycle with real gaps — most often master data and finite capacity. The usual mid-market shape, and improvable without replatforming. |
| **61–80** | **Integrated** | Connected planning through to execution with measured accuracy. Remaining gains are optimisation and data quality, not transformation. |
| **81–100** | **Optimised** | Touchless planning with instrumented execution. Rare outside large manufacturers. Verify the running rates and the override rate before accepting it. |

**The index is a summary, not the finding.** In P2M the index should always be read next
to two numbers: **stock-record accuracy** and **forecast accuracy**. A 60 with 99% stock
accuracy is a well-run process; a 60 with 85% stock accuracy means the systems are
configured and the data underneath them is not trustworthy, which is a far more expensive
problem than the index alone suggests.

---

## 6. Reading the shape

Three patterns recur often enough to be worth naming. The step ranges and the wording are
declared in `plan_to_make.yaml` under `shape`, so the note the product prints is content
rather than code.

- **Front-loaded** (steps 1–3 strong, 6–8 weak). Planning is sophisticated and the floor
  is not instrumented. The plan is built on a WIP and stock position that is reported
  late and approximately, so it degrades between publication and execution — planners
  compensate with buffer stock, and inventory is structurally higher than the plan
  implies. The fix is on the floor, not in the planning tool, which is usually the
  opposite of where a management team wants to invest.
- **Back-loaded** (steps 6–8 strong, 1–3 weak). Execution and stock control are solid —
  often a good WMS and disciplined shop-floor booking — while demand planning and master
  data run on spreadsheets. The business executes accurately against a plan that is
  guesswork, so it is efficient at making the wrong things. This shape usually shows up
  as high inventory *and* poor service simultaneously, which management attributes to
  demand volatility.
- **Uniformly low with a modern ERP.** The licence is not the process. As in P2P and O2C,
  the clearest signal that the last implementation stopped at go-live. In P2M it carries
  an extra implication: the planning modules are almost certainly licensed and unused, so
  a meaningful improvement may be available without new software — which changes the
  investment case from capex to change management, and those have very different risk
  profiles.

Watch also for the pattern the shape note cannot see: **strong systems and a high
override rate**. Every step scores well, the tooling is real, and the planners overrule it
on a third of lines. That is a data-quality or parameter problem wearing an automation
success as a disguise, and only the override and adherence questions will surface it.

---

## 7. Provenance and status of this model

`[EXT]` — this model is **not** taken from Roehl-Anderson (2013). `DD_master.md` was
searched for plan-to-make, production planning, manufacturing, MRP, bills of material,
scheduling and inventory content before this document was written: it contains **no
manufacturing process decomposition**. Its only adjacent material is incidental — "sales
forecast, revenue views, demand plan" appear at p. 519 in the list of data elements
requiring Day 1 protection, "fixed asset inventory" appears in the Finance evidence list
at p. 84, and §4 notes in passing that "a traditional manufacturer still has custom
applications worth understanding". None of that is a process model, and none is cited
below as though it were.

This document is therefore built for this platform, from the same two sources as the P2P
and O2C models: standard process taxonomy (the APQC-style L1/L2 decomposition in common
use, and the MRP II / SCOR vocabulary that manufacturing planning has used for decades)
and the maturity-ladder pattern that CMMI popularised.

It is **a calibration, not an authority**, and should be tuned against real engagements
exactly as `DD_master.md` §15.1 says of the scope engine's mix weights.

The weights in §3 are the most likely to need adjustment once this has been run against
real targets — in particular, a process-industry target (continuous, recipe-driven) and a
discrete engineer-to-order manufacturer stress this decomposition in opposite directions,
and the honest answer may eventually be two variants rather than one. Both the weights and
the shape thresholds live in `backend/app/reference/processes/plan_to_make.yaml`, editable
by a practitioner without a developer.

**Still not defined:** Hire to Retire, Record to Report. They appear in the product as
named processes with no questionnaire behind them. Each needs its own version of §3 — the
step decomposition, the weights and the per-level evidence — before it can be assessed.
The ladder in §2, the scoring arithmetic in §4 and the banding in §5 are process-agnostic
and carry over unchanged; the **shape** in §6 is not, and is declared per process in its
questionnaire YAML.
