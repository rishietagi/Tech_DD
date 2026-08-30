# docs/phases/PHASE1_PLAN.md — Tech DD Platform, Phase 1

Companion to `CLAUDE.md`. That file is the constitution; this is the build plan.
Scope of this document: **Phase 1 only** — the routed application and the complete,
persisted intake. The Scope-of-Work *generation engine* is deliberately deferred to
Phase 2 (§10).

---

## 1. Where the mockup falls short

The existing single-file HTML mockup is a good design reference and a poor product.
Concretely:

**Architecture**
1. One `.html` file, one `<form>`, inline `<style>` and an IIFE. Nothing is
   composable, testable or routable.
2. `novalidate` + hand-rolled validation. No schema, no typed data, no server
   contract.
3. Nothing persists — its own ledger note says "autosaves nothing yet". Close the
   tab and the deal is gone.
4. Submission is a `preventDefault()` that swaps two divs. There is no engagement
   record, no ID, no list, no way to return to a deal.
5. No error, loading or empty states; no concept of a draft; no multi-user or
   multi-deal notion.

**Content — the part that actually matters**
The mockup captures 13 fields. None of them are sufficient to decide *what kind of
technical diligence this is*. It asks what the company does, but not:

6. Whether **software is the product** or an enabler of it — the single most
   determinative question for Enterprise vs Product DD.
7. Whether the estate is **built or bought** (in-house engineering vs SAP/Oracle/
   Salesforce/COTS), where it is **hosted** (cloud / on-prem / hybrid), and how big
   the **engineering org** is relative to total headcount.
8. What the **investor actually wants** post-close: standalone growth, cost takeout,
   buy-and-build, carve-out, integration onto an existing platform. "Strategic vs
   financial" is a proxy for this, not a substitute.
9. The **hold period and value-creation levers**, which set the time horizon the
   architecture has to survive.
10. **Regulatory and data sensitivity** (PII / PHI / PCI, GDPR / HIPAA / DPDP,
    SOC 2 / ISO 27001), which makes some workstreams mandatory irrespective of type.
11. **AI/ML dependence** — increasingly its own workstream (model governance, data
    rights, inference cost, vendor lock-in).
12. **Engagement logistics**: deal stage (IOI / confirmatory / exclusivity), bid and
    IC dates, level of access granted (full data room + management + code, VDR only,
    no code), clean-team constraints, budget and team envelope, deliverable format
    (red-flag memo vs full report vs 100-day plan). These set *depth*, and depth is
    half the scope.
13. **Known concerns / red lines** — the free-text field that most often determines
    where the team actually spends its hours.
14. **M&A history / carve-out or TSA context**, which opens an entire separation
    workstream on its own.

**Product surface missing entirely**
15. No engagement list, no resume-a-draft, no edit-after-submit.
16. No live feedback on what the answers imply — a user should see the
    Enterprise/Product leaning forming as they type, with the reasons shown, and be
    able to override it with a recorded justification. This is the product's core
    differentiator and the intake must be built to feed it.

Phase 1 fixes 1–5 and 15, captures 6–14 properly, and builds the *surface* for 16
against a placeholder engine.

---

## 2. Phase 1 definition of done

A developer clones the repo, runs four documented commands, and gets:

- `http://localhost:3000` — landing page, real routes, no dead links.
- A new engagement created through an eight-step routed intake wizard, with a draft
  autosaved to the backend on every step transition and resumable by URL.
- A review step that shows the full cover sheet and files the engagement.
- `/engagements` listing every engagement with status, target, structure and date.
- `/engagements/[id]` showing the filed intake, editable.
- `/engagements/[id]/scope` rendering a scope of work returned by
  `POST /api/v1/engagements/{id}/scope` — which in Phase 1 returns a **deterministic
  placeholder** clearly labelled as such in the UI.
- `http://localhost:8000/docs` — clean OpenAPI.
- `pytest` and `vitest` green; ruff/mypy/eslint clean.
- Repo is git-initialised with a real `.gitignore` and a sensible commit history.
  **No remote, no push.**

---

## 3. Intake information architecture

Eight steps. Each is its own route, each maps to one zod schema and one Pydantic
model. `*` = required.

### Step 1 — Deal Context (`/intake/[id]/context`)
- `dealName*` — internal codename for the engagement (text)
- `contextNarrative*` — what is happening and why now (textarea, min 40 chars)
- `dealStage*` — enum: Pre-IOI / IOI submitted / Confirmatory / Exclusivity / Post-signing
- `processType*` — enum: Broad auction / Limited process / Bilateral / Proprietary
- `sourceOfDeal` — text, optional

### Step 2 — Rationale (`/intake/[id]/rationale`)
- `rationaleNarrative*` — the thesis in plain terms (textarea, min 40 chars)
- `valueCreationLevers*` — multi-select: Organic growth / Product expansion /
  Buy-and-build / Cost takeout / Margin expansion / Geographic expansion /
  Digital or AI transformation / Multiple arbitrage
- `dealBreakers` — textarea, optional: what would make this a pass
- `knownConcerns` — textarea, optional: anything already suspected about the tech

### Step 3 — Deal Structure (`/intake/[id]/structure`)
- `investmentType*` — `strategic` | `financial` (toggle cards, keep the mockup copy)
- `stake*` — `majority` | `minority`
- `stakePercent` — number 0–100, optional
- `postCloseIntent*` — enum: Standalone / Integrate into existing platform /
  Carve-out from parent / Merge with portfolio company / Undecided
- `carveOutOrTsa*` — boolean: is this a carve-out or does it involve a TSA?
- `holdPeriodYears` — enum: <3 / 3–5 / 5–7 / 7+ / Evergreen (optional)

### Step 4 — Investor (`/intake/[id]/investor`)
- `firmName*`, `investorType*` (PE / VC / Growth equity / Corporate or strategic
  acquirer / Family office / Sovereign wealth fund / Other)
- `dealLeadName*`, `dealLeadEmail*`
- `checkSize` — text, optional
- `enterpriseValue` — text, optional
- `existingPortfolioOverlap` — textarea, optional: related assets already held
- `investorTechCapability` — enum: In-house tech team / Operating partner /
  Relies on advisors (optional) — affects how prescriptive the SOW should be

### Step 5 — Target Company (`/intake/[id]/target`)
- `companyName*`, `website`
- `sector*` (existing list + Logistics, Industrials, Edtech, Proptech, Insurtech,
  Media, Retail, Energy, Public sector)
- `lineOfBusiness*` — textarea, min 30 chars: what the company actually sells, to
  whom, and how it makes money
- `businessModel*` — enum: B2B SaaS / B2B2C / Marketplace / D2C ecommerce /
  Transaction or payments / Hardware + software / Services-led / Hybrid
- `revenueModel*` — multi-select: Subscription / Usage-based / Transaction take-rate
  / Licence / Advertising / Professional services / Hardware sales
- `digitalMaturity*` — enum: **Digital native** (software is the product) /
  **Digitally enabled** (software is a major channel) / **Traditional** (software
  supports operations) — the single strongest DD-type signal
- `headcount*`, `revenueStage*`, `hqLocation*`
- `geographies` — multi-select, optional
- `customerConcentration` — enum: optional
- `foundedYear` — number, optional
- `maHistory` — textarea, optional: prior acquisitions, unintegrated estates

### Step 6 — Technology Profile (`/intake/[id]/technology`)  ← new, load-bearing
- ~~`techIsProduct*`~~ — **REMOVED 2026-08-31** as redundant with `ddTypePreference`
  in Step 7. Rules A1 and M6 now read that field. See `docs/PROJECT_LOG.md`.
- `buildVsBuy*` — enum: Predominantly in-house build / Balanced build and buy /
  Predominantly COTS/packaged (ERP, CRM, etc.)
- `coreSystems` — multi-select, optional: SAP, Oracle, Microsoft Dynamics,
  Salesforce, NetSuite, Workday, ServiceNow, Custom in-house, Other
- `hostingModel*` — enum: Public cloud / Hybrid / Predominantly on-premise /
  Colocation / Unknown
- `cloudProviders` — multi-select, optional: AWS, Azure, GCP, Other, None
- `knownTechStack` — text, optional (kept from the mockup)
- `engineeringHeadcount` — number, optional
- `engineeringSharePct` — derived-or-entered %, optional
- `outsourcingReliance` — enum: None / Some contractors / Heavily outsourced (optional)
- `aiMlDependence*` — enum: None / Experimental / Embedded in the product /
  Core to the value proposition
- `dataSensitivity*` — multi-select: None / Personal data (PII) / Health data (PHI) /
  Payment data (PCI) / Financial data / Government or defence
- `complianceRegimes` — multi-select, optional: SOC 2, ISO 27001, HIPAA, PCI-DSS,
  GDPR, India DPDP, FedRAMP, Other, None known
- `knownIncidents` — textarea, optional: outages, breaches, audit findings

### Step 7 — Diligence Objectives & Logistics (`/intake/[id]/objectives`)
- `ddObjectives*` — multi-select: Validate scalability / Quantify tech debt /
  Assess security & compliance / Size IT cost & run-rate / Assess team & key-person
  risk / Test product roadmap credibility / Assess integration or separation effort
  / Evaluate AI capability / Confirm IP ownership
- `accessLevel*` — enum: Full (data room, management sessions, code access) /
  Data room + management sessions / Data room only / Limited or public information
- `codeAccess*` — enum: Full repository access / Read-only sample / Automated scan
  only / None
- `deliverableFormat*` — multi-select: Red-flag memo / Full diligence report /
  IC paper input / 100-day plan / Cost model
- `timelineWeeks*` — number: weeks available
- `bidDate`, `icDate` — dates, optional
- `budgetBand` — enum, optional
- `cleanTeamConstraints` — textarea, optional
- `ddTypePreference` — enum: Let the platform decide (default) / Enterprise Tech DD
  / Product Tech DD / Blended — with `ddTypeOverrideReason` required if not default

### Step 8 — Review & File (`/intake/[id]/review`)
Read-only cover sheet of everything above, grouped by section, each group with an
"Edit" link back to its step. Validation summary listing any missing required field
as a link. "File engagement" button → `POST /engagements/{id}/submit`.

---

## 4. Route map

```
/                                  Landing — what the platform does, "Start an intake",
                                   recent engagements strip
/intake/new                        Server action: creates a draft engagement, redirects
/intake/[id]/context               Step 1
/intake/[id]/rationale             Step 2
/intake/[id]/structure             Step 3
/intake/[id]/investor              Step 4
/intake/[id]/target                Step 5
/intake/[id]/technology            Step 6
/intake/[id]/objectives            Step 7
/intake/[id]/review                Step 8 — cover sheet + file
/engagements                       List: search, filter by status/type, sort by date
/engagements/[id]                  Filed engagement detail; per-section edit
/engagements/[id]/scope            Scope of Work (Phase 1: placeholder, labelled)
/about/methodology                 Static: the Enterprise vs Product framework,
                                   written from CLAUDE.md §2
```

`/intake/[id]/*` shares a layout carrying the masthead, the field counter, the
status stamp and the ledger rail (now a real step navigator with per-step
completion state and free navigation between visited steps).

---

## 5. Data model (backend)

```
engagement
  id (uuid pk) · deal_name · status (draft|filed|scoped|archived)
  current_step · created_at · updated_at · filed_at

engagement_intake            (1:1 with engagement, one JSON-ish column group per section)
  id · engagement_id (fk, unique)
  context_json · rationale_json · structure_json · investor_json
  target_json · technology_json · objectives_json
  -- each column is validated on the way in by its Pydantic section model, so the
  -- table stays stable while the questionnaire evolves. Promote a field to a real
  -- column only when it needs to be queried or indexed.

engagement_denorm            (columns lifted out for listing/filtering)
  company_name · sector · investor_firm · investment_type · stake
  digital_maturity · dd_type · dd_mix

scope_of_work
  id · engagement_id (fk) · version (int) · generator ('placeholder'|'rules'|'llm')
  dd_type · dd_mix · payload_json · created_at
  -- versioned: regenerating never destroys the prior scope
```

Alembic migration `0001_initial` creates all of it. `app/db/init_db.py` seeds
reference data (sectors, enums, and the Phase-2 workstream library stub).

---

## 6. API contract (`/api/v1`)

```
GET    /health                              → {status, version}
GET    /meta/enums                          → every enum the frontend renders,
                                              so option lists live in one place
POST   /engagements                         → create draft            201 {id, ...}
GET    /engagements                         → list (q, status, dd_type, limit, offset)
GET    /engagements/{id}                    → full engagement + intake
PATCH  /engagements/{id}/intake/{section}   → partial save of one section (autosave)
POST   /engagements/{id}/submit             → validate all sections, status→filed
PATCH  /engagements/{id}                    → edit after filing
DELETE /engagements/{id}                    → soft delete (status→archived)
POST   /engagements/{id}/scope              → generate scope, returns latest version
GET    /engagements/{id}/scope              → latest scope
GET    /engagements/{id}/scope/versions     → list versions
```

`PATCH .../intake/{section}` validates against that section's Pydantic model only —
partial drafts must be saveable while incomplete. `POST /submit` runs the strict
full-intake validator and returns field-level errors keyed by `section.field` so the
review step can link straight to them.

---

## 7. Frontend component inventory

**Primitives** (`components/ui/`) — all typed, all with forwarded refs, all built on
the tokens: `Field` (label + hint + error wrapper), `TextInput`, `TextArea`,
`Select`, `MultiSelect` (chip-based), `ToggleCardGroup` (the mockup's radio cards),
`NumberInput`, `DateInput`, `Button`, `Badge`, `Stamp`, `SectionHeader` (`§01` +
title + italic hint), `EmptyState`, `ErrorState`, `Skeleton`, `Toast`.

**Intake** (`components/intake/`): `IntakeShell` (layout), `LedgerRail` (desktop
step nav with completion dots), `LedgerChips` (mobile), `FieldCounter`,
`StepFooter` (Back / Save & continue), `AutosaveIndicator`, `CoverSheet` (review),
`ValidationSummary`, `SignalPanel` — a sidebar that shows the forming Enterprise/
Product leaning and the answers driving it. **In Phase 1 `SignalPanel` renders the
placeholder verdict and is visibly marked "preliminary — engine not yet enabled".**

**Engagement** (`components/engagement/`): `EngagementTable`, `EngagementCard`,
`StatusBadge`, `ScopeDocument`, `WorkstreamCard`, `ScopeHeader`.

**Behaviour**
- Autosave: debounce 800 ms on change + a forced save on step navigation and on
  `beforeunload`. Show "Saving… / Saved 12:04" in the shell.
- Draft resilience: mirror the current step's values into `sessionStorage` purely as
  a crash guard; the API remains the source of truth.
- Step guard: a user can move backwards freely and forwards to any visited step;
  moving forward past an incomplete step is allowed (drafts are drafts) but the step
  dot stays unfilled and the review step lists it.

---

## 8. Work breakdown for Claude Code

1. **Scaffold** — repo root, `environment.yml`, `requirements.txt`,
   `requirements-dev.txt`, `.gitignore`, `.env.example`, `README.md`, `Makefile`,
   `git init` + first commit.
2. **Backend core** — FastAPI app factory, settings, logging, error envelope, health
   route, SQLAlchemy session, Alembic init.
3. **Backend domain** — models, section Pydantic schemas, enums module, migration,
   seed script.
4. **Backend API** — engagement CRUD, section autosave, submit validation, meta
   enums, scope placeholder endpoint behind a `ScopeGenerator` protocol.
5. **Backend tests** — pytest with a SQLite fixture: create → patch each section →
   submit → list → scope. Cover the validation-error shape.
6. **Frontend scaffold** — Next.js 15 + TS strict + Tailwind v4, tokens, fonts,
   layout, masthead, footer, landing page.
7. **Frontend primitives** — the `components/ui/` set with a `/dev/ui` gallery route
   (dev-only) so they can be eyeballed.
8. **Intake flow** — shared layout, ledger rail, all eight step routes, zod schemas,
   RHF wiring, autosave hook, API client.
9. **Review + submit** — cover sheet, validation summary, file action, success state.
10. **Engagements** — list, detail, edit-in-place, scope route rendering the
    placeholder scope with its "placeholder" banner.
11. **Methodology page** — static content from CLAUDE.md §2.
12. **Tests & polish** — vitest for schemas and two key components, one Playwright
    smoke run through the whole flow, a11y pass, responsive pass at 360/768/1280,
    lint/format/typecheck clean.
13. **Docs & commits** — README with the exact four setup commands, final commit.
    **Stop. Do not push.**

---

## 9. Acceptance criteria

- [ ] `conda env create -f environment.yml && conda activate techdd` works from a
      clean machine.
- [ ] `pip install -r requirements.txt -r requirements-dev.txt` installs cleanly.
- [ ] `uvicorn app.main:app --reload` serves `/docs` with no schema warnings.
- [ ] `npm run dev` in `frontend/` serves all routes in §4; none 404, none error.
- [ ] Full intake can be completed, left mid-way, resumed from the URL in a new tab
      with all answers intact, then filed.
- [ ] Filed engagement appears in `/engagements` and its detail page is editable.
- [ ] `/engagements/[id]/scope` renders a structured scope document with a visible
      "placeholder — generation engine not yet enabled" banner.
- [ ] `npm run lint`, `npm run typecheck`, `vitest run`, `pytest`, `ruff check .`,
      `mypy app` all pass.
- [ ] `git status` clean, history readable, **no remote configured**.
- [ ] No `.html` page, no `localStorage` as source of truth, no `any`, no secrets.

---

## 10. Phase 2 — deferred, do not build

The SOW derivation engine. Planning starts only when Rishi says so. Phase 1's sole
obligation to it is the seam: `app/services/scope/base.py` defines

```python
class ScopeGenerator(Protocol):
    def generate(self, intake: IntakeFull) -> ScopeOfWork: ...
```

with `PlaceholderScopeGenerator` as the only implementation, selected via a
`SCOPE_GENERATOR` setting. Phase 2 adds `RulesScopeGenerator` and
`LlmScopeGenerator` beside it and flips the setting — no route, schema or UI rewrite.

Sketch of what Phase 2 will need, recorded here only so Phase 1 does not paint over
it: signal extraction from the intake → a weighted Enterprise/Product mix score →
selection from a versioned workstream module library (each module carrying
objectives, key questions, evidence requests, effort bands and applicability rules)
→ depth calibration from access level, timeline and deal stage → an LLM pass that
tailors wording to the target's line of business and the investor's stated
objectives → human review, edit and re-generation with version history.

The placeholder generator should return a small, honest, hard-coded scope in exactly
that shape (2–3 workstreams, each with objectives, key questions and evidence
requests) so the UI is built against the real contract from day one.
