# docs/reference/H2R_AUTOMATION_MODEL.md — Hire to Retire automation maturity

**The evaluation reference for the Assess module's fourth process.** This document
defines what "level of automation" means for Hire to Retire (H2R), how each step is
scored, and how the step scores roll up into one index. The scoring code reads this
model; `backend/app/reference/processes/hire_to_retire.yaml` is written to elicit
exactly what the model needs.

It shares the **maturity ladder (§2), the scoring arithmetic (§4) and the banding (§5)**
with `P2P_AUTOMATION_MODEL.md`, `O2C_AUTOMATION_MODEL.md` and
`P2M_AUTOMATION_MODEL.md`, because those three are process-agnostic. It does **not**
follow the P2P template in §1, §3 or §6, and the reason is the whole of §1: Hire to
Retire is a different kind of process from anything defined so far, and a deal team
reads its score for a different purpose.

---

## 1. What kind of process this is, and why that changes the assessment

P2P and O2C are **transaction cycles**: a high volume of similar events, each one small,
and the automation question is how many of them still need a person. Plan to Make is a
**decision cycle**: a smaller number of consequential judgements, and the question is
whether the system's output is trusted enough to be used.

Hire to Retire is neither. It is an **identity and obligation lifecycle**. Volume is low
and lumpy — a mid-market target with 600 staff might process 90 joiners, 40 leavers and
twelve payroll runs in a year, which is a rounding error beside its invoice count.
Counting transactions would rank this process as trivial. It is not trivial, and the
reason is that **each event changes four things at once**: an HR record, a set of system
entitlements, a payment obligation, and a legal position. The automation question here
is not "how many people does this take?" but **"when a person's status changes, how many
systems find out, how fast, and can anyone prove it?"**

That produces three commercial readings a deal team can price, and only the first of
them is the familiar one:

1. **Cost, and it is the smallest of the three.** A manual H2R carries HR administration
   FTE, and that cost is real but modest — HR shared-service headcount does not scale
   with revenue the way accounts payable does. A buyer should not expect a large synergy
   here, and a vendor case promising one is usually double-counting payroll outsourcing
   savings that have already been taken.

2. **Security. This is the only process in this module where the automation gap is also
   a cyber finding.** Joiner-mover-leaver is where access provisioning and revocation
   physically happen — every other control in the security workstream assumes JML works.
   A manual offboarding process does not merely cost administrative effort: **it leaves
   credentials live**. A leaver whose account is disabled eleven days after their last
   day had eleven days of access to the target's systems, and in a business with 15%
   staff turnover that is a standing population of live orphaned accounts. This is a
   finding the diligence has to carry into the security workstream, not a footnote in an
   HR observation.

   The practical consequence for the questionnaire is specific and deliberate: **it must
   elicit revocation *timeliness*, measured in days and evidenced, not merely whether an
   offboarding checklist exists.** A checklist is the answer every management team gives
   and it evidences nothing — the score has to turn on whether anyone has counted the
   lag, and on whether an orphaned-account review has ever been run against the leaver
   list. A target with an immaculate documented process and no measurement is a 2, not a
   4. This is the H2R equivalent of the rule P2M draws about an MRP output reworked in
   Excel: the artefact is not the process.

3. **Regulatory and structural exposure, which is where the deal cost usually sits.**
   This process carries **personal data end to end**, and special categories among it,
   since absence records contain health data and payroll contains bank details. The
   regulatory dimension is not a footnote:

   - **Data protection.** Employee data is the largest single population of personal
     data most non-consumer targets hold. Retention beyond the lawful period, leaver
     records never purged, and CVs sitting in a recruiter's mailbox are the common
     findings, and they are findings against the *automation* because a manual process
     has no retention mechanism at all.
   - **Works councils and employee representation.** In much of continental Europe a
     works council has consultation rights over the introduction of systems that monitor
     employees — time and attendance, and performance tooling especially. A target that
     has not been through that process has a delay, not just a cost, sitting in front of
     any HR systems programme the buyer intends. Ask whether the consultation happened;
     it is invisible in the licence register.
   - **Multi-jurisdiction payroll is a carve-out problem as much as an automation one.**
     A target operating in several countries almost always has several payroll systems,
     usually a different local provider per country, frequently inherited from
     acquisitions and never consolidated. Each is a separate transition service, a
     separate data migration and a separate local compliance obligation on Day 1. **The
     payroll count is therefore one of the most useful single numbers in this
     assessment**, and a one-country target and a seven-country target with identical
     automation levels do not carry the same integration cost. The questionnaire asks
     for the count explicitly.

**Where this process meets the rest of the diligence.** The security workstream tests
whether access controls exist; this tests whether the events that should trigger them
actually do. The carve-out workstream sizes TSA exposure; this names how many payroll
and HR systems have to be in it. Where an answer here is a security or separation
finding it belongs in those workstreams as well as in this score — this is the one
process whose output is routinely read by someone other than the operational diligence
lead.

**Scope note.** As with the other models, this grades *automation maturity*, not HR
process design, employment-law compliance, culture or the quality of the people. A
target can run a fully automated onboarding process against a badly designed
organisation. Where an answer reveals a compliance breach rather than an automation
gap — an unlawful retention period, an unconsulted works council — it belongs in the
findings and usually in the legal workstream, not in this score. The score records that
the *mechanism* is manual; the breach is a separate observation.

**A note on applicability.** Every target has this process — there is no equivalent of
P2M's distributor exemption, because every business hires and loses people. But its
*shape* varies enormously with headcount: a 40-person target genuinely does not need a
learning management system, and scoring step 7 harshly for its absence would manufacture
a finding. Where a step is not applicable at the target's scale rather than absent
through neglect, leave it unanswered and record why in the evidence field; the scoring
redistributes the weight. The distinction the analyst has to make is between **too small
to need it** and **too disorganised to have it**.

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
H2R this carries a specific consequence: a step at 0 leaves **no authoritative employee
record**, which means there is no source of truth from which access rights, payroll or a
headcount number can be derived. Several of the findings in this process are downstream
of that one fact.

**One H2R-specific caution, and it is the most important line in this document.** In
every other process, the existence of a documented procedure is weak evidence of a
level. Here it is *no* evidence at all. Onboarding and offboarding are the two steps
where every management team has a checklist and the checklist is followed unevenly,
because the work is done by line managers and IT under time pressure rather than by a
process team with a queue. **Score these two steps on measurement, not on
documentation** — on whether anyone counts the lag between a leaver's last day and the
disabling of their accounts, and whether that count has ever been reconciled against the
actual account population. Where documentation and measurement disagree, the measurement
wins; where there is no measurement, the step cannot be above a 2 however good the
document is.

---

## 3. The nine steps of Hire to Retire

The lifecycle is decomposed into nine L1 steps. Each is scored independently, because
automation is markedly uneven across this process — the recurring mid-market shape is a
modern recruiting front end and a modern payroll engine with an entirely manual middle
holding them together.

**Weights reflect what breaks when the step is manual**, not transaction volume — that
is the substantive departure from the P2P and O2C weighting rule, and it follows from
§1. Offboarding processes a trivial number of events and carries one of the heaviest
weights in the model, because the exposure per missed event is unbounded: a leaver whose
access persists is a live credential, and one is enough. Payroll carries the heaviest
weight because it must be correct every period in every jurisdiction, and because the
number of payroll systems is the single most useful predictor of separation cost. They
sum to 100.

| # | Step | Weight | What it covers | Why it carries this weight |
|---|---|---|---|---|
| 1 | **Workforce planning, recruiting & offer** | 9 | Headcount approval and requisition, vacancy advertising, applicant tracking, interview scheduling and record, offer generation and acceptance, pre-employment checks | Usually the best-automated step and the least consequential if it is not; a manual recruiting process costs time-to-hire, which is an operational irritation rather than a diligence finding |
| 2 | **Onboarding & provisioning** | 14 | Conversion of an accepted offer into an employee record, contract issue, equipment and account provisioning, role-based access assignment, first-day readiness | One half of the joiner-mover-leaver control; where over-provisioning begins, and every excess entitlement granted here persists for the employee's whole tenure unless something removes it |
| 3 | **Core employee data & organisational records** | 13 | The employee master record, organisational and reporting structure, position and role data, contract changes, the mover event, and which system is authoritative | The source of truth the other eight steps read from; where it is fragmented nothing downstream can be automated, and the headcount number in the model cannot be reconciled |
| 4 | **Payroll** | 16 | Payroll calculation and run, input collection, statutory deductions and filings, payments and payslips, multi-country and multi-provider arrangements, payroll reconciliation to the ledger | The heaviest step: it must be right every period under statutory deadlines in every jurisdiction, errors are visible to every employee, and the number of payroll systems drives both integration cost and TSA exposure |
| 5 | **Time, attendance & absence** | 11 | Time capture, shift and rota management, overtime, holiday and sickness recording, absence approval, and the feed into payroll | Where payroll input is created; a manual feed here makes an otherwise automated payroll a re-keying exercise, and in a shift-based or unionised workforce this is the largest administrative load in the whole process |
| 6 | **Performance, compensation review & development** | 8 | Objective setting and review cycle, performance records, annual compensation and bonus review, promotion and progression, succession and talent records | Consequential for the buyer's people plan and for key-person risk, but a manual annual cycle is an inefficiency rather than an exposure, and the data is often reconstructible |
| 7 | **Learning & compliance training** | 7 | Course delivery and records, mandatory and regulatory training, certification and licence currency, evidence for audit | Low in general, but this step is **exposure-bearing in regulated and safety-critical sectors**, where an unevidenced mandatory-training record is a regulatory finding; read the weight as a floor and treat the step as materially heavier where the target is regulated |
| 8 | **Offboarding & access revocation** | 14 | Resignation and termination processing, notice and final pay, equipment return, **account and entitlement revocation and its timeliness**, orphaned-account reconciliation, records retention after exit | The other half of the JML control and the one that generates a security finding rather than a cost finding; near-zero volume, unbounded exposure per missed event, and the step most likely to be scored too generously on the strength of a document |
| 9 | **HR compliance, reporting & data privacy** | 8 | Statutory and management HR reporting, headcount and attrition analytics, data retention and purging, subject access and privacy operations, works council and employee representation records | The step that proves the others: without reporting, no claim made about any preceding step can be substantiated, and retention is where the largest personal-data population in the business is either governed or is not |

### 3.1 What each score looks like, step by step

The scoring rules below are what the questionnaire is written to elicit. Each step names
the evidence that distinguishes its levels.

**1. Workforce planning, recruiting & offer**
- *0* — vacancies are agreed verbally; CVs live in individual mailboxes; no record of who applied or why they were rejected
- *1* — a spreadsheet tracker of candidates, with offers written and sent by hand
- *2* — an applicant tracking system used for the pipeline, but headcount approval sits outside it and offers are produced manually
- *3* — requisition and approval in-system against an approved headcount plan, structured pipeline and interview records, offers generated from templates with an auditable acceptance
- *4* — integrated to onboarding so an accepted offer creates the employee record without re-keying; pre-employment checks tracked to completion; time-to-hire measured and reported
- *5* — workforce planning driven from the organisational and demand plan, with pipeline analytics and automated scheduling, measured against benchmarks

**2. Onboarding & provisioning**
- *0* — a manager emails IT asking for accounts, usually naming a colleague to copy the access from
- *1* — a checklist document worked through by hand across several teams, tracked in a spreadsheet or a mailbox
- *2* — an onboarding workflow exists in a system and raises the requests, but each account is created manually in each application and access is still assigned by copying an existing user
- *3* — the HR record triggers provisioning; **role-based access profiles** are defined and applied, so a new joiner gets the entitlements of the role rather than those of a colleague; completion before the start date is tracked
- *4* — automated provisioning from the HR system into the identity provider and the major applications, with role definitions maintained and joiner readiness measured
- *5* — fully automated joiner-mover-leaver across the estate with continuous entitlement certification, exceptions handled by policy and reviewed rather than by ticket

*The scoring distinction that matters here is copy-a-colleague versus role-based.*
Copying an existing user's access is the single most common cause of entitlement creep
in a mid-market business, and a target that does it cannot be above a 2 on this step
whatever tooling raised the request.

**3. Core employee data & organisational records**
- *0* — no single employee list; headcount is assembled by asking managers, and the payroll register is the de facto record
- *1* — a master spreadsheet maintained by the HR team, re-sent when someone needs it
- *2* — an HR system of record exists but key data is duplicated into payroll, the directory and finance by hand; the org structure is maintained separately as a drawing
- *3* — one authoritative employee master with the organisational and position structure held in it, changes workflow-approved, and downstream systems fed from it
- *4* — the HR system is the acknowledged source of truth for every downstream consumer including identity and finance, with data quality monitored and mover events driving change automatically
- *5* — continuously reconciled across the estate, with position management and effective-dated history supporting planning and analytics

**4. Payroll**
- *0* — payroll is calculated in a spreadsheet and paid by manual bank transfer
- *1* — a payroll system or bureau is used, but every input is compiled by hand and sent as a file or an email each period
- *2* — a payroll system with structured inputs, reconciled manually each run; several countries on several unconnected arrangements with no common view
- *3* — payroll integrated with the HR master so changes flow without re-keying, with a defined pre-run validation and a reconciliation to the general ledger each period
- *4* — largely touchless run with exception-based review, statutory filings automated, payroll cost posted and reconciled automatically, and a consolidated view across countries
- *5* — continuous payroll validation with anomaly detection before the run, and a single global operating model with local compliance handled by configuration

*Record the number of payroll systems and countries regardless of the level.* A 4
achieved in one country and a 4 achieved across seven providers are not the same asset,
and the second carries a separation cost the first does not.

**5. Time, attendance & absence**
- *0* — hours and absence are recorded on paper, in a diary or in a manager's head; payroll is told by email
- *1* — spreadsheet timesheets collected and re-keyed into payroll each period
- *2* — a time or absence system in use for some populations, with manual export into payroll and manual approval chasing
- *3* — time and absence captured in-system with configured entitlement and approval rules, feeding payroll directly without re-keying
- *4* — automated capture at the point of work — clock, badge, mobile or scheduling system — with rules for overtime and premia configured, exceptions flagged, and absence trends reported
- *5* — demand-based scheduling integrated with time capture and payroll, continuously optimised against cost and cover

**6. Performance, compensation review & development**
- *0* — no records; reviews happen by conversation if at all, and compensation decisions leave no auditable trail
- *1* — review forms completed as documents and filed; the compensation round is run in a spreadsheet emailed between managers
- *2* — a system holds review records, but the compensation round is still modelled and approved outside it
- *3* — an in-system review cycle with completion tracked, and a compensation round run in-system against budget with approval rules enforced
- *4* — performance, compensation and progression connected to the employee record and to the reward framework, with cycle completion and distribution reported and pay-equity analysis available
- *5* — continuous feedback and talent data feeding succession and workforce planning, measured for consistency and bias

**7. Learning & compliance training**
- *0* — no record of who has been trained on what
- *1* — training attendance logged in a spreadsheet or on certificates in a drawer
- *2* — a learning system holds courses and completions, but mandatory training is chased manually and currency is not visible
- *3* — mandatory and regulatory training assigned by role from the HR record, with completion tracked, expiry monitored and evidence retrievable for audit
- *4* — automated assignment, reminder and escalation with compliance rates reported by population, and certification currency enforced where a lapse would stop someone working
- *5* — skills and competency data maintained against role requirements and feeding development and workforce planning

**8. Offboarding & access revocation**
- *0* — IT finds out someone has left when a manager mentions it, or when the account goes unused; no list of leavers is shared
- *1* — an offboarding checklist worked by hand, with access removal requested by email; nobody records when it completed
- *2* — a leaver workflow raises the tasks and they are completed manually across the applications; **the process is documented but the lag is not measured**
- *3* — the HR termination record triggers revocation, the primary directory account is disabled on or before the last working day, completion is tracked per system, and final pay and equipment return are workflowed
- *4* — automated deprovisioning across the integrated estate on the effective date, **revocation lag measured and reported**, and periodic reconciliation of active accounts against the active employee list with orphans investigated
- *5* — immediate policy-driven revocation across the whole estate including unfederated and third-party systems, with continuous entitlement certification and an auditable zero-orphan position

*This is the step most often scored too generously.* A documented process with no
measured lag is a 2. A target cannot reach 4 on the strength of tooling alone — the
evidence required is the measured lag and the reconciliation, because the failure mode
is not the absence of a process but its uneven execution.

**9. HR compliance, reporting & data privacy**
- *0* — no HR reporting beyond a headcount assembled on request; nobody can say where employee data is held or how long it is kept
- *1* — periodic reports built by hand in a spreadsheet; retention is "we keep everything"
- *2* — standard reports available from the HR system, and a retention policy exists as a document that is not enforced by any system
- *3* — HR reporting and headcount reconciled to payroll and finance, a data inventory covering employee data, and retention rules applied in the principal system
- *4* — self-service analytics on headcount, attrition and cost with measured data quality; retention and purging automated across systems; subject access and privacy requests handled through a defined, tracked process
- *5* — workforce analytics feeding planning decisions, with privacy controls continuously monitored and evidenced

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
draws on. In H2R the numbers most worth capturing are **headcount, the annual joiner and
leaver counts, the number of payroll systems and the countries they cover, the HR
administration headcount, and above all the measured revocation lag in days** — a score
without the revocation lag beside it has not tested the finding this process exists to
produce.

---

## 5. The index

The **H2R Automation Index** is the weighted mean of the assessed step scores,
normalised to 0–100, on the same formula and the same bands as the other processes:

```
index = ( Σ (step_score × step_weight) / Σ (step_weight) ) × 20
```

where both sums run over assessed steps only.

| Index | Band | What it means for the deal |
|---|---|---|
| **0–20** | **Manual** | The employee lifecycle runs on documents and mailboxes. There is no reliable employee master, so access rights, headcount and payroll cannot be reconciled to one another. Expect a security finding on revocation and a personal-data retention finding alongside the administrative cost. |
| **21–40** | **Emerging** | Systems exist at the ends — usually recruiting and payroll — with a manual middle holding them together. Every status change is re-keyed several times. The exposure is in the joins, not in the systems. |
| **41–60** | **Standardised** | A defined, system-mediated lifecycle with real gaps, most often in revocation timeliness and in the feed into payroll. The usual mid-market shape, and improvement is available without replacing the HR system. |
| **61–80** | **Integrated** | Joiner-mover-leaver flows from the HR record into the estate, with revocation measured. Remaining gains are optimisation and coverage of the unfederated tail. |
| **81–100** | **Optimised** | Automated lifecycle management with continuous entitlement certification. Rare outside larger or regulated businesses. Verify the orphaned-account reconciliation before accepting it. |

**The index is a summary, not the finding, and in this process that is truer than in any
other.** A deal team will act on two specific things in this payload far more often than
on the number: **the revocation lag** and **the payroll system count**. A target scoring
a respectable 58 with an eleven-day average revocation lag has a security finding the
index conceals, and a target scoring 58 across six payroll providers has a separation
cost the index does not express at all. Read those two answers before reading the band.

---

## 6. Reading the shape

Three patterns recur often enough to be worth naming. The step ranges and the wording
are declared in `hire_to_retire.yaml` under `shape`, so the note the product prints is
content rather than code.

The front end here is steps 1–3 (recruiting, onboarding and the employee master) and the
back end is steps 7–9 (learning, offboarding and compliance reporting). Unlike P2P and
O2C, the two ends are not sequential stages of one transaction — they are the beginning
and the end of an employee's tenure, often years apart, and that is exactly why the gap
between them is informative: **the same organisation is enthusiastic about the arrival
and indifferent to the departure.**

- **Front-loaded** (steps 1–3 strong, 7–9 weak). The overwhelmingly common shape, and
  the one this process is most often assessed to find. Hiring is visible, competitive and
  owned by someone senior, so it gets tooling; leaving is administrative and nobody's
  priority. The consequence is not inefficiency but **a growing population of live
  credentials belonging to people who no longer work there**, and a personal-data
  retention position nobody can evidence. Both are findings for the security and legal
  workstreams rather than for the cost case, and a buyer's HR systems business case
  almost never mentions either. Ask for the measured revocation lag before accepting any
  reassurance about this shape.
- **Back-loaded** (steps 7–9 strong, 1–3 weak). Uncommon, and where it occurs it usually
  means a regulated business that was made to evidence training currency and leaver
  controls by an auditor, while the employee master underneath remains a spreadsheet.
  The controls are real but they are being operated manually on top of unreliable data,
  so they are expensive and they will fail quietly the moment volume rises. Treat the
  compliance evidence as sound for now and the cost of maintaining it as understated.
- **Uniformly low with a modern HR platform.** The licence is not the process. As in the
  other three, the clearest signal that the last implementation stopped at go-live. In
  H2R it carries a specific implication: an HR platform that is not the source of truth
  for identity means the provisioning and revocation integrations were the part that was
  descoped, which is precisely the part that carries the security exposure — so the
  remediation is cheaper than it looks and more urgent than management believes.

Watch also for the pattern the shape note cannot see: **a strong middle with weak
ends** — a competent employee master and payroll sitting between manual recruiting and
manual offboarding. It reads as a moderate index and behaves adequately day to day, but
it is the configuration in which the revocation finding is most easily missed, because
the HR data itself is good and the assessment feels reassuring.

---

## 7. Provenance and status of this model

`[EXT]` — this model is **not** taken from Roehl-Anderson (2013). `DD_master.md` was
searched for HR, human resources, payroll, employee data, joiner-mover-leaver,
onboarding, offboarding, provisioning and recruiting content before this document was
written. It contains **no hire-to-retire process decomposition**, and its only material
on the subject is incidental:

- **HR as a data-room folder** [p. 83–84, Exhibit 5.9] — listing what IT information is
  found there: IT organisation charts, target employee count, employee locations, IT
  CVs, IT job responsibilities, and the employee roster. This is guidance on where to
  look for *IT* information, not a model of the HR process.
- **"HR separation" as a Day 1 area with critical IT dependencies** [p. 253–254],
  alongside finance separation, rebranding and network connectivity. This corroborates
  §1's point that multi-country payroll and HR systems are a separation problem, and it
  is cited for that and nothing more.
- **"IT human resources" in the IT risk management areas** [p. 285] — which concerns the
  IT function's own staffing, not the employee lifecycle process.

None of the three is a process model and none is cited above as though it were. The
security reading in §1 and §2 is the platform's own, and follows from the joiner-mover-
leaver control being the mechanism the security workstream depends on rather than from
anything in the source.

This document is therefore built for this platform, from the same two sources as the
other three models: standard process taxonomy (the APQC-style L1/L2 decomposition in
common use) and the maturity-ladder pattern that CMMI popularised and every major firm's
process assessments now use in some form.

It is **a calibration, not an authority**, and should be tuned against real engagements
exactly as `DD_master.md` §15.1 says of the scope engine's mix weights. The tests are
what make that tuning safe: change a weight, and the case that breaks tells you what you
broke.

The weights in §3 are the thing most likely to need adjustment, and two of them are
deliberately contestable: **offboarding at 14 is high for a step with near-zero
transaction volume**, and **learning at 7 is low for a regulated target**. Both are
argued in §3 and both live in `backend/app/reference/processes/hire_to_retire.yaml`,
editable by a practitioner without a developer. The bands in §5 are shared with the
other processes and should not be moved for one process alone.

**Record to Report was defined alongside this document** — see
`R2R_AUTOMATION_MODEL.md`. With both, all five processes named in the Assess module are
defined and the module's content is complete.
