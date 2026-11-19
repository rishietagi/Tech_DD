# Tech DD Platform — partner cheat sheet

Presenter's notes. The workflow end to end, the logic behind every step, the numbers worth
quoting, and straight answers to what a partner will ask. Demo engagement: **Project Kiln**
(carve-out of an industrial distributor; enterprise DD).

---

## 1. The pitch in 30 seconds

> A technology due diligence platform that takes a deal from intake to a draft report.
> **Rules decide; the analyst judges; AI only writes.** The scope, the request list, the
> scores and the gaps are all produced by explicit, cited rules — so every number traces to a
> reason. The analyst records evidence and judgement. An AI model, when switched on, only
> polishes wording and is checked after every call. Everything the client sees is editable
> before it is exported.

**The one idea behind it:** the scope of a tech DD is not generic. It is a function of
(a) how central technology is to the target, (b) the investor's thesis, and (c) the deal
structure. The platform makes that derivation explicit, auditable and overridable.

---

## 2. The workflow, start to end

| # | Step (screen) | The analyst does | The platform does | Output |
|---|---|---|---|---|
| 1 | **Intake** (6 steps) | Captures deal context, rationale, structure, target, technology profile, objectives | Autosaves; classifies the deal live | Filed engagement |
| 2 | **Scope of work** | Reviews, overrides any area, edits wording | Fires 37 encoded rules → product/enterprise mix → opens areas at a depth | Scope deck (PPTX) |
| 3 | **Company research** | Runs it, or writes it by hand | Grounded web search, cited, refuses rather than invents | 8-section business brief |
| 4 | **Information requests** | Edits, adds, sends the workbook; uploads replies | Seeds every request from the scope; ranks priority; reads the shared drive | IRL workbook (Excel) + tracking |
| 5 | **Templates** (same page) | Sends templates; target fills them | Round-trips applications, data domains, infrastructure platforms, IT team, contracts, **projects**, **cyber tools**, **IT financials** | Structured facts from the target |
| 6 | **Assess** (six tabs) | Answers questionnaires with remarks; triages projects | Scores deterministically; raises **findings by theme** | Process, application, data & infrastructure, team & governance, strategy & projects, IT budget |
| 7 | **Report** | Reviews, edits, sets risk, fills investment | One row per finding, grouped by diligence area, in the KPMG report shape | Draft report (PPTX) |

Each module is a versioned record. Regenerating creates a new version, and the old versions are kept.

---

## 3. The logic behind each step

### Step 1–2: Intake → scope of work

- **Source of truth:** `DD_master.md`, distilled from Roehl-Anderson, *M&A Information
  Technology Best Practices* (Wiley, 2013, a Deloitte practitioner volume), plus the house
  scope-of-work voice transcribed from the KPMG SOW deck. Content the book does not support is
  marked **[EXT]** (modern practice we added: cloud, DORA, open-source licensing, AI/ML).
- **37 rules** (26 active, 10 dormant, 1 disabled). Each one fires on intake answers, and the
  signals it produces carry the rule id and a page citation.
- **Product vs enterprise mix:** start at **50**, add each rule's delta, damp it by **0.55**,
  and clamp to 0–100. The bands are **Enterprise 0–34 · Blended 35–65 · Product 66–100**.
  A declared preference overrides the band, but the computed value stays visible.
- **Confidence** falls when few rules fired, when strong rules pull in opposite directions,
  or when an input is unknown.
- **Depth tiers:** 0 Not in scope · **1 Screen · 2 Assess · 3 Deep dive.**
  - **Access caps:** public-information-only work is capped at Screen. Exploratory and bid
    stages are red-flag screens. Exclusivity is confirmatory.
  - **Effort check:** roughly 1.5 / 4 / 10 person-days per tier, against about 15 person-days
    per week. The lowest-signal rows step down if the timeline can't carry the scope, and
    every step-down writes its reason on the row.
- **The two decks:**
  - **Enterprise** has 9 rows: Applications, Strategy and Roadmap, Organisation and
    Governance, Infrastructure, IT Financials, Projects, SDLC, Emerging Technologies,
    Contracts.
  - **Product** has 12 rows: the 10 KPMG objectives, plus Product Financials and AI Readiness.
- **House rules, enforced in code:**
  - The deck never names the target or the investor.
  - Bullets are verb-led and abbreviations are expanded.
  - Sequencing, cost and team stay **XXX** until the team fills them in.
- **Scope boundaries, enforced in code:**
  - IT financials means the **budgeting process, never a cost model**.
  - We review **contracts and their expiry**; we never scope TSAs.

### Step 3: Company research
- Grounded Gemini web search, then a **second pass that attributes sources**. Source ids
  only exist after the answer is written, so the model cannot cite a source it never
  retrieved.
- **The brief has eight sections:** summary, what they do, how they make money, customers and
  markets, sector, competitive position, the visible technology stack, and implications.
- **A section the sources don't support is left empty, not padded.**
- **The technology section has the strictest rule:** a technology is named only where a source
  names it *for this company*.
- **Feeding the IRL:** the brief shapes the request list's wording, but the
  "implications" section is deliberately withheld, because it is the model's opinion.
- **With the AI off,** research is written by hand. There is no rules version of facts about a
  company.

### Step 4: Information requests
- **Every request traces to a scope area:** each opened row's evidence list seeds a request.
  The list asks for **documents and questions** (DD_master §6 has both), grouped by the
  scope's own headings, with the owning function as a column.
- **Priority is deterministic, with a stated reason:**
  - **Critical:** evidence on security, process or data (where gaps break deals).
  - **High:** deep-dive areas, and legal or finance requests.
  - **Medium:** assessed areas.
  - **Low:** screened areas.
- **Excel round-trip:** a hidden request ID keeps matching exact even if the client reorders
  or rewords rows. A blank cell never erases an answer. Unmatched rows are reported back.
- **Shared-drive scan:**
  - Every file is tokenised and shortlisted against each document request by deterministic
    matching, with synonyms (org/organisation, DR, BCP…).
  - The model judges each shortlisted file: document type, received in full or in part, and
    **follow-up questions** that close the gap.
  - **It never overwrites a status a person set.**
  - With the AI off, it matches on filenames only, and the screen says so.

### Step 5: Templates (on the Information requests page)
- **Seven templates plus the financials sheet:** applications, data domains, infrastructure
  platforms, IT team, IT contracts, **in-flight IT projects** (allocated capex, capex used,
  % complete, dates, vendor) and a **cyber tools checklist** (SIEM, PAM, MFA, backup, DLP,
  MDM…), plus an **IT financials** sheet (budget and actual by line and year). They travel as
  extra sheets in the IRL workbook; an upload fills them in and **never clears a value**.
- **The target supplies facts, never scores.** A target asked to rate its own systems rates
  them well, so the fit, criticality and maturity questions belong to the analyst. A test
  bans scoring fields from the templates.
- The application fields mirror the source's own request, near-verbatim on p. 83:
  functionality, version and licences, customisation, platform, scalability and redundancy,
  hosting and support.

### Step 6: Assess — six tabs

**How every finding is made (Phase 8).** A due diligence reports what moves the value of
the deal, not a defect list per system. Rules still look at every application, platform,
role and project, but what they find is an **observation** — evidence. Observations are
grouped into **themes**, and the theme is the finding: a headline ("Critical applications
facing end-of-support risks"), the evidence, an implication, a **deal-impact lens** (one-off
investment · run-rate cost · risk to the plan · continuity · compliance · integration — the
book's p. 70 definition of what a DD must find), a "Target should…" action and a severity.
- **Severity rule, everywhere:** High = threatens continuity of a critical operation,
  regulatory exposure, or an **unfunded investment the plan depends on**; Medium = constrains
  the plan or adds cost; Low = an improvement.
- **Information not provided is a data limitation, not a finding.**
- **The target supplies facts; the analyst supplies judgement.** No template asks the target
  to rate itself — a test bans it.

**The shared maturity ladder (0–5):** Manual · Recorded · Standardised · Integrated ·
Automated · Optimised. **Index:** weighted mean × 20 → 0–100. **Bands:** ≤20 · ≤40 · ≤60 ·
≤80 · above (automation words for process and application indices; Initial · Developing ·
Defined · Managed · Optimised for the maturity indices).

**(a) Business processes**, five defined: P2P, O2C, Plan to Make, Hire to Retire, Record to Report.
- Each process is broken into weighted steps (P2P weights invoice capture and matching
  heaviest, at 17), and weighted by what matters for that kind of process — volume and
  exposure (P2P, O2C), the decisions it controls (P2M), what breaks if manual (H2R —
  offboarding doubles as a cyber finding), close effort and misstatement risk (R2R).
- **An unanswered question is never scored as zero.**
- The **only** place the AI may move a number: a step score by at most ±1, with a reason, on
  at most 3 steps, the deterministic score shown beside it.

**(b) Applications** — *no fit scores, no dispositions.* Per application: **criticality,
automation, AI level**. Four portfolio questions: is the core platform fit for the plan; how
are core systems integrated; how is management reporting produced; who owns applications.
Themes: end-of-support exposure, core platform upgrade, fragmentation and overlap, heavy
customisation, lack of integration, incomplete digitisation, **licensed capability not used**
(a process scored Manual/Emerging while systems claim to support it — *what was bought is
not what is used*), limited analytics, AI limited to embedded features.

**(c) Data & infrastructure** — domains scored 0–100 (ownership 25, master data 20, quality
30, lineage 10, privacy 15); platforms on support, patching, recoverability, capacity; **21
estate checks** across resilience, engineering and cyber (incl. pen test, awareness
training, DLP/MDM, ISO 27001/SOC 2, leaver revocation). **A tool is not a control:** a cyber
tool the target says it lacks fails its check until the analyst answers; a tool it has
passes nothing.

**(d) Team & governance** — counted from the team sheet: in-house vs outsourced mix, roles
only one person can do, **business-critical applications supported by exactly one person**.
Questionnaire (sourced to the book's IT organisation questions, COBIT governance objectives
and TOGAF's architecture board): dedicated IT leader, security accountability, dependency on
the parent group, steering committee, review of new technology, policies, KPI reporting,
vendor governance, capacity and skills against the plan, attrition, cross-training,
succession, documentation, retention through the deal. **Product deals** add: bus factor on
the core codebase, IP in contractor code, product-management ownership. Contracts expiring
within 12 months, change-of-control clauses and parent-held contracts land here too.

**(e) Strategy & projects** — is there a strategy (approved / unapproved / *a list of
priorities only* / none), who develops it, **is it funded**, how detailed is the roadmap; PMO
and portfolio governance; delivery record; AI strategy and governance (and, where AI is
material, training-data rights and model dependency). Projects on the target's own figures:
**over budget**, **late**, **spend ahead of delivery** (spent − % complete > 25 points), and
the analyst's **triage** — the book's rule: Day-1 critical / enables the plan / business as
usual / candidate to stop. **The roadmap is reconciled against the change budget:** remaining
allocation on in-flight and planned projects vs the latest change budget → "IT roadmap not
funded".

**Every register:** one row per theme; a consultant's edits (headline, evidence, action,
severity) survive re-scoring.

**(f) IT budget** — now a tab of Assess. Its findings group into six themes.
- **Three financial years** by default.
- **Variance:** actual vs budget per line, flagged beyond ±10%.
- **Movement:** actual spend moving more than 20% year on year is flagged. This is the
  source's own question, "significant variances year-over-year" (p. 74).
- **The total variance compares like for like:** unbudgeted spend is a finding of its own,
  not an overrun.
- **Six budgeting-process questions:**
  - how the budget is built;
  - who approves it;
  - how often spend is reported against it;
  - business cases for capital spend;
  - technology spend outside IT;
  - whether it is tied to the technology plan.
- **No % of revenue, no benchmark, no cost model.** See Q8.

### Step 7: Report
- **Sections:** cover, table of contents, context setting, glossary, in-scope areas, data
  limitations, executive summary, supporting analysis and appendix.
- **Executive summary: one row per finding**, grouped by diligence area (business process
  enablement, applications, infrastructure, cyber, data, IT organisation, IT governance,
  strategy, PMO, budgeting, contracts, engineering, AI), as in the Gaps & Risks deck.
  - Each finding has its **own risk** (editable) and its own "Target should…" actions.
  - At most 5 findings per area and 3 evidence bullets per finding; the rest are pointed to
    in the register. Applications can no longer flood the summary.
  - **Investment impact is XXX** per finding, for the team to complete.
  - **No finding is ever dropped.** One whose area is not configured appears under its own.
- **"Not assessed" vs "no material gaps":** an area claims no material gaps only when **at
  least half its requests have arrived**. Otherwise it reads Not assessed.
- **Data limitations:** requests still outstanding, requests answered in part with their
  follow-ups, missing inventories and checks that couldn't be established.
- **Supporting analysis differs by DD type:**
  - **Enterprise:** applications, landscape diagram, infrastructure, cyber, data,
    organisation & governance, strategy & project portfolio, budget, processes, AI adoption.
  - **Product:** architecture, engineering, product security, organisation & governance,
    data & AI, strategy & project portfolio, budget, business systems.
- **The landscape diagram** is drawn only from inventory facts. **Network diagrams** are the
  target's own, uploaded and placed in the appendix.
- **Every element is editable** and can be included or excluded, and edits survive
  regeneration. **The export is exactly what is on screen.**

---

## 4. How the AI is used (and contained)

- **One switch: `AI_MODE`.** Off (the default) runs every generator deterministically, even
  with a key. Auto turns the model on, skill by skill.
- **Ten skills,** each a `SKILL.md`. Each states what the model may change, what it must not
  change, its house rules, and its deterministic fallback. The file *is* the prompt, so the
  instructions a reviewer reads are the ones the model gets. They are visible in the app
  under **AI & skills**.
- **Guards checked after every call:**
  - **Scope deck:** wording only. It cannot add, drop or re-tier an area; if it tries, the
    whole tailoring is rejected.
  - **Report:** a rewrite that **adds any number** not already in the text is thrown away.
  - **Research:** no grounding means no stored run.
  - **Shared-drive scan:** a file not offered to the model can't be cited.
- **The fallback is always a complete deliverable.** The AI improves wording; it is never
  needed for content.

---

## 5. Questions a partner will ask — and the answers

**Q1. Is this just an AI writing a report?**
No. With AI off, which is the default, the platform produces the entire scope, request list,
scores, gaps and report with **no model at all**. Rules decide what is in scope and what each
score is; the analyst supplies the judgement. The AI only polishes prose, and it is checked
after every call.

**Q2. Can it hallucinate?**
Containment is structural:
- the model never decides content;
- research must be grounded in retrieved sources, or it isn't stored;
- a report rewrite that introduces a number is rejected.

With AI off, there is nothing to hallucinate.

**Q3. Where does the methodology come from?**
Two sources:
- **Roehl-Anderson (2013),** encoded rule by rule with page citations;
- **the KPMG scope-of-work deck,** for the voice and the rows.

Anything modern that the book lacks is tagged **[EXT]**: our practice, not the source's
authority. The assessment weights and thresholds are [EXT] calibrations (Q14).

**Q4. How do I know the scope is right? Can I disagree?**
Every area shows *why* it opened:
- the rule that fired;
- the intake answer behind it;
- the page citation;
- the depth reason.

You can override the tier, the title and the wording. The engine's original is kept beside
your edit.

**Q5. Product vs enterprise — who decides?**
The engine computes a mix from the intake (Enterprise ≤34, Blended 35–65, Product ≥66). The
deal team's declared preference overrides the band, while the computed value stays visible.
It drives which deck opens, and later which report sections appear.

**Q6. Why does cost say XXX?**
House rule: sequencing, cost, team and investment impact are judgement calls the engagement
team makes against the specific deal. The platform won't assert them. The fields are there
to complete, and they export exactly as typed.

**Q7. What if the target sends nothing?**
The report says so, section by section:
- data limitations list exactly what is outstanding;
- areas without evidence read **Not assessed**, not "clean";
- an area only claims "no material gaps" once at least half its requests have arrived.

**Q8. Why not benchmark IT spend as a % of revenue?**
A deliberate scope boundary. We review the **budgeting process** and spend against the
target's own budget; we don't build, validate or benchmark a cost model. The source itself
warns to *"utilize benchmarks with care, as factors unique to each organization's specific
situation can significantly impact a company's actual spending needs"* (p. 81).

**Q9. Aren't the analyst's scores subjective?**
The judgement is the analyst's; that is the point of diligence. It is disciplined three ways:
- **Defined ladders.** Every level has an observable descriptor.
- **Remarks.** Every answer carries the evidence heard.
- **Explicit arithmetic.** Unanswered questions are excluded rather than scored as zero, and
  "unknown" checks become gaps to validate.

Two analysts with the same evidence should land on the same level.

**Q10. Can we change the questions, weights or thresholds?**
Yes, without a developer. All of it is YAML that a practitioner can edit: the scope rows,
the rules, the questionnaires, the report routing and the templates. It is validated when
the server starts, so a malformed edit stops the server rather than producing a quietly
wrong score.

**Q11. Is there an audit trail?**
- Every generated deliverable is versioned.
- Every rule firing carries its id and citation.
- Every hand edit keeps the original beside it.
- Every AI-assisted output records which skill and version produced it.
- Gap and report edits are separate records, so you can see exactly what a person changed.

**Q12. Does client data leave the firm?**
With **AI off (the default), no**: nothing is sent to any model. With AI on, prompts go to
Google's Gemini API. **For production use, that needs an approved enterprise agreement with
data-use terms; the current setup is a development key.** Raise this before anyone switches
it on for a live deal.

**Q13. Does it replace the consultant?**
No. It removes the assembly work: drafting the scope, building the request list, chasing
documents, and compiling tables and the report skeleton. The time goes into interviews and
judgement instead. Every client-facing word is reviewable and editable before export.

**Q14. Are the thresholds and weights validated?**
They are calibrated, not yet validated across live engagements:
- the 3.0 fit threshold;
- the data-domain weights;
- the ±10% budget variance tolerance.

They are explicit and tunable precisely so they can be adjusted against real deals.

**Q15. What's the clever bit?**
The connections between modules:
- **Licence vs use.** A process scored Manual despite three supporting systems means the
  software was bought but isn't used.
- **Leavers.** Access revocation is assessed in Hire to Retire *and* surfaces as a cyber gap.
- **Unsupported platforms.** Applications running on out-of-support servers fall out of the
  join between two inventories.
- **Traceability.** Every executive-summary line traces back to a gap and an evidence trail.

**Q16. How long does a DD take with it?**
Not measured yet; don't quote a number. The honest claim is about the assembly work in Q13.

**Q17. What isn't built?**
- multi-user accounts and permissions;
- email reminders (stubbed in the UI);
- a client-facing export of the assessment scores (deliberately internal);
- the drive scan filling the inventories automatically.

---

## 6. Numbers worth quoting

| | |
|---|---|
| Encoded scope rules | 37 (26 active) |
| Scope decks | Enterprise 9 rows · Product 12 rows |
| Depth tiers | Screen · Assess · Deep dive |
| Business processes defined | 5 (P2P, O2C, P2M, H2R, R2R) |
| Maturity ladder | 0–5, index 0–100, 5 bands |
| AI may move a number | Only process step scores, ±1, max 3 steps, with reason |
| Templates | 7 inventories + IT financials sheet |
| Assess tabs | 6 (processes, applications, data & infrastructure, team & governance, strategy & projects, IT budget) |
| Gap themes | 50 across five assessments, each with a deal-impact lens |
| Estate checks | 21 (resilience, engineering, cyber) |
| AI skills | 10, all off by default |
| Backend tests | 579 |

---

## 7. Demo script (Project Kiln, ~10 minutes)

1. **Scope of work.** Open "Evidence, depth and provenance" on Applications. *"Every area says
   why it's here."* Edit a bullet to show it's editable before export.
2. **Request list.** Show priorities and their reasons, a follow-up question the drive scan
   raised, then the Application inventory tab. *"The target fills this in the same workbook."*
3. **Assess › Applications › Score & findings.** "Critical applications facing end-of-support
   risks", and "Licensed system capability not used": *"Order to Cash is manual although SAP
   claims to support it — what was bought is not what is used."* Open "what raised it".
4. **Assess › Data & infrastructure.** The recovery finding carrying the analyst's remark about
   the 2024 ransomware; a check failed because the target's cyber tools sheet says no DLP.
   *"A tool is not a control."*
5. **Assess › Team & governance.** "Critical dependency on individuals" — three critical
   systems each supported by one person — and "Heavy dependency on the parent group for IT".
6. **Assess › Strategy & projects.** S/4HANA readiness: 84% spent, 40% complete. *"Spend is
   running ahead of delivery."* The intranet project tagged a candidate to stop.
7. **Report.** One row per finding, grouped by area, risk cells coloured, XXX per finding.
   Edit an investment cell, regenerate to show the edit survives, then **Export PowerPoint**.
8. **AI & skills.** *"Off today. Here are the exact instructions it would follow, and what it
   may never change."*

---

## 8. If you get stuck

- **"Show me where that number came from."** Every score's step table, a finding's "what
  raised it" list, the rule id on a scope area, and `DD_ASSESSMENT_FRAMEWORK.md` for the
  source of every question.
- **"What if we disagree?"** Override it. The original stays beside the edit.
- **"What if the AI is wrong?"** It's off by default, and when on it can't change content.
