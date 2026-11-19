# Phase 8: diligence-grade assessments (team, governance, strategy, projects) and strategic gaps

## Context

Rishi reviewed the built platform against a real KPMG "Gaps & Risks" deck and a client IRL
workbook (screenshots, 2026-11-18). Both are client material: **record structure only, and
never names**. The slides name the client, the target, its systems and a vendor.

His verdict is that the platform reads like an **enterprise-architecture review**, not a
**due diligence**:
- per-application fit scores and dispositions (Invest / Modernise / Replace…);
- gap registers with one row per application or platform;
- an executive summary dominated by applications.

A diligence asks something different. The book's own definition [DD_master §1.1, p. 70]:
**matters that can have a material impact on the value of the target**, expressed as:
- one-time cost;
- recurring cost;
- risk;
- synergy.

The slides show what that looks like. Each row is one **thematic finding** under a diligence
area, with its own risk level and "Target should…" actions. Examples of the shape:
- "Critical applications facing end-of-support risks";
- "Lack of comprehensive planning in IT strategy";
- "Heavy dependency on the parent group IT";
- "No dedicated IT team".

He asked for:
1. **Team & governance** and **Strategy & projects** assessments in Assess.
2. A **projects template** on the request page (the in-flight projects sheet).
3. Rename the IRL page, and rename **Data & technology → Data & infrastructure**.
4. **Dispositions removed** entirely.
5. **Gaps strategic, not transactional**.
6. An executive summary that is not application-heavy.
7. His own research into how team, product, enterprise and AI diligence is actually done, going beyond what he listed.

### Decisions (Rishi, 2026-11-18)
| # | Decision |
|---|---|
| D1 | The page is renamed **"Information requests"**. The workbook keeps the abbreviation IRL. |
| D2 | The executive summary has **one row per finding**, grouped by diligence area, each row with its own risk and actions. **Investment impact = XXX** is kept per finding. |
| D3 | Each application is asked **criticality, automation and AI level only**. The fit questions, the fit quadrant, dispositions, the debt index and the per-application gaps all go. |
| D4 | Two more templates: a **cyber tools inventory** and an **IT financials sheet**. Both round-trip through the workbook. |
| D5 | **IT budget moves into Assess** as a tab. The sidebar entry goes, and `/it-budget` redirects there. |

---

## What the research says (and what I'm adding beyond the brief)

Sources:
- **The book** [DD_master]: W-OPS p. 73, W-STRAT p. 74, W-PROC p. 73, W-VEN p. 73, and Ch. 20 on key people.
- **COBIT 2019** governance objectives: EDM01 governance framework, APO01 IT management framework, APO02 Managed Strategy, APO05 Managed Portfolio, APO07 Human Resources, BAI01 Programmes.
- **TOGAF**: the Architecture Board and compliance review. This is the *governance* idea only, not EA modelling.
- **Implement Consulting's IT DD framework**: portfolio health, benefit realisation, key-person replaceability, churn.
- **Practitioner PE sources**:
  - findings sorted as **deal breaker / red flag / value-creation opportunity**;
  - cost sorted as **one-off** (comes off the price) versus **recurring** (hits the multiple);
  - "one person holds architecture, code review and infra" as the most common product red flag.
- **AI diligence checklists** (Orrick, McCarter, Promise Legal):
  - strategy versus embedded vendor features;
  - governance and acceptable use;
  - training-data rights;
  - third-party model dependency;
  - retention of key data scientists.

Five things I'm adding that you didn't ask for, each grounded in the sources above:

1. **One finding model across every assessment: observation → theme → gap.**
   - Rules still fire on individual applications, platforms, roles and projects. These are **observations**, kept as evidence in a drill-down.
   - The register shows **themes**: each one a headline, evidence bullets ("3 of 14 applications, including X and Y, reach end of support within 24 months"), an implication, a "Target should…" action, a severity, and a **deal-impact lens**.
   - The lens is one or more of: `one_off_investment`, `run_cost`, `plan_risk`, `continuity`, `compliance`, `integration_dependency`. This is the book's p. 70 definition made explicit, and it is what makes a gap "strategic".
   - A test pins that **no register contains a per-item gap**.
2. **Facts versus judgement, carried into the new areas.**
   - The target supplies roles, projects and tools. The analyst supplies judgement: project **triage**, using the book's encodable rule [p. 8, 148] (Day-1 critical / enables the plan / business as usual / candidate to stop or defer); delivery confidence; and the questionnaire answers.
3. **The budget and the roadmap are reconciled.**
   - Remaining allocation on in-flight and planned projects is compared with the change budget on the IT budget tab.
   - This turns your "a document exists but there's no investment behind it" into a computed finding, not only a questionnaire answer.
4. **"A tool is not a control."**
   - The cyber tools inventory is evidence, never a pass. A tool marked *No* defaults its check to *fail*. A tool marked *Yes* leaves the check for the analyst to evidence.
   - This is the same licence-versus-use logic the process assessment already applies.
5. **Product and AI variants by rule, not by a separate module.**
   - Team & governance gains engineering questions on Product and Blended deals: bus factor on the core codebase, IP assignment on outsourced development, product-management ownership.
   - Strategy gains AI data-rights and model-dependency questions when AI is material (signal A11).
   - Enterprise deals get the embedded-AI and AI-governance questions only.

### Severity rule (one rule for every theme, stated in YAML)
| Severity | Meaning |
|---|---|
| **High** | Threatens continuity of a critical operation, creates regulatory exposure, or is an **unfunded investment the plan depends on**. |
| **Medium** | Constrains the plan or adds cost. |
| **Low** | An improvement. |

Escalators are declared per theme, e.g. "touches a criticality ≥ 4 application → High".

---

## Part A — The theme model (shared mechanics)

**Content.** Each assessment YAML gains a `themes:` block. Each theme has:
- `id`;
- `area` (a diligence area id, see Part F);
- `headline`;
- `implication`;
- `impact: [lens…]`;
- `action` ("Target should…", with `{subjects}` / `{count}` placeholders);
- `severity: {base, escalate_when}`;
- `trigger` (the named rule that collects observations).

Everything is validated at startup.

**Code.** `services/estate/gaps.py` gains:
- `Observation(rule, subject, text, critical)`;
- `build_theme_gaps(observations, themes)`: one gap per fired theme. It holds evidence bullets that summarise counts and name at most 3 subjects, the full observation list for drill-down, and severity from the declared rule.

`Gap` schema changes:
- adds `headline`, `evidence`, `implication`, `impact`, `action`, `area`, `observations`;
- `description` and `hypothesis` are replaced by `evidence` and `action`;
- the overlay can edit headline, evidence, action and severity;
- `scope` becomes `"theme"` only.

**Old payloads.** Estate assessment payloads get a version. An older payload is shown as "Re-score needed", not parsed. Only Kiln carries any.

## Part B — Applications (slimmed: no dispositions)

`applications.yaml`:
- **Questions kept:** criticality, automation and AI only.
- **Questions removed:** the `bf_*` and `tf_*` questions, and the `disposition`, `technical_health` and `hypotheses` blocks.
- **New portfolio questions** (option → finding, the IT budget pattern):
  - fitness of the core ERP / platform for the plan;
  - integration between core systems (governed APIs / point-to-point / manual re-keying);
  - reporting and analytics (one enterprise source / departmental / spreadsheets);
  - application ownership (central with named owners / decentralised by business unit / unclear).

**Themes** (from the book's common findings [p. 75] and the slide shapes):

| Theme | Fires when |
|---|---|
| Critical applications facing end-of-support risk | lifecycle EOL, or platform out of support |
| Core systems not integrated | portfolio question, plus a new inventory fact `integration` (API / file / manual) |
| Fragmented landscape with functional overlap | duplication clusters, or decentralised ownership |
| Business functions run outside systems | process with no system, or spreadsheets only |
| Licensed capability not used | weak process despite supporting systems (kept from Phase 6) |
| Heavy customisation constraining upgrade | high customisation on critical applications |
| Critical applications dependent on one person or vendor | key-person fact on critical applications |
| Limited enterprise analytics | portfolio question, or no analytics/BI application |
| AI adoption limited to embedded features | per-application AI levels |

**Moved elsewhere:**
- "Application inventory incomplete" becomes a **data limitation**, not a gap: it is information not provided.
- Contract expiry goes to contracts (Part F).

**Index.** The application index is the criticality-weighted automation index, kept, plus an AI adoption index.

## Part C — Data & infrastructure (rename and themes)

- **Labels only.** "Data & technology" becomes "Data & infrastructure" and "Technology platforms" becomes "Infrastructure platforms". The internal key `data_tech` stays, so nothing needs migrating. The workbook import accepts both the old and new sheet names.
- **New checks.** These match the shape of the slides and the cyber IRL:
  - IF1 asset lifecycle and refresh policy, funded;
  - CY9 penetration test / VAPT in the last 12 months;
  - CY10 security awareness training;
  - CY11 data-loss prevention and mobile device management;
  - CY12 certification (ISO 27001 / SOC 2) or an equivalent assessment.
- **Themes:**
  - data ownership undefined;
  - data not trusted for reporting;
  - personal data unclassified;
  - infrastructure out of support;
  - recovery capability untested (DR and RTO/RPO);
  - ageing end-user estate with no refresh plan;
  - cyber governance gaps;
  - identity and access gaps;
  - threat detection and response gaps;
  - vulnerability management;
  - third-party security;
  - delivery pipeline and security testing (engineering).
- **Cyber tools inventory** (`cyber_tool`, prefix T). Purpose comes from a fixed list mapped to checks:
  - SIEM → CY5; PAM → CY3; backup → RS3; patching → CY4; DLP/MDM → CY11; MFA/SSO → CY2;
  - endpoint protection, ITSM, network monitoring, threat intelligence, email security, firewall, vulnerability scanning.

  Other fields: available, vendor / product, managed by (in-house / MSSP / parent), coverage, remarks. The template pre-seeds one row per purpose, as the client sheet does. The tools appear as evidence beside each check, and the "a tool is not a control" defaulting applies (see addition 4).

## Part D — Team & governance (new domain `team_governance`)

**Computed from the IT team inventory** (facts already captured):
- headcount;
- in-house / outsourced / contractor mix;
- sole holders;
- **critical applications supported by exactly one person** (bus factor 1, joined to criticality);
- share of the team with under one year of service.

**Questionnaire.** Each option carries a value from 0 to 1 and a finding/severity. Every question has a source.

1. **Leadership & accountability** (COBIT EDM01/APO01; book W-OPS "Is IT leadership capable…")
   - dedicated IT leader (on the management team / below it / run part-time by the CFO or another executive / no one);
   - security accountability (CISO / IT leader / outsourced / none);
   - dependency on parent-group IT (standalone / shared under agreement / parent runs critical IT without agreement / not applicable).
2. **Governance & decision rights** (EDM01; TOGAF Architecture Board; book W-PROC and W-VEN)
   - IT steering committee with business members;
   - review of new technology before adoption;
   - policies approved and reviewed;
   - IT KPIs/SLAs reported to management, and how often;
   - governance of outsourced vendors (SLAs monitored, periodic reviews).
3. **Organisation & capacity** (book: "sufficient to support … expected growth")
   - capacity versus the plan;
   - skills versus the roadmap (cloud, data, security, ERP);
   - attrition over the last 12 months (bands [EXT]).
4. **People risk** (book Ch. 20; W-OPS on redundancy and succession)
   - cross-training on critical knowledge areas;
   - succession plans;
   - runbooks and documentation;
   - retention arrangements for key staff through the deal.
5. **Product engineering** (Product and Blended only)
   - bus factor on the core codebase;
   - one person holding architecture, code review and infrastructure;
   - IP assignment on outsourced development;
   - product-management ownership of the roadmap.

**Themes:**
- no dedicated IT leadership;
- key-person dependency (computed and questionnaire);
- reliance on outsourcing without vendor governance;
- dependency on parent-group IT;
- governance forums absent;
- capacity or skills short of the plan;
- high attrition;
- concentration of engineering knowledge.

**Index.** A 0-100 maturity index per section and overall. The bands are those already used.

## Part E — Strategy & projects (new domain `strategy_projects`)

**Projects inventory** (`it_project`, prefix P, sheet "In-flight IT projects"). Facts only:
- name, description, business objective, sponsor;
- status (planned / in progress / on hold / completed in the last 12 months / cancelled);
- start date, planned completion date, revised completion date;
- allocated capex, capex used, % complete as reported;
- delivery (in-house / outsourced / mixed), vendor;
- applications affected;
- business case approved.

**Analyst judgement per project:**
- **triage**: Day-1 critical / enables the plan / business as usual / candidate to stop or defer [book p. 8, 148];
- **delivery confidence**: on track / at risk / off track.

**Computed, from reported figures only:**

| Finding | Rule |
|---|---|
| Overrun | capex used > allocated |
| Spend running ahead of delivery | used ÷ allocated − % complete > 25 points [EXT] |
| Slippage | past the planned date and not complete, or revised date > planned |
| Unfunded roadmap | remaining allocation on in-flight and planned projects > the current year's change budget on the IT budget tab; or projects with no allocation |
| Vendor concentration | one vendor > 50% of in-flight allocation |
| Inherited commitments | remaining allocation on in-flight projects |
| Discretionary spend | share of in-flight spend tagged candidate-to-stop |

**Questionnaire:**
1. **IT strategy** (APO02; book W-STRAT; Implement)
   - Is there a strategy? (documented and approved / documented, not approved / high-level list of priorities only / none)
   - Who develops it? (IT with business leaders / IT alone / parent group / consultants, without ownership)
   - Is it aligned to the business plan?
   - **Is it funded?** (costed and in the budget / costed, not funded / not costed)
   - Roadmap detail (sequencing, dependencies, resources and timelines / priorities and dates only / none)
   - Refresh cadence.
2. **Portfolio governance** (APO05, BAI01)
   - prioritisation criteria and business cases;
   - a PMO and portfolio tool;
   - stage-gates and change control;
   - tracking of benefits realised.
3. **Delivery track record** — major projects over the last three years delivered on time and on budget.
4. **AI** (PD-12 and the AI checklists)
   - AI strategy (documented roadmap / ad hoc pilots / embedded vendor features only / none);
   - AI governance and acceptable-use policy;
   - *where AI is material:* training-data rights and provenance; dependency on a third-party model; model monitoring and evaluation.

**Themes:**
- no IT strategy, or strategy only a list of priorities;
- strategy not funded;
- roadmap lacks delivery planning;
- no PMO / portfolio governance;
- projects over budget or late;
- spend ahead of delivery;
- in-flight spend not aligned to the plan;
- AI strategy absent;
- AI governance absent;
- AI data rights or model dependency unverified.

## Part F — The report

- **Diligence areas** (`report.yaml › areas`): an ordered list of id, label and workstream:
  - business process enablement;
  - IT applications;
  - IT infrastructure;
  - cyber security;
  - data governance;
  - IT organisation;
  - IT governance;
  - IT strategy and roadmap;
  - project delivery (PMO);
  - IT budgeting;
  - IT contracts;
  - AI implementation;
  - product engineering (product deals).

  Each theme names its area. This replaces the routing-by-category table. A finding is still never dropped, and the test stays.
- **Executive summary (D2).** It is built from **themes**, grouped by area in configured order and ranked by severity within the area. Each finding row holds headline, bullets, risk, actions and investment XXX. With at most 5 findings per area, and themes rather than items, applications can no longer flood it.

  The PPTX changes to match the slides: a merged diligence-area cell; a bold headline over bullets; a coloured risk cell per row; a "Low / Medium / High" legend; and pagination by measured row height. The overlay keys become `exec.<area>.<theme>.<field>`.
- **Business process automation.** Per-process findings stay, since the slides do this too, under "Business process enablement".
- **Contracts and budget.** Their findings are converted to the theme shape.
- **Supporting analysis.**
  - Enterprise adds: *IT organisation & governance* (team mix, key-person table) and *IT strategy & project portfolio* (projects table: allocation, used, % complete, triage; plus the funding reconciliation).
  - Product adds the team section with engineering concentration.
  - Both add *AI adoption* when AI questions are answered.
  - The appendix adds projects and cyber tools.
- **Application tables** lose the disposition and fit columns.

## Part G — Information requests page, templates, Assess layout

- **Renames.** The page is "Information requests" (sidebar, header, cheat sheet, docs). The API path `/irl` and the type names are unchanged.
- **Inventory sections:**
  - Requests;
  - Applications;
  - Data & infrastructure;
  - IT team & contracts;
  - **Projects** (new);
  - **Cyber tools** (new).
- **IT financials sheet (D4).** One row per budget line and two columns per year (budget, actual), with a run/change kind. An upload fills the IT budget inputs, **never clears a value**, and reports what it filled. A standalone template download is also provided.
- **Assess tabs:** Business processes · Applications · Data & infrastructure · **Team & governance** · **Strategy & projects** · **IT budget** (D5: the existing page component, embedded).
- **Shared components.** The new tabs reuse `EstateAssessment` and the results view, extended for option questions and per-project judgement, and the same theme register.

## Part H — Docs, skills, tests

- **Docs.**
  - New `docs/reference/DD_ASSESSMENT_FRAMEWORK.md`: every question's source; the theme model; the deal-impact lens; the severity rule; the product/enterprise/AI variants; [EXT] tags; and what was searched for and not found.
  - `docs/phases/PHASE8_PLAN.md`.
  - `REPORT_STRUCTURE.md`: the per-finding layout, **structure only**.
  - `PROJECT_LOG`, `CLAUDE.md` §1/§9, `PARTNER_CHEATSHEET.md` (rewritten for themes and the two new assessments), README.
- **Skills.** `estate-summary` is updated (no dispositions; summarises themes, prose only). `report-executive-summary` is updated for per-finding rows (may reword headline and bullets; may not change the risk, the area, any number or XXX).
- **Tests:**
  - "disposition" appears nowhere in estate or report output;
  - every register is themes-only (no per-item gaps);
  - every theme is valid and reaches the executive summary;
  - key-person on a critical app gives High;
  - overrun, ahead-of-delivery, slippage and unfunded-roadmap rules;
  - a strategy that is documented but unfunded gives its theme;
  - tool No → fail, tool Yes → unknown;
  - projects, cyber tools and IT financials round-trip, and an upload never clears;
  - facts-only (no judgement fields) holds for `it_project` and `cyber_tool`;
  - the product-only questions are hidden on enterprise deals;
  - the cost-model boundary sweep extends to the new text;
  - the report's investment cell is XXX on every finding;
  - the scope deck is still anonymised.

**No DB migration.** Inventory kind and assessment domain are string columns, and the report and payloads are JSON.

---

## Checklist (execution order)

- [ ] 1. Docs first: `DD_ASSESSMENT_FRAMEWORK.md` (research, sources, every question), `PHASE8_PLAN.md`
- [ ] 2. Theme model: `Observation`, `build_theme_gaps`, `Gap` v2, overlay v2, payload versioning, YAML validation
- [ ] 3. Applications: strip fit/disposition/debt; three per-app questions; portfolio questions; `integration` inventory fact; nine themes; inventory-incomplete → limitation
- [ ] 4. Data & infrastructure: rename, new checks IF1/CY9–CY12, themes; `cyber_tool` inventory + check evidence/defaulting
- [ ] 5. Team & governance: computed people indicators, questionnaire (5 sections, product-only section), themes, index, API
- [ ] 6. Strategy & projects: `it_project` inventory, per-project triage/confidence, computed portfolio rules incl. budget reconciliation, questionnaire incl. AI, themes, index, API
- [ ] 7. IT budget: findings to theme shape; IT financials workbook sheet + import (never clears)
- [ ] 8. Report: areas list, per-finding executive summary, new supporting sections and appendix, PPTX per-finding layout with merged area cell, overlay keys
- [ ] 9. Frontend: rename to Information requests; Projects and Cyber tools sections; Assess six tabs (Team & governance, Strategy & projects, IT budget embedded); theme register view with evidence drill-down; remove dispositions from the UI; `/it-budget` redirect
- [ ] 10. Skills (estate-summary, report-executive-summary) + tests listed above
- [ ] 11. Verify: ruff, mypy, pytest; tsc, eslint, vitest; both servers; **fill Kiln with illustrative team/projects/tools/financials, score all six tabs, generate the report, render the PPTX to PNG and read every slide**; browser drive with no console errors
- [ ] 12. Update PROJECT_LOG, CLAUDE.md, cheat sheet, README; memory

## Verification

- Backend: `C:\miniconda\envs\techdd\python.exe -m pytest`, plus ruff and mypy. Frontend: tsc, eslint, and vitest run from `C:\…`.
- On Kiln:
  - The executive summary should read like the slides: thematic headlines, a mix of areas, at most 5 per area, and no application names as headlines.
  - Dispositions appear nowhere.
  - An unfunded roadmap appears when the change budget is below the remaining project allocation.
  - A tool marked No shows as a failed check, with the inventory as its evidence.
- Then a product-type engagement, to check that the engineering-team and AI questions appear and the enterprise-only wording does not.
- Render the PPTX through PowerPoint COM and inspect each slide image.
- **Confidentiality.** Nothing from the screenshots (client, target, system or vendor names) goes into the repo.
