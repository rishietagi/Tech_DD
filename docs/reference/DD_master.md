# docs/reference/DD_master.md — Technology Due Diligence: Master Reference

**Status:** authoritative domain reference for the Tech DD platform. Phase 1 (routed app + intake) is built; this file is the input to Phase 2, the scope-of-work engine. Read this
alongside `CLAUDE.md` (project constitution) and `docs/phases/PHASE1_PLAN.md` (Phase 1 build).
This file is what the scope-of-work engine encodes.

**Primary source:** *M&A Information Technology Best Practices*, ed. Janice M.
Roehl-Anderson (Wiley, 2013) — a Deloitte-authored practitioner volume. Page
citations in square brackets `[p. 70]` are printed pages of that book. Chapter 5
("IT Due Diligence Leading Practices", Andrews & Sternberg) is the spine of §3–§9.

**Two provenance rules, applied throughout:**
- Content traceable to the book is cited. Anything marked **[EXT]** is a modern
  extension *not* in the source — added because the book predates cloud-native
  SaaS, DevOps metrics, open-source licence hygiene, GDPR/DPDP, and AI/ML as a
  diligence subject. Treat **[EXT]** as reasoned practice, not sourced authority.
- Content marked **[DATED]** is in the book but should be handled with care today.

---

## 1. What technology due diligence is, and what it must produce

### 1.1 The primary objective (sourced, near-verbatim)

The primary objective of an IT due diligence assessment is to understand those
matters — risks or issues — that can have a **material impact on the value of the
target business** and that the buyer must account for prior to acquisition (and
often plan for or address post-acquisition) [p. 70]:

1. Identification of previously unknown or undisclosed risks and opportunities
   (e.g. departing intellectual property).
2. **One-time IT costs** to integrate the acquisition (e.g. setting up an ERP
   replacement system).
3. **Impact on recurring IT costs** to run the business (e.g. maintenance costs of
   ERP licences and support).
4. Evaluation of opportunities such as **IT-enabled synergies** (e.g. rationalisation
   of similar applications).

Secondary but material: DD is the opportunity to collect information that
accelerates post-transaction activity — Day 1 tasks, midterm and end-state visions
[p. 70].

Two claims from the source that justify the whole exercise:
- *"IT generally has the highest cost to achieve post-merger benefits"* and *"the
  majority of planned synergies in many deals are dependent upon the successful
  completion of a post-transaction IT initiative. So a lack of information
  discovered during the pre-deal process could make or break a deal."* [p. 70]
- *"IT Is the #1 Driver of Synergy Benefits"* / *"IT Is Typically the Largest Cash
  Cost to Achieve"* — Deloitte analysis of 30+ prior merger-of-equals transactions
  [p. 184].

### 1.2 Why a tech DD is not a normal IT assessment

The book is explicit that M&A DD ≠ standard IT assessment [p. 69–70]. The
differences drive every design decision in the tool:

| Constraint | Consequence for scope |
|---|---|
| Accelerated pace, fixed deadline | Scope must be prioritised, not exhaustive |
| Limited information; may have no data room yet | Scope must name evidence requests, not assume access |
| Little or no access to target IT management | Scope must plan around a single CIO interview |
| Extreme confidentiality; few target staff "over the fence" | Questions must be askable "under cover" |
| Deal team priorities change mid-stream | Scope must be re-generatable and versioned |

*"Potential buyers that overlook, or minimize, IT due diligence during a proposed
transaction often pay a high price later on through unexpected conversion costs,
consolidation methods, or environment improvements."* [p. 69]

### 1.3 The deliverable

A tech DD produces, at minimum:
- A **disposition** — go / go-with-conditions / no-go signal to the deal team, with
  prioritised findings.
- **Order-of-magnitude cost estimates**, one-time and recurring. The book is
  emphatic: *"it is not practical for the due diligence team to identify exact costs
  ... cost estimates provided to the deal team should be order-of-magnitude ranges"*
  and every estimate must document its assumptions and the sensitivity of the
  estimate if those assumptions do not hold [p. 87].
- **Open matters** requiring further investigation in later phases [p. 87].
- A **mapping to post-transaction plans** — see §10.

---

## 2. Where DD sits in the deal lifecycle

The source lifecycle [p. 5–6]:

```
        LOI signed              Deal signed (Day 0)          Deal closed (Day 1)          Day 2
            │                          │                            │                       │
  ┌─────────┴──────────┐   ┌───────────┴────────────┐   ┌───────────┴──────────┐  ┌─────────┴────────┐
  │   DUE DILIGENCE    │   │ INTEGRATION/SEPARATION │   │ INTEGRATION/SEPARATION│  │  END STATE /     │
  │ "Getting the       │   │ PLANNING               │   │ EXECUTION             │  │  TSAs TERMINATED │
  │  required info     │   │ "Aligning or           │   │ "Effectively executing│  │  FULL SEPARATION │
  │  up front"         │   │  separating systems    │   │  the acquisition or   │  │                  │
  │                    │   │  and processes"        │   │  separation"          │  │                  │
  └────────────────────┘   └────────────────────────┘   └───────────────────────┘  └──────────────────┘
```

- **LOI signed** — period of exclusivity; due diligence initiated [p. 5].
- **Day 0 (deal signed/announced)** — regulatory and shareholder approvals;
  integration/separation planning initiated [p. 5].
- **Day 1 (deal closed)** — financial close; execution begins [p. 5].
- **Day 2** — full separation; TSAs terminated (divestiture side) [p. 14].

**Blueprinting rule:** *"start with the end in mind and work backward to Day 1"*
[p. 10]. Milestones are framed as **Day 1, Day 1+30, Day 1+90** [p. 10]; the interim
blueprint milestone is *"most often after the first or second quarter after closing"*
[p. 187]; *"most of the strategic and operational changes that are envisioned should
be in place after the first six months"* [p. 50].

**Day 1 must-haves** (the irreducible minimum, verbatim structure) [p. 10]:
1. *Keep the business running* — take orders, invoice customers, deliver product.
2. *Comply with federal, legal and regulatory requirements* — licences transferred,
   applied for, or in place; contracts assigned; consolidated financial reporting.
3. *Deliver Day 1 must-haves* — e-mail connectivity, voice mail, some level of file
   transfer capability.

**Why this matters to scoping:** DD scope is set by what the *next* phase will need.
A scope that answers "is this asset sound?" but not "what will Day 1 cost and how
long will it take?" has failed its downstream consumer.

---

## 3. The two archetypes — and why the split is real

The source draws the line explicitly. Ordinary IT DD covers **people/process/
spending, applications, infrastructure**. Where the target's own software *is* the
revenue-generating asset, the book adds a distinct mode:

> *"With the proliferation of companies whose core operations are their IT systems,
> there is an increasing number of IT due diligence efforts focused on assessing
> proprietary technology. The overall evaluation areas in a proprietary due diligence
> are the same as those covered previously, but with additional depth of analysis and
> specific measures focused on assessing the architecture, maintainability,
> reliability, scalability, and security of the custom platforms that the company
> delivers to its clients."* [p. 76–77]

So the source position — and the platform's position — is:

**Product DD is not a different subject. It is the same subject plus a mandatory
additional depth layer on the product platform.** The archetypes below are a
weighting of effort, never a menu where one excludes the other.

### 3.1 Effort baseline (sourced)

*"Typically, approximately 80 percent of the due diligence effort may be placed on
people, process, and spending; applications; and infrastructure. The remaining
20 percent generally is tailored to the particular situation or some
out-of-the-ordinary feature(s) of the buyer and/or target."* [p. 72]

```
├──────────────────────── 80% ────────────────────────┤├──── 20% ────┤
  People, Process        Applications   Infrastructure   Other client-
  and Spending                                           specific focus
```

The scope engine's job is to decide **what fills the 20%** and **how the 80% is
re-weighted** — not to invent a new framework per deal.

### 3.2 Enterprise Tech DD (technology as enabler)

Question answered: *does the IT estate support the plan, and what will it cost?*

Core workstreams: operating model / IT organisation; vendors and contracts;
processes and controls; IT strategy and project portfolio; IT spending (capex/opex
run-rate); application landscape (commercial + ad-hoc tools); infrastructure (data
centre, servers, network, end-user, DR); cyber, risk and compliance; separation /
integration effort; TSA scope where relevant.

Signals that pull this way: traditional or asset-heavy line of business; COTS/ERP-
heavy estate; small engineering headcount relative to total; carve-out or corporate
separation; cost-takeout or buy-and-build thesis; strategic acquirer intending to
integrate onto an existing platform; heavy on-premise footprint.

### 3.3 Product / Proprietary Technology DD (technology as the asset)

Question answered: *can this product and the team behind it carry the growth case?*

The book's own dimensions for proprietary technology DD (Exhibit 5.6, verbatim)
[p. 77]:
- Product strategy and product value versus select competitors.
- Organizational effectiveness and maturity of product management, development,
  and support teams.
- Functionality of the system is appropriate within the industry domain.
- Architecture — the design of both the software and hardware components of the
  system that enable reliability, scalability, and maintainability.
- Reliability and the impact to the client (and the company) of the software and/or
  services becoming unstable.
- Scalability and the ability to add new customers and clients as the business
  expands.
- Maintainability and the level of complexity (and resulting cost) to incorporate bug
  fixes and enhancements.
- Age/viability of underlying software, system, and service environments.

Consequence, verbatim: *"If any of the factors noted in Exhibit 5.6 are found to be
inadequate, the platform may require significant time and resources to bring it back
to the level necessary to drive business operations effectively."* [p. 77]

**[EXT]** Modern product DD adds, beyond the book: delivery performance metrics
(deployment frequency, lead time, change failure rate, MTTR); SDLC, code review and
test automation practice; open-source licence hygiene and SBOM; IP ownership and
contributor assignment; third-party and API dependency risk; multi-tenancy and
tenant-isolation design; infrastructure unit economics (COGS per customer/tenant);
data and AI/ML capability, model governance and data rights; product analytics and
PMF evidence; key-person concentration in the engineering org.

### 3.4 The blend

Real engagements are a blend. Express it as a **mix ratio** (0 = pure enterprise,
100 = pure product), never a binary. Both archetypes always retain a floor of the
other's mandatory items: a digital-native still has vendors, contracts, compliance
and IT spend; a traditional manufacturer still has custom applications worth
reviewing.

---

## 4. Scoping drivers — what actually changes the scope

These are the variables the engine reasons over. Each has a sourced effect.

### 4.1 Deal type [p. 71, Exhibit 5.1]

| Deal type | Effect on scope |
|---|---|
| **Full acquisition** | *"often full acquisitions are a more straightforward deal type"*; scope depends on the other factors below |
| **Carve-out** | Identify shared resources (which may need to be replaced) and their replacement costs. Likely TSA requirement. *"a carve-out transaction is typically more challenging due to shared resources and systems between the target business unit and the parent company"* [p. 70] |
| **Joint venture** | Greater coordination — both parties may run DD simultaneously. Future integration road map may be unclear → more complex cost/synergy analysis. Post-transaction reporting requirements must be accounted for |
| **Divestiture (sell-side)** | Same domains, inverted lens — see §4.7 |

Carve-out-specific investigation areas, verbatim [p. 78]:
- What staff, applications, and infrastructure are provided by or shared with the
  parent? What is planned for inclusion with the transaction?
- Which licences cannot transfer with the transaction?
- What interfaces will need to be disentangled?
- What transition services are being contemplated and for what length of time?
- What are the estimated one-time investment and recurring costs for a stand-alone
  IT environment?

Common carve-out findings [p. 78]: shared resources will need to be replaced;
specific human resources will not accompany the transaction (loss of operational
efficiency due to lack of IP); the seller has not fully vetted the TSAs to be
offered; **there is a significant difference between the seller's estimated costs and
the buyer's estimated costs**.

Joint-venture investigation areas [p. 78]: expected breakdown of IT
responsibilities, systems and funding from each partner going forward; whether one
partner's systems have better functionality/scalability aligned to the deal team's
future strategy. Common findings: organisation support and future IT strategy
expectations do not align; post-transaction reporting requirements undetermined.

### 4.2 Buyer type — strategic vs financial [p. 78–79]

The book's position is precise and worth quoting because it is frequently
misremembered: *"the due diligence team should focus on the same areas regardless of
whether they are supporting a financial buyer or a strategic buyer. However, the
team's lens should be different."* [p. 78]

**Strategic buyer** [p. 78–79]:
- More interested in the details of the target's IT environment — they must decide
  whether to run it stand-alone or integrate it.
- If integrating: document the specifics of **each** aspect of the IT domain
  (organisation, processes, applications, infrastructure).
- Determine potential synergies between buyer and target IT environments, including
  rationalisation of resources, processes and systems.

**Financial buyer** [p. 79]:
- Investment with a defined exit strategy; often fairly hands-off with ongoing
  management.
- *"may care more about the short-term financial risks of the investment than the
  longer-term issues."*
- Method: *"an initial high-level review across each aspect of the IT domain,
  followed by a more targeted assessment in the specific areas that appear to have
  significant risk or cost impacts (including opportunities to gain cost efficiencies
  through IT investment)."*

Reinforced in Appendix A [p. 496]: financial buyers (PE, VC, hedge funds, family
offices) *"typically have an investment time horizon of four to seven years"* and
*"generally need the target business's back-end infrastructure to endure"* — so their
playbook focuses **less on integration with existing systems and more on the
development of TSAs and use of outsourcers**. Strategic buyers *"focus less on the
strength of the target company's existing back-office infrastructure ... as these
functions will often be eliminated during the post-transaction integration phase"* and
more on synergy identification and data migration to the buyer's systems.

### 4.3 Integration requirement [p. 71]

If the target is planned to be integrated into the buyer's environment (or vice
versa): IT resources and systems may require rationalisation; **thorough system
scalability assessments may be required** because users may be transferred onto an
existing buyer or seller system; an unclear future road map makes cost/synergy
estimation more complex.

Integration models (four, used consistently across Ch. 1–3 and mirrored in the
Appendix A naming Retention / Assimilation / Metamorphosis / Transformation)
[p. 10–11, 28–29, 498]:

| Model | Description | IT consequence |
|---|---|---|
| **Consolidation** (Assimilation) | Rapid conversion of one company to the other's strategy, structure, processes, systems | Easiest path to aggressive synergy targets; parent standards dominate; migration planning is the scope |
| **Combination** (Metamorphosis) | Select the most effective processes/systems from each | *"best path toward achieving aggressive synergy targets"*; scope must support best-of-breed selection with a scoring model |
| **Transformation** | Synthesise disparate pieces into a new whole | Significant people/process/technology impact; new architecture defined; heaviest change management |
| **Preservation** (Retention) | Companies retain unique capabilities and cultures | Minimal standardisation beyond contracts consolidation and financial reporting roll-up; scope narrows to interfaces and consolidation reporting |

Model selection is driven by overlap [p. 37]: high business-model parity + high scale
parity → Consolidation; high business-model similarity, low scale parity →
Combination; low overlap on both → Preservation; low business-model similarity, high
scale parity → Transformation.

Chapter 4's coarser taxonomy is also useful for scoping [p. 48]: **full integration**
(same industry/segment; single platform for e-mail, HCM, CRM, ERP), **partial
integration** (geographically distant or diversification-driven; select systems
integrated), **minimal integration** (holding company; *"IT integration may be only for
financial reporting purposes"*, and *"the ability to divest the acquired organization
is much easier down the road"*).

### 4.4 Target size relative to buyer [p. 71]

- **Not significant vs buyer** — less time to review and finalise disposition
  (smaller IT footprint); more likely to adopt the buyer's systems.
- **Significant vs buyer** — more information to review, so more time; harder to
  determine whether the buyer's systems will be the end-state platforms.

Appendix A adds [p. 497]: a target small in revenue can still be highly complex if
it operates in multiple business segments, legal entities, countries, or platforms,
or if its **business model differs significantly from the acquirer's** — in which case
adoption of the buyer's systems may simply not work.

### 4.5 IT landscape complexity [p. 71]

Low complexity → quicker dispositions. High complexity → the level of
interdependencies between systems and processes requires more time, and **may require
support from buyer subject matter advisers or external resources**.

### 4.6 Timing / available access [p. 71]

- Sufficient time → greater ability to drill into concerning areas.
- Limited time → *"Quickly need to assess what is most important to deal team, and
  drive toward finding the most critical issues that could affect the deal."*

**[EXT]** Access level is a first-class scope constraint distinct from time: full data
room + management sessions + code access; data room + management; data room only;
public information only. Code-level product DD is impossible without code access; a
scope that promises it anyway is a scope that will fail.

### 4.7 Sell-side vs buy-side [p. 70–72]

The book is buy-side-oriented but states the attributes translate. Sell-side
differences [p. 72]:
- Much can be done **before the buyer interacts with the seller**: collection and
  preparation of data room documentation, and a determination of *what level of
  detail should be shared*.
- *"Careful data preparation provides confidence to potential buyers because it shows
  that the target company has mature documentation and processes and is being
  transparent and willing to share information."*
- Appendix B: the same DD checklist is used by a seller pre-market to find and fix
  issues that would depress perceived value [p. 509].
- Ch. 9 sell-side DD objectives [p. 152]: assess the current IT function to maximise
  perceived value to buyers; identify cost-reduction opportunities for the **remaining**
  (parent) organisation; support buyer DD information requests.

### 4.8 Regulatory and data sensitivity **[partly EXT]**

Sourced: policies and controls must promote compliance with industry and regulatory
standards, *"e.g., HIPAA, PCI"* [p. 73]; named frameworks are **COBIT 5.0, ISO 27002,
GAPP** [p. 286]; named regimes include SOX 404 with SSAE 16 / SOC 1 for shared or
split systems, FFIEC, 12 CFR 216, PCI DSS, BIS 35, HITECH, HIPAA, OIG [p. 288–289].
**[DATED]** — PCI DSS v2.0 and SSAE 16 are superseded; today read PCI DSS v4.x and
SSAE 18 / SOC 2.

**[EXT]** Add GDPR, UK GDPR, India DPDP Act, CCPA/CPRA, NIS2, DORA (EU financial),
plus SOC 2 Type II as the de facto B2B SaaS baseline. Any of these being in scope
makes a compliance workstream **mandatory regardless of archetype**.

### 4.9 AI/ML dependence **[EXT]**

Not a subject in the 2013 source. Where AI/ML is embedded in the product or core to
the value proposition, add a workstream covering: model inventory and lineage;
training-data provenance and rights; vendor/model lock-in and pricing exposure;
inference cost per unit of revenue; evaluation and monitoring practice; model and
data governance; regulatory exposure (EU AI Act, sectoral rules).

---

## 5. Complexity → level of effort

The book frames Exhibit 5.1 as the instrument for estimating effort: *"The level of
effort and the number of resources required to conduct a due diligence assessment can
be estimated more effectively by understanding potential project characteristics and
complexities"* [p. 70]. The six criteria are: **Deal Type, Integration Requirements,
Target Size, IT Landscape, Timing** [p. 71] — with buyer type and DD scope
(back-office vs proprietary technology) named separately as further refiners [p. 72].

**Encodable model [EXT, structure only]:** score each driver, sum to a complexity
band, and use the band to set (a) number of workstreams opened, (b) depth tier per
workstream, (c) indicative team shape and duration. The drivers and their directions
are sourced; the arithmetic is the platform's.

---

## 6. The workstream library

This is the canonical module set. Each module below carries: **objective**, **areas of
investigation** (sourced questions where available), **evidence requests**, **common
findings**, and **applicability**. The scope engine selects and depth-tiers these.

### 6.1 W-OPS — IT Operating Model, Organisation and People
*Archetype: both. Almost always in scope.*

Areas of investigation, verbatim [p. 73]:
- Is IT managed to deliver value to the business?
- Is the IT organization sufficient to support the current business and expected
  growth?
- What is the mix of staff skills and experience? Are there any areas where IT staff
  support is limited?
- Is there sufficient redundancy or cross-training on critical knowledge areas?
- Are there succession plans for staff?
- Is IT leadership capable and well suited for successfully driving the company's IT
  strategy and operation?
- Are there planned or anticipated changes to the company's operating model?

Common findings [p. 73]: lean IT organisation that will require expansion to support
future growth plans; staff to proactively target for retention post-transaction;
areas where institutional knowledge has been lost or is at risk; IT skills not
aligned with current/future requirements; abnormally high staff turnover; lack of a
dedicated leader.

Evidence: IT organisation charts, employee roster (often with salary), IT CVs, job
responsibilities, employee locations, outsourcing arrangements, tenure, training,
compensation structure [p. 84, 510].

Cross-reference: key-person risk and retention are treated at length in Ch. 20 —
critical talent identification, departure-risk assessment, retention tooling,
programme management [p. 362]; and *"key employees begin to receive external job
inquiries within days or weeks of an M&A announcement"* [p. 121].

### 6.2 W-VEN — Vendors, Contracts and Licensing
*Archetype: both. Mandatory where any transfer of contracts occurs.*

Areas of investigation, verbatim [p. 73]:
- What services are provided by external vendors?
- What contingency plans are in place if the vendor needs to be replaced?
- Does each vendor sufficiently meet company needs, and are their rates competitive?
- How well are strategic vendor relationships managed?
- How flexible are the current vendor contracts?
- Are all software licences current?

Common findings [p. 73]: non-current software licences; expired contracts;
**contracts that are non-transferable**.

Checklist items [p. 511]: vendor viability; licences; terms and conditions; transfer
or relicensing fees; contract termination fees.

Why this workstream is disproportionately dangerous — from Ch. 13:
- *"Your suppliers ... control the fate of your deal far more than you may expect.
  They may even have the power to stop it."* [p. 199]
- Suppliers may threaten to discontinue Day 1 service; charge exorbitant assignment
  or transition fees; assess punitive termination penalties; require version upgrades
  or extra licences; require reinstated maintenance; or use the deal as a pretext to
  audit or renegotiate the entire contract [p. 199–200].
- **Supplier lead time to grant contractual rights: up to six months** [p. 222, 474].
- Right-to-use clauses may permit continued use for up to a year post-close; absence
  of such provisions is a cost risk requiring new licence purchases [p. 102].

Four cost categories for third-party spend [p. 206]: **transaction costs** (one-time
separation), **operational costs** (reversing operating decisions; *"can become
dis-synergies"*), **stranded costs** (retained assets no longer needed), **dis-synergies**
(unit-cost increases from reduced volume).

Business intent taxonomy — a clean enum for the tool [p. 208]: *Assign in full;
Assign in part; Buyer stand-up; No action needed; Terminate; Transition services
agreement (TSA); Reverse TSA.*

Supplier prioritisation criteria [p. 213]: business criticality; spend; renewal
dates; time remaining until renewal; structural lead-time issues; complexity of
agreement; specifics of relationship; supplier risk; resource capacity; data
availability. *"Rarely are there more than 50 suppliers on the list even for very
large, multinational companies."*

### 6.3 W-PROC — IT Processes, Controls and Compliance
*Archetype: both. Mandatory where regulated data is present.*

Areas of investigation, verbatim [p. 73]:
- Are the IT processes and controls well defined and documented?
- Are IT processes sufficient for supporting proper alignment with company strategy
  and effective management of company IT?
- Do company policies and controls promote compliance with industry and regulatory
  standards (e.g., HIPAA, PCI)?
- What security/privacy protocols are in place at the company?
- Have there been any historical security breaches? Are policies in place to deal
  with breaches?
- How often are IT operations metrics reviewed?

Common findings [p. 73–74]: lack of disaster recovery and other documented
processes; processes are not comprehensive; audits have uncovered critical issues
that have not been remediated; IT operations are not monitored or not run in an
effective and efficient manner.

IT risk management areas to cover, verbatim [p. 285]: Architecture; Asset
management; Business continuity management; Change management; Contracting and
outsourcing; Information security; IT financial control; IT human resources;
Operations records management; Physical and environmental problem management;
Privacy and data protection; Project management; Technology licensing.

### 6.4 W-STRAT — IT Strategy and Project Portfolio
*Archetype: both.*

Areas of investigation, verbatim [p. 74]:
- How well do planned initiatives align with business needs?
- What enhancements or changes to IT are planned or needed?
- What projects do not align with buyer's post-transaction integration plans, IT
  environment, or IT strategy?

Common findings [p. 74]: lack of an IT road map; projects that do not add business
value; planned or in-flight projects that may need to be placed on hold or deferred.

**Project triage rule (encodable)** [p. 8, 148]: priority goes to IT projects that
(1) link to critical Day 1 requirements, (2) enable or accelerate large synergy
opportunities, or (3) are essential to implementing future strategic initiatives.
Everything else is a candidate for hold or cancellation.

### 6.5 W-SPEND — IT Spending, Run-rate and Capex
*Archetype: both. Weighted heavily for financial buyers and cost-takeout theses.*

Areas of investigation, verbatim [p. 74]:
- Does the technology spend seem reasonable and appropriate?
- What future investments in company IT are planned or may be needed?
- Have there been any significant variances in the operating budget year-over-year?
- Have there been any unusual or unexpected costs related to software or
  infrastructure that have occurred recently?

Common findings [p. 74]: capital and operating expenditures disproportionate to
comparable companies or historical trends; unexplained year-over-year variances.

Evidence [p. 84]: IT budgets, historical IT expenses, fixed asset inventory, audit
controls — **these live in the Finance folder of the data room, not the IT folder**.

Benchmark caution, verbatim [p. 81]: *"the team should utilize benchmarks with care,
as factors unique to each organization's specific situation can significantly impact a
company's actual spending needs."*

### 6.6 W-APP — Application Landscape
*Archetype: both. The book: "significant effort should be spent on this aspect."* [p. 74]

Areas of investigation, verbatim [p. 75]:
- **Application landscape**: What are the major IT applications used to support the
  business? What business functionality is supported by each system, and are there
  any areas where system support is lacking (i.e. require manual processes)? What
  system interfaces and dependencies are in place, and how complex are they? What is
  the level of system stability, availability, and scalability?
- **Commercial applications**: What version of each application is in use, and what
  other underlying technology is required? What licence, maintenance, and support
  agreements are there for each application? What is the level of customization?
- **Custom-developed applications**: What technology is used to develop each system?
  What software development process and coding practices are in place? What is the
  level of scalability, reliability, maintainability, and security of the systems?
  Does the system support the required functionality to have parity with comparative
  systems? Does the system design and architecture support the preceding attributes?
- **Ad hoc tools**: Are any business processes supported by ad hoc tools (e.g. Excel
  spreadsheets)?

Common findings [p. 75]: frequent availability/reliability issues; complex
application suites; system not readily scalable; known security holes; non-compliant
IT systems; significant level of user complaints; **buildup of technical debt**;
obsolete applications; heavy customisation that makes upgrade difficult; obsolete
technologies constraining performance; poorly documented systems and maintainability
problems; inability to scale to future requirements; business process limitations
requiring investment; data inconsistencies from manual entry.

Application checklist scope [p. 510]: ERP; finance and accounting; CRM; SCM; BI;
ECM; BPM; PLM; HRMS; industry-specific applications (proprietary and open source);
office productivity (e-mail and calendaring, IM, collaboration, personal
productivity).

Rationalisation criteria to apply, verbatim [p. 64]: *"Business criticality of the
application. Applicability to current and future processes. Operational supportability
and sustainability. Vendor viability assessment. Usage, maintenance, and licensing
cost. Compatibility with current ERP."* Ch. 12 adds a **scoring model on functionality,
supportability and cost** [p. 196].

### 6.7 W-INFRA — Infrastructure, Hosting and Resilience
*Archetype: both.*

Areas of investigation, verbatim [p. 76]:
- What is the state of the data center environment (HVAC, power, backup power,
  backup generator, etc.)?
- What level of excess capacity is in the data center?
- What is the composition of the company's IT asset inventory (including existing
  assets, useful life, and refresh/replacement expectations)?
- What type of network connections and bandwidth does the company have?
- What is the current utilization of servers, storage, and network capacity?
- How does the company support system availability and performance monitoring?
- What is the level of redundancy in servers, storage, network, and data center HVAC
  and power?
- Does the company have established data backup and disaster recovery procedures?
- What information security mechanisms are in place at the company?

Common findings [p. 76]: obsolete servers, workstations, network appliances;
historical lack of investment in infrastructure; future investment required to
maintain currency or support growth; limited or no disaster recovery capability;
reliability issues; no redundancy in data centre or backups; insecure data centre.

**Full infrastructure inventory** to request (verbatim, Ch. 6) [p. 92]: Data centers;
Hosting services; Disaster recovery infrastructure and services; Servers (physical
and virtual); Mainframes; Storage infrastructure (e.g. SAN); Databases and data
infrastructure; Backup or tape infrastructure; Managed print services; Batch
processing; Software licensing; Hardware maintenance agreements; WAN; LAN; Internet
services; Web services (e.g. domain names); E-mail and messaging services; Active
directory; Call center infrastructure; Desktop and laptop computers; Mobile devices;
Telephony (VoIP, traditional PBX); Help desk services.

**Lead-time red flag** [p. 93]: order and procure new or changed dedicated circuits as
early as possible, *"especially for international locations, some of which can have
particularly long procurement lead times"*; multinational firewalling and testing can
take **four to six months**, country by country [p. 259].

### 6.8 W-SEC — Cyber Security, Risk and Controls
*Archetype: both. Depth escalates with data sensitivity.*

Risk differs by activity type [p. 284–285]:
- **Synergies** — DD gets overlooked post-planning; documentation adherence lapses;
  security configuration and change management activity diminishes; access becomes an
  afterthought.
- **Integrations** — new platforms expose internal and external threats; *"malicious
  outsiders may target announced deals"*; constrained staff *"rubber-stamp"* access,
  exception and change requests.
- **Divestitures** — compliance/audit requirements in flux; employee transition hits
  morale; segregation-of-duty requirements on shared systems get overlooked.

Note the counterintuitive sourced claim: risk profile differs by **deal type, not deal
size** — *"Smaller projects involving nonpublic companies can even introduce greater
risk"* due to weaker compliance adherence [p. 284].

Access certification types [p. 296]: **complete** (comprehensive, semiannual —
thorough but labour-intensive and prone to rubber-stamping); **delta** (only new
access since last review — efficient but can miss earlier gaps); **triggered**
(event-based, e.g. after final application separation). Recommended at minimum at the
outset and soon after Legal Day 1.

Three data-protection initiatives [p. 299–300]: implement data protection plans
(covering the full lifecycle — collection, storage, usage, transfer, destruction);
conduct technical security reviews and scans after changes and before Legal Day 1;
elevate monitoring and log correlation during the uncertainty of M&A.

**[EXT]** For product DD add: product security architecture, tenant isolation, secrets
management, dependency and supply-chain security (SBOM), vulnerability management
SLAs, penetration-test history, bug bounty, incident history and post-incident
practice.

### 6.9 W-DATA — Data, Privacy and Migration/Separation
*Archetype: both. Mandatory in carve-outs.*

Key distinction, verbatim [p. 169]: *M&A aims at **data integration**; divestitures aim
at **data separation**.* Cut-over strategy is the second axis: parallel legacy systems
→ target is **synchronisation** (middleware); consolidation → target is
**standardisation and migration**.

Nine-step data road map [p. 169–172]: (1) identification of data assets; (2)
assignment of data owners; (3) prioritisation based on value and risk; (4) data
definition (dictionaries); (5) data quality assessment; (6) data mapping; (7) data
requirements definition; (8) data solution implementation; (9) post-execution
assessment and audit.

Data quality questions, verbatim [p. 170]: *"How complete are the data? How consistent
are the data? How many duplicates exist? How up-to-date are the data? How much of the
data is corrupted?"*

Governance minimum [p. 167–168]: a **data steward** per domain (deep understanding of
business meaning, quality, suppliers, consumers, business rules) plus an **executive
owner**; on the IT side, architects, application specialists and information security
experts per domain. Named tools: **clean room** and **data masking** [p. 168].

Data elements that commonly require Day 1 protection [p. 519]: customer terms and
conditions; customer-specific pricing; product costs and margins; sales forecast,
revenue views, demand plan; customer-specific sensitive information; customer issue
management; financial transactional data; revenue recognition policies and
methodology; product development lifecycle information; product information.

Archiving rule [p. 168–169]: archived data must be preserved *"in a format that can be
accessed independently of any applications that may become inaccessible as part of the
transaction"* — which may mean retaining an application solely for archive access.

### 6.10 W-SEP — Separation / Carve-out Readiness and TSA Scope
*Archetype: both. Triggered by carve-out, divestiture, or TSA involvement.*

Day 1 option pattern per domain (network, e-mail, AD, data centre, applications)
[p. 94–101] — branch on TSA vs no TSA, and seller side vs buyer side:

| | No TSA | TSA |
|---|---|---|
| **Seller side** | *Separation to stand-alone infrastructure* / "clone and go" — lowest risk to seller, long lead time, requires most other services cut over first | *Restricted access (TSA gateway)* — achievable by Day 1 with planning; acceptable security/risk compromise; critical dependency is firewall rule collection and testing |
| **Buyer side** | *Separate to buyer infrastructure* / "extract and go" / "clone and vitiate" / "new build" — typically a **Day 2**, not Day 1, option because buyer security will not allow access before Day 1 | *As-is access* — *"measure of last resort if timeline between Day 0 and Day 1 is extremely short"*; high risk to seller |

Separation approaches (six) [p. 12]: **clone and go**; **clone, vitiate, and go**;
**copy, configure, and load**; **extract and go**; **give and go**; **hybrid**. Appendix A
compresses these to three [p. 501]: **clone, cleanse and go**; **extract and load**;
**new build**.

TSA scope to define — the checklist the DD should anticipate [p. 517–518]: services
provided at each stage; complete description of service including process and
subprocess detail; description of services **not** provided; third-party delivery
dependency; frequency; resources providing the service; **defined end date for every
schedule item**; process to add/delete/change services; ownership at end of TSA
period; review process and issue-resolution path; service metrics; penalties or
incentives; TSA management ownership; financial arrangements; dependencies with
other TSAs; key risks and mitigations.

Typical IT TSA service list [p. 517]: enterprise application support; application
enhancement and development; network services; service management centre; server and
storage hosting; mainframe infrastructure services; backup and recovery;
e-mail/messaging and collaboration; corporate application support; desktop services;
help desk; identity and access management; remote access; voice and video;
telecommunication services; file and print services.

Governing principle for TSA scoping, verbatim [p. 270]: **"What you get today is what
you will get tomorrow, no more but perhaps a little less."** Corollaries: a service
broken pre-Day 1 remains broken post-Day 1; TSAs should not be created for services
not delivered pre-Day 1.

Stranded costs to size [p. 249]: onshore FTE costs; offshore FTE costs; fixed costs;
vendor costs; IT-specific costs; operations-specific costs.

### 6.11 W-INT — Integration Effort, Day 1 Readiness and Synergy Sizing
*Archetype: both. Triggered where integration is intended.*

Day 1 areas with critical IT dependencies [p. 253–254]: finance separation; HR
separation; rebranding; network connectivity; TSA and data segregation; e-mail and
communication.

IT's own Day 1 preparation steps, verbatim [p. 262]: blueprinting and problem
solving; risk review and prioritisation; integration Day 1 planning; Day 1 readiness
checklist; command center and cut-over list.

Synergy sizing method — four sequential steps [p. 13–14]: (1) develop IT cost
baseline (regional and functional, using DD data, benchmarked); (2) conduct top-down
target setting; (3) develop bottom-up synergy commitments; (4) create tracking tools
and processes.

Synergy taxonomy [p. 23–25]: **shared overhead** (eliminate duplicate IS roles;
reduce support costs through standardisation); **economies of scale** (common
technologies/platforms/systems; combined IT procurement); **cross-fertilisation**
(customer database and data mining; groupware/intranets/workflow); **operational
integration** (integrated production, forecasting, logistics; order-entry and
customer-facing systems; data warehouse).

### 6.12 W-PROD — Product and Platform Deep-Dive
*Archetype: product. Triggered where proprietary technology is the revenue asset.*

Sourced dimensions: Exhibit 5.6, reproduced in full at §3.3 [p. 77].

**[EXT]** Structure the deep dive as sub-modules, each with its own evidence:
- **P1 Architecture and scalability** — architecture diagrams, service boundaries,
  data flows, known bottlenecks, capacity headroom, load and growth projections.
- **P2 Code quality and technical debt** — repository access or scan, language/
  framework currency, test coverage, static-analysis output, complexity hotspots,
  documented debt register.
- **P3 Engineering velocity and delivery** — deployment frequency, lead time for
  change, change failure rate, MTTR, sprint/issue data, release history, incident log.
- **P4 SDLC, testing and release practice** — branching model, code review policy,
  CI/CD pipeline, environments, QA approach, rollback capability.
- **P5 Product management and roadmap credibility** — roadmap vs delivered history,
  discovery practice, PMF evidence, usage analytics, churn and expansion by cohort.
- **P6 IP, open source and third-party dependencies** — contributor IP assignment,
  contractor agreements, OSS licence inventory and copyleft exposure, SBOM,
  third-party API and model dependencies with commercial terms.
- **P7 Data and AI capability** — see §4.9.
- **P8 Engineering org and key-person risk** — team shape, seniority mix, attrition,
  bus-factor on critical components, contractor dependence, hiring pipeline.
- **P9 Product security and multi-tenancy** — see W-SEC extension.
- **P10 Infrastructure unit economics** — hosting cost per tenant/customer/
  transaction, gross-margin trajectory, committed-spend agreements.

Note the source's own caution, which applies with force here: product DD is *"the
same [areas] ... but with additional depth of analysis"* [p. 76–77] — do not drop the
enterprise modules because the target is digital-native.

---

## 7. Depth tiers

The book prescribes a **tiered and iterative process** (Exhibit 5.10) [p. 86]:

- **Tier 1** — high-level initial assessment across *all* aspects of the target's IT
  environment. Flags potential issues (risks or opportunities).
- **Tier 2** — a further layer across all aspects (*"which is typical, but not always
  warranted"*), plus **more vigorous effort around the perceived areas of potential
  risk**.
- The methodology repeats, each tier drilling further, *"until the due diligence team
  is familiar with the target's IT environment and fully comprehends each area of
  potential risk and opportunity."*

Rationale, verbatim: *"the sizes of the shaded areas ... represent effort (or expense)
associated with each tier of the assessment. So, using this approach can identify
potential issues at a deeper level with the least amount of exertion."* [p. 86]

**Encodable depth model [EXT, structure only]:**

| Tier | Name | What it means in a scope |
|---|---|---|
| 0 | Not in scope | Explicitly excluded, with the reason stated |
| 1 | Screen | Document review + one question set; findings flagged, not sized |
| 2 | Assess | Document review + management interview + order-of-magnitude sizing |
| 3 | Deep dive | Above + artefact-level analysis (code, config, contracts, cost model) + specialist adviser |

Every workstream in a generated scope carries a tier. Tier 3 on any module must be
justified by a signal, and must be checked against the access level — Tier 3 on
W-PROD requires code access.

---

## 8. Process — plan, conduct, finalise

### 8.1 Planning [p. 79–81]

**Prepare in advance.** *"IT due diligence assessments share many of the same elements
across projects. As a result, the advance preparation of detailed document templates
and question sets is both feasible and beneficial."* Enhance the template library after
each project [p. 79]. — *This sentence is the product thesis of the platform.*

**Pick the right team** [p. 80]:
- **Core team members** — strong general IT knowledge plus understanding of M&A
  process, considerations and approach.
- **Subject matter advisers (SMAs)** — deeper expertise in an IT or industry subject
  area critical to the transaction.
- **Buyer-side IT leadership** — actively and promptly engaged, especially for
  strategic buyers intending to integrate.
- Team members must be prepped for *"extreme responsiveness, precision, and
  flexibility."*
- Caution: *"SMAs may not be familiar with M&A concepts, and this context is important
  in providing an appropriate disposition."*

**Understand the project context** [p. 80–81] — deal type and planned level of
integration affect separation/transition considerations and synergy analysis, so ask
*situation-appropriate* questions.

**Establish expectations up front** — questions to put to the deal team, verbatim
[p. 81]:
- Will the target company plan to be integrated (to some extent) into the buyer's
  organization (or one of its subsidiaries), or will it operate in a stand-alone
  environment?
- What is the transaction timeline, and when will the investment committee require
  the due diligence disposition?
- What is the proposed timeline of the postclose activities?
- What are the preliminary expectations regarding the integration or rationalization
  of target IT staff, applications, and infrastructure?

**Use benchmarks — with care** [p. 81].

### 8.2 Conducting [p. 82–86]

**Initial research** before the data room is available [p. 82]: company website
(including investor relations and annual reporting); **IT job listings** (*"these may
give insight into the technologies used at the company"*); news and analyst research;
social networking and media sites.

**Develop a concise data request** [p. 82–83]. Initial data request contents,
verbatim [p. 83]:
- Provide information on the IT organization, including outsourced vendor
  relationships.
- Provide a description of the IT strategy and any documented IT policies and
  processes (data retention, performance monitoring, risk/control, etc.).
- Provide an inventory of software applications, including primary business
  functionality, version and licenses, customization, platform/architecture, level of
  scalability and redundancy, and hosting and support arrangements.
- Provide an application architecture diagram showing the interfaces between the
  applications (and modules) in use.
- Provide a summary-level inventory of infrastructure components (servers,
  workstations, networking, etc.) showing location, age, current utilization, and
  expected replacement dates.
- Provide the company's disaster recovery plan.

Rules for data requests [p. 83]: limit items to what has not already been asked or
provided; supplemental requests must be targeted and specific; be sensitive that a
small number of target staff are "over the fence" and cannot ask questions internally
without arousing suspicion; **do not go back repeatedly** — *"the seller can become
overwhelmed and even ultimately unresponsive"*; escalate non-response to the deal
team. And the diagnostic: *"a lack of data could also be a sign that the IT
environment is not very mature."*

**Review the data room — including the hidden folders** [p. 83–84]. Sources of hidden
IT information (Exhibit 5.9, verbatim):

| Folder | IT information found there |
|---|---|
| Finance | IT budgets; historical IT expenses; fixed asset inventory; audit controls |
| HR | IT organization charts; target employee count; employee locations; IT CVs; IT job responsibilities; employee roster (often with salary) |
| Legal | IT contracts (applications, infrastructure, services, etc.); intellectual property inventory |
| Real Estate | Data center locations |
| Other | Confidential information memorandum; management presentations; business process narratives |

Also: check frequently for updates (*"One day the team may receive 20 documents; the
next day, nothing"*); use data-room alerting if available; capture initial findings
and questions in a draft summary document that becomes the base of the final report
[p. 84].

**Interviews** [p. 84–85]: request access to the highest-ranking IT officer and any
others who can explain the environment; prepare questions in advance; ask focused
rather than leading questions — the book's own example is to replace *"Does your
department deliver value to the business?"* with *"Have you had any challenges meeting
business requirements or know of challenges that may develop in the near future?"*;
prioritise questions because time with management is limited; avoid repeating
questions across sessions.

In-person vs remote — decision factors, verbatim [p. 85]: availability of due
diligence team and target personnel; size of the project; budgetary constraints; any
discovered risks that require additional tactile/visual due diligence, such as a
complicated proprietary tool that requires whiteboarding; an IT data center review.

On-site confidentiality rules, verbatim [p. 85]: having a cover story when arriving;
not talking about the deal (or any related information) in shared corridors or
elevators; not wearing anything with a buyer's logo.

**Apply the tiered process** — see §7.

### 8.3 Finalising [p. 86–87]

- Compile from interviews, adviser input, data room, and cost estimation; assess the
  **magnitude** of significant risks and opportunities.
- Understand what the deal team expects and prioritise findings accordingly — *"It is
  not uncommon for these requirements to change—one day the deal team may want just a
  high-level summary, and the next day they may want detailed information."*
- Distinguish **significant one-time costs affecting deal valuation** from costs
  affecting the post-merger environment (one-time and recurring).
- Provide **order-of-magnitude ranges**, never point estimates. Sources for cost
  analysis: core team experience, adviser experience, vendor websites or discussions,
  benchmarks, other internet sources.
- **Document assumptions** and understand how estimates change if assumptions fail.
- By deal type: full purchase → costs to mitigate risks/opportunities found;
  carve-out → **also** the cost of replacing resources, systems and services performed
  by the parent that are not accompanying the transaction; JV or any integration →
  develop a preliminary IT integration approach aligned to the future business
  strategy and estimate incremental one-time/recurring costs plus rationalisable costs
  (synergies).
- Include **open matters** requiring further investigation.

---

## 9. Rules of thumb, benchmarks and thresholds

Every figure below is from the source, with its citation. **Treat them as anchors for
a practitioner's judgement, not as computed outputs.** Several are dated.

| # | Rule | Cite |
|---|---|---|
| R1 | ~80% of DD effort on people/process/spending + applications + infrastructure; ~20% situation-specific | p. 72 |
| R2 | ERP integration ≈ **80% of total integration costs**; other applications can run a parallel track | p. 197 |
| R3 | Applications rationalisation savings tiers: **20–30%** (standard architecture, IT governance, shared services), **10–20%** (app rationalisation, resourcing strategy, hardware utilisation, demand management), **5–10%** (licence optimisation, project rationalisation, application retirement, storage optimisation, strategic sourcing) | p. 181 |
| R4 | Blanket supplier renegotiation ("dialing for dollars") yields ≈ **5–10%**, supplier- and category-dependent; can backfire with large IT suppliers | p. 201 |
| R5 | **80/20 supplier rule** — 80% of supplier spend sits with 20% of suppliers; segment high/medium/low | p. 209 |
| R6 | Critical-supplier shortlist rarely exceeds **~50 suppliers**, even at large multinationals | p. 213 |
| R7 | Suppliers need lead time of **up to six months** to grant required contractual rights | p. 222, 474 |
| R8 | Right-to-use clauses may permit continued use **up to a year** post-close | p. 102 |
| R9 | TSA pricing benchmark: **cost plus 10%** (percentage adjustable); minimum fee protects against Day 1+1 cancellation | p. 233 |
| R10 | TSA invoice dispute threshold: **<10%** resolved between functional leads; **>10%** becomes a formal dispute at the governing body. Payment **net 30** | p. 244, 242 |
| R11 | TSA pricing-method preference order (easy → hard): **Current P&L → Market Rates → Head Count Proxy → Build from Scratch** | p. 233 |
| R12 | Governance escalation split: **80%** day-to-day at work-stream level, **15%** cross-work-stream at the operating committee, **<1%** strategic at steering committee | p. 239 |
| R13 | Multinational firewall build and testing: **four to six months**, country by country | p. 259 |
| R14 | Blueprinting process: **six to eight weeks** to develop comprehensive service and asset inventories | p. 469 |
| R15 | Synergy baseline build-out: a **six-week** sequence (recommend metrics → definition → source and frequency → baseline established → process test → first review) | p. 126 |
| R16 | Deal-close speed: small carve-outs can close **~30 days** after announcement; deals **>$1B average 115 days** to close **[DATED — 2008 study]** | p. 265 |
| R17 | Financial buyers' typical investment horizon: **four to seven years** | p. 496 |
| R18 | Integration test cycles: **two full rounds**, each **3–4 weeks** (up to **6 weeks** for high-risk/development scope); round 1 without full security, round 2 with | p. 441, 447 |
| R19 | Stress/volume testing to **125–150%** of typical volumes | p. 442 |
| R20 | **At least two mock cut-overs** before production cut-over | p. 443 |
| R21 | End-to-end test scenarios: typically **10 to 30**, depending on scope | p. 445 |
| R22 | M&A outcomes **[DATED — Deloitte studies of 2000 and 2008]**: ~60% of acquisitions fail to achieve stated strategic objectives in the planned time frame; announced synergies not achieved in ~70% of transactions; productivity can fall ~50% in the first 4–8 months post-close; only 23% of acquirers earn their cost of capital; ~47% of executives leave in year 1, 75% by year 3 | p. 451 |
| R23 | Interim blueprint milestone lands after **Q1 or Q2** post-close; most strategic/operational change in place by **six months** | p. 187, 50 |
| R24 | Contract programme milestones: **"Day 1 Ready"** (all rights secured) and **"Day 1 Complete"** | p. 216–217 |

---

## 10. Tying DD to what comes next

The source insists DD outputs are inputs to post-transaction planning, and that
*"all assumptions and crucial decisions made during the due diligence phase should be
revisited and validated"* post-signing, with the DD team carried into the mapping
exercise [p. 88].

Opportunities to leverage DD outputs (Exhibit 5.11, condensed but faithful) [p. 89–90]:

**Strategy, process and controls** — identify alternative IT processes/strategy for
NewCo; identify the pool of controls (regulatory, vulnerability, audit) needing
implementation; identify leading practices the buyer could adopt; identify critical IT
support activities to prioritise; identify existing communication channels to
continue. *Carve-out:* how separation impacts IT and business teams. *JV:* level of
post-transaction reporting required.

**Organisation, vendors and contracts** — need to hire vs pool of retainable staff;
high-level plan from current to end-state operating model; new vs retained vendors;
pool of usable contracts; contracts needing renegotiation, with termination or
transfer costs. *Carve-out:* critical resources and a retention plan. *JV and
carve-out:* preferred options for required contracts, services and costs.

**Budgeting and projects** — order of magnitude of one-time and recurring integration
costs; projects continuing after close; new projects to launch after close.

**Applications** — pool of applications for NewCo (target's vs buyer's); new licences
required; applications needing new or existing interfaces; systems and data
integrable into buyer systems. *Carve-out:* systems and data needing separation from
the parent; potential data separation issues.

**Infrastructure** — new data centre vs existing; underlying infrastructure needed to
support target applications; telecommunications equipment; NewCo bandwidth
requirements; workstations, phones; systems integrable into the buyer's. *Carve-out:*
what must be separated from the parent.

---

## 11. Failure modes the scope should defend against

From Ch. 26, structured as the book presents them [p. 453–455]:

**1. Unclear scope, not aligned with business**
- *Unclear IT scope / no agreed integration or divestiture approach* → timing,
  resource and cost issues. Fix: set and articulate IT M&A strategy up front (guiding
  principles, non-negotiables); establish governance and escalation early; appoint
  strong IT leads; run an early scoping workshop with documented, agreed outputs.
- *Unaligned business and IT requirements* → inefficiency and Day 1/Day 2 continuity
  issues. Fix: documented, vetted, agreed requirements; joint kickoff; periodic joint
  design reviews; monitor cross-functional dependencies.

**2. Trying to do too much in too short a period**
- *Complex Day 1 scope.* Fix: leverage one organisation's existing solutions; control
  the tendency to reengineer; focus only on Day 1 must-haves.
- *Commitment to overly aggressive synergies.* Fix: top-down IT synergy analysis;
  understand leadership's commitments; validate with technical experts; negotiate to
  achievable levels; educate leadership that IT synergies have long lead times (data
  centre consolidation, help desk consolidation, application consolidation/retirement).

**3. Lack of, or inaccurate, communication**
- *Information erroneously shared* → legal/regulatory risk. Fix: legal counsel early
  on what can be shared pre-close; **clean team** approach where needed.
- *Disconnect between IT and overall communications.* Fix: dedicated communications
  team; shared tools and published timeline aligned to the business.

**4. Lack of resource and budget**
- *Overstretched IT team members doing double duty.* Fix: document IT resource needs
  early; prioritise; off-load regular work; hire contractors; shut down in-flight
  projects.
- *Lack of clarity on IT budgeting* — IT is often one of the largest cost drivers.
  Fix: involve financial analysts and project controllers early.

Ten critical success factors, verbatim headings [p. 455–457]: **Experience;
Coordination; Leadership; Clear intent; Perseverance; Accountability; Leverage;
Focus; Decisiveness; Communications** — the last described as possibly the most
important: *"Employee uncertainty can be the silent killer of successful merger
integration."*

M&A IT key success factors [p. 459–461]: **Involve IT Early; Facilitate IT Readiness;
Control the Integration; Minimize Risk; Manage Cost to Achieve; Enable Key Stakeholder
Engagement** (staff M&A positions with paired IT + business individuals — *"double
boxing"*); **Focus on Talent Retention**.

The most directly applicable best practice for this platform, verbatim [p. 469–470]:

> **"Assess Transaction Characteristics and Context Early in the Process to Establish
> a Proper Understanding of Due Diligence Scope and Priorities.** Proper understanding
> of key transaction characteristics, such as deal type, buyer type, IT landscape, and
> post-merger objectives, is critical to correctly evaluating due diligence project
> requirements (e.g., key areas of investigation, level of effort, resource needs, and
> mix)."
>
> Do: Conduct this analysis as early as possible. Confirm with the deal team the
> business rationale, transaction objectives, and diligence priorities. Pick the right
> IT team based on transaction context and priorities. **Tailor due diligence approach,
> scope, and standard artifacts to align with transaction context and due diligence
> priorities.**
>
> Don't: **"Don't simply apply a predefined standard due diligence approach and scope.
> You should adapt to the specific transaction context."**

That paragraph is the product specification.

---

## 12. What the platform must be, according to the source

Appendix A describes an **M&A IT playbook**: *"a prescriptive guide documenting the
tasks needed to effectively and efficiently execute an IT integration or divesture
based on the parameters of the deal"*, answering [p. 493]:

- Who does it?
- When does it start?
- What are the dependencies?
- How long might it take (if appropriate)?

Playbook themes the source insists on [p. 494]:
- M&A is not a stand-alone project — it is a subset of the overall business effort.
- Acquisitions and divestitures are projects and should use standard project
  management methods (approval gates, issue resolution, resource balancing,
  acceptance testing).
- *"Playbooks can only provide guidance, ideas, and suggestions. A playbook should not
  be a substitute for experience, critical thinking, and common sense."*
- *"Every deal is different: all plans, templates, tools, and the like should be
  tailored to the circumstances, and the playbook should continually evolve."*
- People issues can be the most challenging — the playbook must address them.
- **"M&A playbooks should be alive"** — a living document that evolves with each deal
  [p. 494].

**Tools and templates a playbook should carry** (verbatim) [p. 503] — read this as the
platform's product roadmap:
- Generic work plans for executing IT due diligence, IT integration or divestiture
  planning, IT integration or divestiture transition.
- **IT due diligence checklist.**
- **IT security questionnaire.**
- **Tool to model cost estimates during due diligence.**
- **Synergy tracking tool.**
- **IT TSA checklist.**
- **IT integration and divestiture Day 1 readiness checklists.**
- **List of lessons learned aggregated from previous M&A deals and updated after each
  new transaction.**

Sample material to accompany it [p. 503]: sample due diligence report; sample
integration/divestiture kickoff deck; sample project plans; sample integration and
divestiture test plans; sample communication plan; sample Day 1 user experience
document; sample cut-over plans.

**Implication for this product:** the scope-of-work generator is step one of a
playbook engine, not a standalone feature. Design the workstream library so the same
modules can later emit a work plan, a data request, an interview guide, a cost model
and a Day 1 checklist — not just prose.

---

## 13. Intake → what the engine needs

Fields already specified in `docs/phases/PHASE1_PLAN.md` §3 are marked *(have)*. Fields the scope
engine needs that Phase 1 does **not** yet capture are marked **(ADD)** and must be
added to the intake before the engine can run.

### 13.1 Transaction shape
| Field | Values | Why it matters | Cite |
|---|---|---|---|
| `deal_type` **(ADD)** | full_acquisition · carve_out · joint_venture · merger_of_equals · divestiture_sell_side · minority_growth | Primary complexity and scope driver | p. 71, 78 |
| `perspective` **(ADD)** | buy_side · sell_side | Inverts objectives and evidence availability | p. 72, 152 |
| `investment_type` *(have)* | strategic · financial | Sets the lens, not the areas | p. 78–79 |
| `stake` *(have)* | majority · minority | Access depth, control-oriented workstreams | — |
| `post_close_intent` *(have)* | standalone · integrate · carve_out · merge · undecided | Selects integration model | p. 48, 10–11 |
| `integration_model` **(ADD)** | consolidation · combination · transformation · preservation · undecided | Directly sets application/infrastructure scope | p. 10–11, 498 |
| `carve_out_or_tsa` *(have)* | boolean | Triggers W-SEP | p. 71 |
| `relative_size` **(ADD)** | target_much_smaller · comparable · target_larger | Time required; end-state platform question | p. 71, 497 |
| `hold_period_years` *(have)* | <3 · 3–5 · 5–7 · 7+ | Horizon the architecture must survive | p. 496 |

### 13.2 Target technology shape
| Field | Values | Why | Cite |
|---|---|---|---|
| `digital_maturity` *(have)* | digital_native · digitally_enabled · traditional | Strongest single archetype signal | p. 76–77 |
| ~~`tech_is_product`~~ **(REMOVED 2026-08-31)** | ~~yes · partly · no~~ | Redundant with `dd_type_preference`, which the user declares in Diligence Objectives. A1 and M6 now read that field. See docs/PROJECT_LOG.md | p. 76–77 |
| `build_vs_buy` *(have)* | in_house · balanced · cots | Weights custom vs commercial application modules | p. 75 |
| `core_systems` *(have)* | SAP, Oracle, Dynamics, Salesforce, NetSuite, Workday, ServiceNow, custom, other | ERP-heavy estate → enterprise weighting; ERP ≈ 80% of integration cost | p. 197 |
| `hosting_model` *(have)* | public_cloud · hybrid · on_prem · colo · unknown | Infrastructure depth; DR and data-centre modules | p. 76, 92 |
| `it_landscape_complexity` **(ADD)** | low · medium · high | Explicit complexity driver in Exhibit 5.1 | p. 71 |
| `engineering_share_pct` *(have)* | number | Product vs enterprise weighting | — |
| `ai_ml_dependence` *(have)* | none · experimental · embedded · core | Triggers AI workstream **[EXT]** | — |
| `data_sensitivity` *(have)* | none · PII · PHI · PCI · financial · gov | Makes W-SEC/W-DATA mandatory | p. 73 |
| `compliance_regimes` *(have)* | SOC 2, ISO 27001, HIPAA, PCI-DSS, GDPR, DPDP, FedRAMP, none | Compliance depth | p. 288–289 |
| `shared_with_parent` **(ADD)** | free text / multi-select of shared services | Carve-out scoping — the single most under-asked question | p. 78 |
| `ma_history` *(have)* | free text | Unintegrated estates from prior deals | — |

### 13.3 Engagement constraints
| Field | Values | Why | Cite |
|---|---|---|---|
| `deal_stage` *(have)* | pre_IOI · IOI · confirmatory · exclusivity · post_signing | Sets whether the scope is red-flag or confirmatory | p. 71 |
| `access_level` *(have)* | full · data_room_plus_mgmt · data_room_only · public_only | Hard gate on achievable depth | **[EXT]**, p. 70 |
| `code_access` *(have)* | full_repo · read_only_sample · scan_only · none | Hard gate on W-PROD Tier 3 | **[EXT]** |
| `timeline_weeks` *(have)* | number | Depth budget | p. 71 |
| `management_access` **(ADD)** | none · CIO_only · CIO_plus_team · full | Determines interview plan feasibility | p. 84 |
| `deliverable_format` *(have)* | red_flag · full_report · IC_input · 100_day · cost_model | Shapes output sections | **[EXT]** |
| `dd_objectives` *(have)* | multi-select | Explicit user priorities beat inferred ones | p. 81 |
| `dd_type_preference` *(have)* | auto · enterprise · product · blended (+ reason) | Human override, always recorded | **[EXT]** |
| `budget_band` *(have)* | band | Effort envelope | p. 85 |

**Rule:** the engine must never require a field the user has not been asked for. Any
`(ADD)` field ships as part of the same change that ships the engine.

---

## 14. Scope of work — required output structure

A generated SOW must contain, at minimum:

1. **Engagement header** — target, investor, deal type, stage, timeline, access level,
   deliverable format, date, version, generator.
2. **Classification** — `dd_type` (enterprise | product | blended), `dd_mix` (0–100),
   **confidence**, and the **signals** that produced it, each traceable to an intake
   field. Plus any human override and its recorded reason.
3. **Objectives** — restated against the four sourced DD objectives (§1.1), tailored
   to the stated `dd_objectives` and the deal thesis.
4. **Workstreams** — for each selected module:
   - id, name, archetype weighting, **depth tier** and the reason for that tier;
   - objective (one paragraph, tailored to this target's line of business);
   - key questions (drawn from §6, tailored — never generic);
   - evidence / data requests (specific documents, mapped to the data-room folder
     they are likely to live in, per Exhibit 5.9);
   - interview targets and topics;
   - common findings to test for;
   - indicative effort band and dependencies on other workstreams;
   - explicit **out of scope** statement where access constrains it.
5. **Sequencing** — a **broad pass** then a **deep dive**, mapped against the available
   weeks and the deal stage; the iterative model of §7 made concrete.
   **[EXT — practice vocabulary, confirmed with the engagement partner 2026-08-31]** The
   two passes are named as the practice names them, and the handoff between them is
   explicit: the broad pass reviews every area in scope at structural level and its
   *deliverable is the prioritised areas of focus*; the deep dive then works only on
   those. A plan that lists the passes without naming what moves between them reads as
   two unrelated activities. The Tier 1/2/3 depth model above is unchanged and still
   governs individual areas — only the phase vocabulary follows the two-pass framing.
6. **Cost-estimation plan** — which one-time and recurring cost lines this scope will
   produce, and the assumptions register that will accompany them (§8.3).
7. **Team shape** — core team + named SMA specialisms required (§8.1).
8. **Risks to the diligence itself** — access gaps, timeline risk, information
   asymmetry, dependence on management representations.
9. **Explicit exclusions** — with reasons. A scope that does not say what it excludes
   is not a scope.
10. **Provenance footer** — every rule that fired, so a reviewer can audit why a
    workstream is present at the tier it is at.

**Versioning:** regenerating produces a new version; prior versions are never
destroyed. The book's own reason: deal-team requirements change day to day [p. 87].

---

## 15. Encodable decision rules

Candidate rule set for the engine. Each rule has an id, a condition, an effect and a
citation. **These are drafting inputs, not final logic** — weights need calibration
against real engagements.

### 15.1 Archetype mix
| Rule | Condition | Effect | Cite |
|---|---|---|---|
| A1 | `dd_type_preference = Product Tech DD` *(re-sourced 2026-08-31; was `tech_is_product = yes`)* | mix += 35 | p. 76–77 |
| A2 | `digital_maturity = digital_native` | mix += 25 | p. 76–77 |
| A3 | `digital_maturity = traditional` | mix −= 20 | p. 72 |
| A4 | `build_vs_buy = cots` OR ERP in `core_systems` | mix −= 20 | p. 197 |
| A5 | `build_vs_buy = in_house` | mix += 15 | p. 75 |
| A6 | `engineering_share_pct >= 30` | mix += 10 | **[EXT]** |
| A7 | `investor_type ∈ {VC, growth_equity}` | mix += 10 | p. 496 |
| A8 | `deal_type = carve_out` | mix −= 10, force W-SEP | p. 71, 78 |
| A9 | `post_close_intent = integrate` AND `investment_type = strategic` | mix −= 10, force W-INT | p. 78 |
| A10 | `hosting_model = on_prem` | mix −= 10 | p. 92 |
| A11 | `ai_ml_dependence ∈ {embedded, core}` | mix += 10, open AI module | **[EXT]** |

Clamp to 0–100. Bands: 0–34 enterprise · 35–65 blended · 66–100 product. Confidence
falls when few rules fire or when rules conflict strongly.

### 15.2 Mandatory workstreams (cannot be dropped by mix)
| Rule | Condition | Effect | Cite |
|---|---|---|---|
| M1 | always | W-OPS, W-APP, W-INFRA, W-SPEND at Tier ≥ 1 | p. 72 |
| M2 | `data_sensitivity ≠ none` | W-SEC and W-DATA at Tier ≥ 2 | p. 73 |
| M3 | `compliance_regimes` non-empty | W-PROC at Tier ≥ 2 | p. 288–289 |
| M4 | `deal_type = carve_out` OR `carve_out_or_tsa = true` | W-SEP at Tier ≥ 2; add licence-transferability and interface-disentanglement questions | p. 78 |
| M5 | `post_close_intent = integrate` | W-INT at Tier ≥ 2, incl. scalability assessment of the receiving platform | p. 71 |
| M6 | `dd_type_preference ∈ {Product Tech DD, Blended}` *(re-sourced 2026-08-31; was `tech_is_product ∈ {yes, partly}`)* | W-PROD at Tier ≥ 2 | p. 76–77 |
| M7 | any contract transfer implied (`deal_type ≠ minority_growth`) | W-VEN at Tier ≥ 2; flag the six-month supplier lead time | p. 222 |

### 15.3 Depth and access gates
| Rule | Condition | Effect | Cite |
|---|---|---|---|
| D1 | `code_access = none` | W-PROD capped at Tier 2; state the limitation explicitly in the scope | **[EXT]** |
| D2 | `access_level = public_only` | all modules capped at Tier 1; scope becomes a screen, not an assessment | p. 70 |
| D3 | `management_access = none` | remove interview-dependent evidence; substitute document-only questions; raise diligence-risk section | p. 84 |
| D4 | `timeline_weeks <= 3` | Tier 1 across all; Tier 3 only on the single highest-signal module. *"Quickly need to assess what is most important to deal team"* | p. 71 |
| D5 | `deal_stage ∈ {pre_IOI, IOI}` | red-flag posture: breadth over depth | p. 71 |
| D6 | `deal_stage ∈ {confirmatory, exclusivity}` | confirmatory posture: depth on flagged areas, cost model required | p. 86 |
| D7 | `investment_type = financial` | Tier 1 sweep across all domains, then Tier 3 only on significant risk/cost areas | p. 79 |
| D8 | `investment_type = strategic` AND integrating | Tier 2+ on **every** domain (organisation, processes, applications, infrastructure) plus synergy identification | p. 78 |
| D9 | `it_landscape_complexity = high` | +1 tier on W-APP and W-INFRA; flag need for SMAs / external resources | p. 71 |
| D10 | `relative_size = comparable` or `target_larger` | +1 tier on W-APP; end-state platform question becomes explicit | p. 71 |

### 15.4 Content injection
| Rule | Condition | Effect | Cite |
|---|---|---|---|
| C1 | ERP present | inject: ERP ≈ 80% of integration cost; treat ERP disposition as its own decision | p. 197 |
| C2 | `hosting_model ∈ {on_prem, colo}` AND cross-border | inject circuit/firewall lead-time warning (4–6 months) | p. 93, 259 |
| C3 | `deal_type = carve_out` | inject the five carve-out investigation questions verbatim | p. 78 |
| C4 | `deal_type = joint_venture` | inject JV responsibility-split and post-transaction reporting questions | p. 78 |
| C5 | always | inject the hidden-data-room-folder map (Exhibit 5.9) into evidence requests | p. 84 |
| C6 | always | inject the initial data request (six items) as the opening evidence ask | p. 83 |
| C7 | `carve_out_or_tsa = true` | inject TSA checklist items and the *"what you get today"* principle | p. 517, 270 |
| C8 | `ai_ml_dependence ∈ {embedded, core}` | inject AI/model governance questions **[EXT]** | — |
| C9 | always | cost estimates presented as order-of-magnitude ranges with an assumptions register | p. 87 |

### 15.5 Guardrails
- **G1 — never emit a generic scope.** Every workstream objective must reference the
  target's line of business. The source's own "don't": *"Don't simply apply a
  predefined standard due diligence approach and scope."* [p. 470]
- **G2 — never promise depth the access level cannot deliver.** Check D1–D3 before
  emitting.
- **G3 — never drop the 80% core** to make room for the 20% tailoring [p. 72].
- **G4 — always state exclusions and open matters** [p. 87].
- **G5 — always show the rule provenance.** A scope a reviewer cannot audit is a
  scope a reviewer cannot defend.
- **G6 — the human overrides the engine.** `dd_type_preference` and per-workstream
  tier edits always win, and the override reason is stored.

---

## 16. Handling the source's age

The book is from 2013 and is Deloitte-authored. Three consequences:

1. **[DATED] content to modernise, not delete.** The cloud chapter's suitability
   matrix, workload-readiness lists (ERP listed as "not ready for cloud"), PCI DSS
   v2.0, SSAE 16, and the text-mining accuracy caveat all reflect 2013. Keep the
   *structure* (a suitability rubric, a workload triage, a controls mapping) and
   refresh the *values*.
2. **[EXT] gaps the book simply does not cover.** SaaS-native and multi-tenant
   architecture; DevOps/DORA delivery metrics; open-source licence hygiene and SBOM;
   GDPR/DPDP-era privacy; cloud FinOps and unit economics; AI/ML as an asset and a
   risk; product-led growth and product analytics as diligence evidence; modern
   security frameworks (SOC 2 Type II, NIST CSF, CIS). All of these belong in the
   workstream library and must be labelled `[EXT]` in the data so a reviewer can see
   what is sourced and what is not.
3. **Single-source risk.** One publisher, one firm's house view, one era. The
   workstream library schema must carry a `source` field per module and per question
   so a second source (a different firm's methodology, the user's own house
   standards, later editions) can be layered in without rewriting the engine.

**Rule for the platform:** everything the engine emits carries provenance. Sourced
content cites the book. Extended content is labelled as practice. Nothing is presented
as authority it does not have.

---

## 17. Glossary

| Term | Meaning |
|---|---|
| **Day 0** | Deal signed / announced; regulatory and shareholder approval period begins [p. 5] |
| **Day 1** | Financial close; buyer assumes control; execution begins [p. 5, 253] |
| **Day 2** | Full separation; TSAs terminated [p. 14] |
| **TSA** | Transition Services Agreement — seller continues providing services to the buyer post-close for a fee and defined term [p. 226] |
| **Reverse TSA** | Buyer provides services back to the seller [p. 266] |
| **Clean team / clean room** | Sequestered specialists permitted to access restricted information before deal approval [p. 7, 482] |
| **Stranded cost** | Retained cost no longer needed after a disposal [p. 206, 249] |
| **Dis-synergy** | Unit-cost increase caused by the transaction (e.g. losing a volume discount tier) [p. 206] |
| **Cost to achieve** | One-time cost of realising a synergy [p. 119] |
| **Business intent** | How the seller's business wishes to hand a third-party product/service to the buyer [p. 207] |
| **Blueprint** | End-state and Day 1 target-state design, worked backwards from the end state [p. 10] |
| **Adopt and go** | Quickly select the process/system/policy best suiting the combined company from existing capabilities [p. 43] |
| **Double boxing** | Pairing an IT and a business individual in each key M&A role [p. 461] |
| **SMA** | Subject matter adviser — deeper expertise supplementing the core DD team [p. 80] |
