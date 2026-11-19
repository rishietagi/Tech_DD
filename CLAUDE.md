# CLAUDE.md — Tech DD Platform

Project constitution. Read this file **and** `docs/phases/PHASE1_PLAN.md` before writing any code.
Rishi edits this file; treat it as authoritative over your own preferences.

---

## 1. What this product is

An end-to-end **Technology Due Diligence** platform for investors (PE, VC, corporate
acquirers, family offices).

The flow the product owns:

1. **Intake** — capture the transaction: deal context (including the investor
   firm), rationale and focus areas, deal structure, target company, target
   technology profile, and diligence objectives and logistics.
2. **Scope of Work generation** — from that intake, produce a tailored technical
   diligence scope: which areas open, at what depth, what evidence is requested.
   Built in Phase 2 — see §9.
3. **Company research** — search public sources for what is known about the target,
   with citations, to inform the request list. Built in Phase 3 — see §9.
4. **Information requests (the IRL)** — from the scope, produce the list of artefacts the
   target must supply, grouped by business function and exported to Excel for the
   client to complete, with the templates the target fills in (applications, data and
   infrastructure, IT team and contracts, projects, cyber tools, IT financials). Built in
   Phase 3; renamed and extended in Phase 8 — see §9.
5. **Checklist** — track which requested documents have actually arrived, ranked by
   importance. Built in Phase 4 — see §9.
6. **Assess** — perform the diligence: work through a business process step by step,
   recording what management said, and score its level of automation. Built in Phase 5,
   **complete for all five processes** — see §9. Phase 6 added **application** and **data &
   infrastructure** assessment beside the processes; Phase 8 added **team & governance** and
   **strategy & projects**, and moved the IT budget in as a tab. Each reports **themes** —
   strategic findings with a deal-impact lens — never one gap per system.
7. **IT budget** — review how the technology budget is built, approved and controlled,
   and reported spend against it. Built in Phase 6; a tab of Assess since Phase 8 — see §9.
8. **Report** — the final IT due diligence report, built from every module above, fully
   editable, exported to PowerPoint. Built in Phase 7 — see §9.

The central intellectual claim of the product: **the scope of a tech DD is not
generic.** It is a function of (a) the target's line of business and how central
software is to it, (b) the investor's objective and hold thesis, and (c) the deal
structure. The platform's job is to make that derivation explicit, auditable and
overridable.

---

## 2. The Enterprise vs Product DD axis (domain knowledge — memorise this)

Two archetypes sit at the ends of one spectrum. Real engagements are a blend; the
platform should express the blend as a ratio, not a binary.

### Enterprise Tech DD
Technology is an **enabler of** the business. The question is "does the IT estate
support the plan, and what will it cost?"

Typical workstreams: application landscape & ERP fitness; infrastructure, hosting
and cloud cost; IT operating model, org and spend (run vs change); vendor and
licence contracts; cyber security posture and compliance; business continuity and
DR; integration / separation (TSA, carve-out) readiness; IT capex and run-rate
normalisation; data governance; shadow IT.

Signals that pull this way: traditional or asset-heavy line of business; COTS/ERP
-heavy estate (SAP, Oracle, Dynamics, Salesforce); small engineering headcount
relative to total; carve-out or corporate-separation situation; cost-takeout or
buy-and-build thesis with IT consolidation; strategic acquirer intending to
integrate onto an existing platform; heavy on-prem footprint.

### Product Tech DD
Technology **is** the business. The question is "can this product and the team
behind it carry the growth case?"

Typical workstreams: architecture and scalability; code quality and technical
debt; engineering velocity and delivery metrics (DORA); SDLC, testing and release
practice; product management, roadmap credibility and PMF evidence; data and AI
capability; product security and multi-tenancy; IP ownership, open-source licence
hygiene and third-party dependencies; engineering talent, org design and key-person
risk; unit economics of infrastructure (COGS per customer).

Signals that pull this way: digital-native target; software or platform is the
revenue-generating asset; product-led growth motion; high engineering share of
headcount; predominantly in-house build; growth / multiple-expansion thesis;
minority growth investor backing a product roadmap; venture or growth-equity
investor type.

### Modifiers that apply to both
- **Majority** stake → deeper access, control-oriented workstreams (org change,
  cost takeout, 100-day plan) are in scope. **Minority** → influence-oriented,
  lighter, more reliance on management representations.
- **Strategic** investor → integration/interoperability, data migration, product
  overlap and rationalisation, security-posture alignment. **Financial** investor
  → standalone viability, scalability headroom, cost curve, exit-readiness.
- **Regulated data** (PII / PHI / PCI / financial) → mandatory compliance and
  privacy workstreams regardless of archetype.
- **AI/ML dependence** → model governance, data rights, vendor lock-in, inference
  cost workstreams.
- **Deal stage & access level** → determine depth: exploratory and bid-situation
  engagements are red-flag screens, exclusivity is confirmatory, and public
  information alone caps every area at a screen. (`code_access` is deliberately not
  captured — see `docs/PROJECT_LOG.md`.)

Glossary the code should use consistently: `engagement`, `intake`, `workstream`,
`module`, `scope_of_work` (SOW), `dd_type` (`enterprise` | `product` | `blended`),
`dd_mix` (0–100 product-weighting), `signal`, `override`.

---

## 3. Stack (locked — do not substitute)

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router) + React 19 + TypeScript (strict) |
| Styling | Tailwind CSS v4 + CSS variables for the design tokens |
| Forms | react-hook-form + zod (`@hookform/resolvers`) |
| Client state | Zustand for the intake draft; TanStack Query for server state |
| Backend | Python 3.11 + FastAPI + Pydantic v2 |
| LLM | **Google Gemini** (`google-genai`), model `gemini-2.5-flash` — see note below. **Off by default** (`AI_MODE=off`); every generator has a deterministic floor and a `SKILL.md` |
| ORM / DB | SQLAlchemy 2.0 (declarative, typed) + Alembic; SQLite in dev, Postgres in prod via `DATABASE_URL` |
| PPT export | **python-pptx** — pure Python. **The** client-facing artefact: a SOW is circulated as a deck. PDF export was removed 2026-09-02 |
| XLSX export | **xlsxwriter** — the IRL workbook (Function / Question / Response) |
| Web research | Gemini's `GoogleSearch` grounding tool — sources come back as citations |
| Testing | Vitest + Testing Library (FE), pytest + httpx (BE), Playwright for one smoke E2E |
| Lint/format | ESLint + Prettier (FE); ruff + black + mypy (BE) |
| Env | **conda** environment named `techdd`, Python 3.11 and Node 20 both installed into it |

Hard rules:

- **No standalone `.html` file as the frontend.** No jQuery, no CDN script tags,
  no vanilla-JS DOM manipulation. Every screen is a React component under a real
  Next.js route.
- **No `localStorage` as the system of record.** It may cache an in-progress draft
  for resilience only; the backend is the source of truth.
- No `any` in TypeScript. No bare `except:` in Python.
- Server URLs, keys and secrets come from env vars only. Never hard-code them.

**LLM provider — recorded deviation (2026-08-30).** `docs/phases/PHASE2_SPEC.md` §8 and
earlier versions of this table specified the Anthropic Messages API. Rishi chose
**Gemini** instead: a Claude Pro subscription does not include API credits, and Gemini
has a free tier (`aistudio.google.com/apikey`, no card required). The LLM layer is
prose-tailoring only — the deterministic engine decides what the scope contains — so
the provider choice does not affect defensibility or the audit trail. Swapping back
means rewriting `services/scope/llm.py` and re-pinning the SDK; nothing else depends
on it.

---

## 4. Repository layout

```
Tech_DD/
├── CLAUDE.md                  # this file — the constitution
├── README.md                  # setup + run instructions
├── docs/
│   ├── PROJECT_LOG.md         # running log of decisions and state — READ THIS FIRST
│   ├── PARTNER_CHEATSHEET.md  # presenting the platform: workflow, logic, partner Q&A
│   ├── phases/
│   │   ├── PHASE1_PLAN.md     # Phase 1 build plan (intake)
│   │   ├── PHASE2_SPEC.md     # Phase 2 build spec (scope engine)
│   │   ├── PHASE2_PROMPT.md   # the Phase 2 handoff prompt
│   │   ├── PHASE3_PLAN.md     # Phase 3 build plan (IRL + research)
│   │   ├── PHASE4_PLAN.md     # Phase 4 build plan (checklist + shared-drive scan)
│   │   ├── PHASE5_PLAN.md     # Phase 5 build plan (assess)
│   │   ├── PHASE6_PLAN.md     # Phase 6 build plan (estate assessment + IT budget)
│   │   ├── PHASE7_PLAN.md     # Phase 7 build plan (report, AI pipeline, edit-before-export)
│   │   └── PHASE8_PLAN.md     # Phase 8 build plan (team, governance, strategy, projects; themes)
│   └── reference/
│       ├── DD_master.md       # the domain authority (Roehl-Anderson 2013)
│       ├── KPMG_SOW_LANGUAGE.md  # house scope-of-work voice, from the source deck
│       │   # (the source PDF is gitignored — client-confidential, local only)
│       ├── P2P_AUTOMATION_MODEL.md   # Assess: Procure to Pay, 9 steps  [EXT]
│       ├── O2C_AUTOMATION_MODEL.md   # Assess: Order to Cash, 8 steps   [EXT]
│       ├── P2M_AUTOMATION_MODEL.md   # Assess: Plan to Make, 8 steps    [EXT]
│       ├── H2R_AUTOMATION_MODEL.md   # Assess: Hire to Retire, 9 steps  [EXT]
│       ├── R2R_AUTOMATION_MODEL.md   # Assess: Record to Report, 8 steps [EXT]
│       ├── ESTATE_ASSESSMENT_MODEL.md  # Phase 6 estate model (partly superseded by the next)
│       ├── DD_ASSESSMENT_FRAMEWORK.md  # Phase 8: themes, deal-impact lens, every question's source
│       ├── REPORT_STRUCTURE.md  # the final report's structure (from a sample; no client content)
│       └── mockup_v0.html     # v0 visual reference (architecture superseded)
├── assets/                    # brand assets (logos)
├── .env.example               # every env var, no real values
├── environment.yml            # conda env `techdd` (python 3.11 + nodejs 20)
├── requirements.txt           # backend python deps, pinned
├── requirements-dev.txt       # test/lint deps
├── Makefile                   # make setup / dev / test / lint
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory, CORS, router mount
│   │   ├── core/              # config.py (pydantic-settings), logging.py, errors.py
│   │   ├── db/                # base.py, session.py, init_db.py
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── api/v1/            # router.py + routes/{engagements,scope,meta}.py
│   │   ├── services/
│   │   │   └── scope/         # the engine: signals, scoring, selection, depth,
│   │   │                      #   composer, llm, export (internal Markdown),
│   │   │                      #   export_pptx + prompts/
│   │   ├── irl/               # seeds, composer, llm, export_xlsx, import_xlsx + prompts/
│   │   ├── assess/            # process questionnaires, scoring, llm + prompts/
│   │   ├── research/          # grounded web search + prompts/
│   │   └── checklist/         # ranking, service, scanner + extract + scan_llm
│   │   └── report/            # inputs, findings (routing), sections, diagram, builder,
│   │   │                      #   edits (overlay), llm (prose only), export_pptx
│   │   └── intelligence/      # skills registry + use_llm (the AI_MODE switch)
│   │   └── estate/            # inventory (+ xlsx), applications, data_tech, gaps,
│   │                          #   budget, llm (prose only) + prompts/
│   │                          #   content: reference/estate/*.yaml
│   │   └── reference/         # enums + kpmg_scope/*.yaml + scope_rules.yaml
│   │                          #   + investigation_questions.yaml (the IRL's questions)
│   │                          #   + processes/*.yaml (the Assess questionnaires)
│   ├── alembic/
│   └── tests/                 # incl. golden cases and mocked LLM tests
└── frontend/
    ├── public/                # logos served by next/image
    └── src/
        ├── app/               # routes (see docs/phases/PHASE1_PLAN.md §4)
        ├── components/        # ui/ (primitives) + intake/ + engagement/
        ├── lib/               # api client, zod schemas, store, formatting
        ├── types/             # shared TS types mirroring backend schemas
        └── styles/            # tokens.css + globals.css
```

**Domain content lives in YAML, not Python.** `reference/kpmg_scope/*.yaml` and
`reference/scope_rules.yaml` are editable by a practitioner without a developer, and
validated at startup. Put content there, not in code.

---

## 5. Environment & dependency rules

- Create the conda env **before** anything else:
  `conda env create -f environment.yml` then `conda activate techdd`.
- Python deps: `pip install -r requirements.txt -r requirements-dev.txt` **inside
  the activated env**. Pin every dependency to a known-good version.
- Node deps: `npm install` inside `frontend/`, using the Node that conda installed
  into `techdd`. Commit `package-lock.json`.
- If you add a Python dependency at any point, add it to `requirements.txt` in the
  same commit. No undeclared imports.
- Never `pip install` into the base environment.

---

## 6. Git rules

- **Rishi does all pushing.** You never run `git push`, never create a remote,
  never open a PR, never force-push, never rewrite history.
- You may and should: `git init` (if absent), write a proper `.gitignore`, and
  `git add` + `git commit` locally with clear conventional-commit messages
  (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
- `.gitignore` must cover at minimum: `.env`, `*.db`, `*.sqlite3`, `__pycache__/`,
  `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.venv/`, `node_modules/`,
  `.next/`, `out/`, `dist/`, `coverage/`, `.DS_Store`, `.idea/`, `.vscode/`,
  `*.log`, `.conda/`.
- Never commit `.env`, a populated SQLite file, or anything with a real key in it.
- Keep commits scoped — scaffold, backend, frontend routes, styling, tests as
  separate commits rather than one monolith.

---

## 7. Engineering conventions

**Backend**
- Routes are thin; logic lives in `app/services/`. Routes do validation +
  delegation + response shaping only.
- One Pydantic schema per direction (`EngagementCreate`, `EngagementRead`,
  `EngagementUpdate`). Never return SQLAlchemy models directly.
- All IDs are UUIDs (string in SQLite, native in Postgres).
- Every table carries `created_at` / `updated_at` (UTC, timezone-aware).
- Errors return a consistent envelope: `{"detail": {"code": ..., "message": ...,
  "field_errors": [...]}}`.
- API is versioned under `/api/v1`. OpenAPI must be clean enough to generate the
  TS client from.

**Frontend**
- Server Components by default; `"use client"` only where interactivity demands it.
- One zod schema per intake step in `lib/schemas/`, composed into a full
  `intakeSchema`. The same schema shape is mirrored by the backend Pydantic models —
  if they drift, that is a bug.
- No fetch calls inside components. All network access goes through
  `lib/api/client.ts` + typed wrappers.
- Every interactive element is keyboard-reachable and labelled. Respect
  `prefers-reduced-motion`. Target WCAG AA contrast.
- Loading, empty and error states are required for every data-backed view — not
  optional polish.

---

## 8. Design language (carry over from the mockup — do not invent a new one)

> **Superseded in part (Rishi, 2026-11-18/19).** The app now wears the **KPMG theme**: KPMG
> blue `#00338D` sidebar and primary actions, light blue `#0091DA` for information, white
> paper — tokens in `frontend/src/styles/tokens.css`. Type is a **Helvetica-style
> neo-grotesque**: **Inter** for text and **Inter Tight** for headings, loaded with
> `next/font/google` (Helvetica itself is licensed and Windows swaps it for Arial).
> `font-serif`/`font-display` both map to the heading face, `font-mono` to Inter with
> tabular figures, and `font-code` (Plex Mono) is the only true monospace. Screens ease in
> (`app/template.tsx`), route segments show `PageLoader` (`loading.tsx`), sidebar links show
> a top progress bar while pending, and placeholders shimmer. The palette and fonts below are
> history; the motifs (section numbers, progress rail, status stamp, cover sheet) still apply.
>
> **Explainability is a design rule** (Rishi, 2026-11-19): every computed number carries an ⓘ
> (`InfoTip`) or a "How … is scored" disclosure (`HowItWorks`) stating its rule and formula.
> All the text lives in `components/engagement/explain.tsx`, written from the backend code —
> change it when a scoring rule changes. Editors and confirmations open as a centred `Modal`,
> never a side drawer.
>
> **Minimal** (Rishi, 2026-11-19): hairlines not shadows, nothing moves on hover, colour only
> where it carries meaning (a dot for band or severity), short page intros, longer
> explanation in drop-downs. Every Assess result reads **score → findings → detail**, and
> every findings register is editable and exports to Excel (per tab and all together).

Editorial / legal-document aesthetic: paper ground, ink text, a single red accent
used as a "redline", a steel blue for informational and focus states. Serif for
display headings, sans for UI, mono for labels, section numbers and metadata.

Port these to CSS custom properties in `styles/tokens.css` and expose them to
Tailwind (`tailwind.config.ts`) as named colours. Do not scatter raw hex values in
components.

```
--ink #14171F   --ink-2 #1D212B
--paper #ECEDE6 --paper-2 #E1E2D8 --paper-3 #D8D9CD
--line rgba(20,23,31,0.16)  --line-strong rgba(20,23,31,0.32)
--text #1B1D18  --muted #6C6F63  --muted-2 #8B8E82
--redline #9C3B2E  --redline-dark #7C2E23  --redline-tint rgba(156,59,46,0.09)
--steel #3F5E78    --steel-tint rgba(63,94,120,0.10)
--radius 3px
serif "Newsreader" · sans "IBM Plex Sans" · mono "IBM Plex Mono"
```

The v0 single-file mockup is preserved at `docs/reference/mockup_v0.html` as a
**visual** reference for the toggle cards, ledger rail, stamp and cover sheet.
Read it for the look; ignore its architecture entirely.

Load fonts with `next/font/google`, not `<link>` tags. Keep the motifs that carry
meaning: section numbering (`§01`), the ledger/progress rail, the status stamp
(Draft → In Progress → Ready to File → Filed), the confirmation "cover sheet".

---

## 9. Phasing — where the project stands

**Phase 1 — BUILT and pushed.** The routed application and the fully persisted intake.
Now six steps (was eight; the Investor step was folded into Deal Context on
2026-08-30). See `docs/phases/PHASE1_PLAN.md`.

**Phase 2 — BUILT and committed.** The scope-of-work engine: signal extraction
from 37 encoded rules, Enterprise/Product mix scoring, KPMG scope-row selection and
depth calibration, LLM prose tailoring, and Markdown export. Spec at
`docs/phases/PHASE2_SPEC.md`, though several of Rishi's decisions override it — see
`docs/PROJECT_LOG.md`.

**Two scope boundaries are enforced, not merely preferred** (2026-09-14, Rishi). A bullet
that crosses one promises work that is not being sold, so both are in the row content,
in `tailoring.md` Rule 2a, and swept by tests across every client-facing string in both
decks:

1. **IT financials means the budgeting process, never a cost model.** How the technology
   budget is defined, agreed and approved, and reported spend against it. We do not
   build, rebuild, validate or benchmark a standalone or allocated cost model. The
   **financial review period is stated** — three financial years is the house default, and
   a practitioner overrides the row where a deal needs otherwise.
2. **We do not scope, draft or negotiate transitional service agreements.** On a carve-out
   we review **contracts and their expiry** — terms, expiry and renewal dates, notice
   periods, assignment and change-of-control. The two TSA rules (M4, C7) have been dormant
   since the intake field was removed on 2026-08-30; what changed in 2026-09-14 was the
   remaining vocabulary and the substance that replaced it.

**The product deck carries twelve rows, not ten.** Rows 1-10 are the verbatim KPMG
objectives. **PD-11 (product financials)** and **PD-12 (artificial intelligence
readiness)** were added 2026-09-14 because the source deck has neither. PD-12 opens only
where AI is material — it carries `W-DATA` and trigger `A11`, deliberately **not**
`W-PROD`, which M6 forces open on every Product DD and would have opened the row on every
product deal. Both decks' organisation rows also ask for the **in-house versus outsourced
mix**, the skill sets held, and the number of third-party vendors.

**One rule-sourcing change worth knowing before you touch scoring** (2026-08-31): the
Technology Profile's "Is the software the product?" question was removed as redundant
with `dd_type_preference`, and rules **A1** (mix +35) and **M6** (W-PROD at Tier ≥ 2)
now read the declaration instead. Consequence: under "Let the platform decide" both are
silent by design and the computed mix rests on A2/A5/A6. Do not reintroduce the intake
field — tune those weights instead. Full reasoning in `docs/PROJECT_LOG.md`.

**Phase 3 — BUILT**, extended 2026-09-02: the list now **asks questions as well as
requesting documents** — `DD_master` §6 gives every workstream both, and the engine had
been discarding the questions; requests can be added, reworded and deleted by hand (edits
survive regeneration); the list groups by the **scope of work's own headings** with the
owning function as its own column; and a completed workbook can be **uploaded** to
auto-fill responses. The Initial Request List and company research. The IRL derives from
the scope: every KPMG row's `evidence` list seeds a request, so each question traces to a
scope area a rule opened and the list generates with the LLM off. Research is a grounded
web search that **refuses rather than fabricating** — no grounding metadata, no stored
run — and feeds the IRL so its questions and function names fit the actual business. Plan
at `docs/phases/PHASE3_PLAN.md`.

**Research produces a business brief** (2026-09-11, extended 2026-09-14): **eight** cited
sections — executive summary, what they do, how they make money, customers and markets,
the sector, competitive position, **the technology they use**, and what it means for the
diligence. The technology section reads the **publicly visible stack** — job adverts,
engineering blogs, status pages, partner directories, case studies — because that is a
diligence input available before the data room opens. It is the **most invention-prone
section in the brief**, since a plausible stack can be written for any company from no
evidence, so it carries a harder rule than the rest: name a technology only where a source
names it for this company, and return nothing otherwise. An empty technology section is
the expected outcome for many private targets. It **does** feed the IRL, because it is
observed fact about the target rather than the module's own opinion. A section the sources do not support is
**omitted, not padded**. The brief feeds the IRL so requests fit the business, but
`implications_for_diligence` is deliberately withheld from it — that section is the
module's own analysis, and the request list takes its cues from the scope, not from a
model's opinion. Citations come from a **second model call**: source ids are assigned from
grounding metadata *after* the answer is written, so the model cannot cite ids that did not
exist when it wrote. Before that pass existed, every stored run carried empty citations.

**Each deliverable is its own versioned child table** hanging off `engagements`
(`scope_of_work`, `information_request_list`, `company_research`, plus `irl_response`).
Adding a module later is one more table + service + router — do not reshape what exists.

**Phase 4 — BUILT.** Tracking of what has arrived against each IRL request, ranked
Critical/High/Medium/Low from the scope tier and the workstream. **The separate checklist
page was deleted on 2026-09-09** (Rishi) and everything it did — progress, the shared-drive
scan, the reminder stub — now lives on the Initial Request List, because the scan's
findings only mean anything beside the request they belong to. The checklist API is
unchanged and still backs it. Plan at `docs/phases/PHASE4_PLAN.md`.

**The shared-drive scanner was built on 2026-09-09** and is no longer deferred. It reads
every file on the drive, matches it to a request, and writes the document type, the
receiving status and — where what arrived is partial — the **follow-up questions** that
close the gap. It never overwrites a human-set status, records what it matched, and only
scans `document`-kind requests: a question is answered in a meeting, not by a file. Email
reminders remain a stub.

**Deferred and in scope — do not treat as missing work:**
- **Email reminders** — frontend stub only, honestly badged "Not connected yet".
- **A client-facing export of the Assess score** — the view is internal-facing by decision;
  the payload carries everything a PPT/PDF would need. Not built rather than guessed at.

**Phase 5 — COMPLETE. All five processes are defined** (2026-09-14): Procure to Pay,
Order to Cash, Plan to Make, Hire to Retire and Record to Report. The Assess module is a
questionnaire per process with conditional **nudges** (if X is the answer, ask Y), a blank
response against every question, analyst-added questions, and a deterministic 0-100
automation index with an executive summary and pointers. **No process is named with nothing
behind it**, and the 409 `process_not_defined` path — still correct, still tested against a
synthetic entry — is no longer reachable in practice.

**The five are not all the same kind of process, and the models say so rather than
borrowing P2P's framing.** P2P and O2C are transaction cycles weighted by volume and
financial exposure. P2M is a decision cycle weighted by the exposure each decision
controls. **H2R is an identity and obligation lifecycle weighted by what breaks when the
step is manual** — offboarding processes almost no events and carries one of the heaviest
weights, because a leaver whose access persists is a live credential. **R2R is a periodic
close weighted by close effort and misstatement risk**, where "volume" barely applies and
the currency is days to close, manual journal count and reconciliation backlog.

**H2R is the one process whose automation gap is also a cyber finding.** Joiner-mover-leaver
is the mechanism the security workstream assumes is working, so the questionnaire elicits
**revocation timeliness in days**, not whether a checklist exists — a documented but
unmeasured process scores 2, never 4. Do not soften that; it is pinned by a test.

**R2R grades the mechanism, not the accounting.** Whether a provision is adequate is the
quality-of-earnings team's question. What this contributes is how much of the reported
result is assembled by hand. Its shape note is deliberately narrower than the other four —
the steps of a close are sequentially dependent, so an even profile is the ordinary result
and the note says so instead of inventing a finding.

**A new process is pure content**: a model document, a questionnaire YAML, a registry flip
and tests. The maturity ladder, the scoring arithmetic, the banding, the API, the scoring
prompt and the frontend are process-agnostic. The one exception was the **shape note**,
whose commercial reading is genuinely process-specific — it moved into a `shape` block in
each questionnaire on 2026-09-09. **H2R and R2R found no second exception**, which is the
strongest evidence the claim holds.

Plan at `docs/phases/PHASE5_PLAN.md`; the domain models at
`docs/reference/{P2P,O2C,P2M,H2R,R2R}_AUTOMATION_MODEL.md`.

**Assess is the one module where the LLM may move a number** (2026-09-02, Rishi's explicit
choice). It may refine a step score by **at most ±1**, with a stated reason, and the
deterministic score is always kept beside it. Everywhere else the model writes prose only.
Do not "simplify" this back to prose-only, and do not loosen the bounds — read the decision
entry in `docs/PROJECT_LOG.md` first.

**The generated deck follows house rules that are enforced in code** (2026-09-02, Rishi):
it never names the target or the investor ("the Target", "the Acquirer", "the Parent"),
headings are generic with the specifics in the bullets, abbreviations are expanded, bullets
are short and verb-led, and sequencing/cost/team are left as **XXX** for the engagement team
to complete. `services/scope/llm.py::enforce_house_rules` backs the prompt up — do not
remove it on the grounds that the prompt already says so. The deal codename ("Project
Kiln") is deliberately kept; only the company name is scrubbed.

**Phase 6 — BUILT** (2026-11-18): the estate. Adapted from Rishi's CIL EA tool; its logic
was carried over, none of its client data. Plan at `docs/phases/PHASE6_PLAN.md`, reference
at `docs/reference/ESTATE_ASSESSMENT_MODEL.md`.

- **Inventories on the IRL** — applications, data domains, technology platforms. They
  travel as extra sheets in the IRL workbook (and as standalone templates), round-trip by a
  visible ID, and an upload never clears a value. They hang off the engagement, not an IRL
  version, so regenerating the request list never wipes them.
- **The target supplies facts; the analyst supplies judgement.** The inventory carries no
  fit, criticality or maturity field — a test bans them. Those questions are asked in Assess.
- **Assess has three tabs**: business processes (unchanged), **applications** (fit gives
  Invest / Retain / Modernise / Replace / Consolidate; automation on the same 0-5 ladder as
  the processes; AI on its own ladder; technical health from intake facts) and **data &
  technology** (per domain, per platform, and estate checks for resilience, engineering and
  cyber). Each scores on a click into a versioned result with an editable gap register;
  edits are an overlay that survives re-scoring.
- **Applications map to the five business processes.** The headline finding this enables:
  a process scored Manual or Emerging while systems claim to support it — what was bought is
  not what is used. Spreadsheets do not count as supporting systems.
- **The LLM is prose only here** — the ±1 refinement stays unique to business processes.
- **IT budget is a budgeting-process review**, never a cost model: budget against actual
  over the review period, variance like-for-like, the run/change mix as reported, and how
  the budget is built and approved. No share of revenue, no benchmark band — swept by a test.

**Phase 7 — BUILT** (2026-11-18): the final report, the intelligence pipeline and
edit-before-export. Plan at `docs/phases/PHASE7_PLAN.md`; structure at
`docs/reference/REPORT_STRUCTURE.md` (taken from a real KPMG report Rishi shared — **structure
only; never add the sample's client, target or people to the repo**).

- **One AI switch.** `AI_MODE=off` (default) runs every generator deterministically even with
  a key; `auto` turns the model on per skill. Every generation task has a
  `backend/app/skills/<name>/SKILL.md` — frontmatter stating what the model may and must not
  change and its deterministic floor, then the prompt itself. **The SKILL.md is the single
  source of the prompt**; no `prompts/` folders remain, and a test fails if one reappears.
  Decide rules vs LLM only through `intelligence.mode.use_llm`.
- **The report** (Report tab, after IT budget) follows the sample: cover, context, glossary,
  in-scope areas, data limitations, executive summary (findings + implication, RAG risk,
  actions, **investment = XXX** for the team), supporting analysis, appendix. Findings are
  routed to areas by workstream (`reference/report/report.yaml`); **no finding is ever
  dropped** — one with no area gets a fallback area. Supporting analysis differs by DD type.
  The landscape diagram is drawn from the inventories; network diagrams are the target's own,
  uploaded. The LLM may rewrite prose only and **may not introduce a number** (checked).
- **Everything exportable is editable before export** (Rishi): scope bullets, summary,
  objectives, risks and delivery approach; research brief (and hand-written when AI is off);
  every report element, via an overlay keyed on stable element keys that survives
  regeneration.
- **Naming.** The report names the investor and the target. The scope deck stays anonymised
  — and now really is: the house rules ran only after LLM tailoring, so the rules deck named
  the target until 2026-11-18.
- **Two more inventories**: IT team and IT contracts, feeding people and contract findings.

**Phase 8 — BUILT** (2026-11-18): diligence-grade assessments. Plan at
`docs/phases/PHASE8_PLAN.md`; model and sources at `docs/reference/DD_ASSESSMENT_FRAMEWORK.md`.
Rishi's verdict on Phases 6–7 was that they read like an enterprise-architecture review, not
a due diligence. What changed, and what must not drift back:

- **Registers report themes, never one gap per system.** Rules fire on single applications,
  platforms, roles and projects; those are **observations**, the evidence under a **theme**
  (`themes:` in each assessment YAML). A theme carries headline, implication, a
  **deal-impact lens** (one-off investment, run cost, plan risk, continuity, compliance,
  integration — DD_master p. 70 made explicit), a "Target should…" action and severity.
  A test pins themes-only registers. Information not provided is a **data limitation**, not
  a finding.
- **No dispositions.** Per application: criticality, automation and AI only. Do not
  reintroduce fit scores or Invest/Retain/Modernise/Replace.
- **Assess has six tabs**: business processes, applications, data & infrastructure (internal
  key still `data_tech`), **team & governance**, **strategy & projects**, **IT budget**.
- **The executive summary is one row per finding**, grouped by diligence area
  (`reference/report/report.yaml › areas`; every theme must name one or the boot fails),
  each with its own risk, actions and **Investment = XXX**.
- **A tool is not a control**: a cyber tool the target lacks fails its check until the
  analyst answers; a tool it has passes nothing.
- **The roadmap is reconciled against the change budget**, scaled by the budget's unit.
  Arithmetic on reported figures only — still not a cost model.
- The IRL page is **Information requests**; the workbook keeps the name IRL.
- **Business processes have findings too** (2026-11-19): three process-agnostic rules in
  `reference/processes/_findings.yaml`, computed on read and editable. They replace the
  report's single process row. Every register's edits live in one table and reach both the
  findings export (`/findings/export.xlsx`, `/findings/{register}/export.xlsx`) and the report.

**Phase 9+ — not planned.** Evidence collection beyond the drive scan, multi-user auth,
email reminders.

**Reference documents:**
- `docs/reference/DD_ASSESSMENT_FRAMEWORK.md` — how findings are made (observation → theme),
  the deal-impact lens, the severity rule, and the source of every assessment question.
- `docs/PROJECT_LOG.md` — decisions, deviations, known gaps, bugs worth remembering.
  **Read this first in a new session.**
- `docs/reference/DD_master.md` — the domain authority, built from Roehl-Anderson,
  *M&A Information Technology Best Practices* (Wiley, 2013). `[EXT]` marks modern
  practice added by us; `[DATED]` marks content needing modernising. That distinction
  survives into the product's output.
- `docs/reference/KPMG_SOW_LANGUAGE.md` — the house scope-of-work voice, transcribed
  verbatim from the KPMG source deck. This is what the generated document must sound
  like.
- `docs/reference/{P2P,O2C,P2M,H2R,R2R}_AUTOMATION_MODEL.md` — the Assess module's five
  evaluation references: each process's step decomposition, its weights, and the 0-5
  maturity ladder the scoring reads. The ladder, arithmetic and banding are identical
  across all five; the steps, weights, per-level evidence and shapes differ, and **so does
  the weighting principle** — §1 of each says what kind of process it is and why that
  changes what the assessment looks for. All `[EXT]` — built for this platform, and
  calibrations to be tuned, not authorities. Each §7 records what was searched for in
  `DD_master.md` and what was not found, rather than implying provenance it does not have.

## 10. Working agreements

- Read `docs/PROJECT_LOG.md` first — it records the decisions that override the phase
  specs, the known gaps, and the bugs worth not repeating.
- If a phase spec conflicts with this file, this file wins. If a later instruction from
  Rishi conflicts with either, that wins — and say so rather than silently choosing.
- Plan first, then build. Show the plan for approval before large file changes.
- Ask before inventing product decisions that aren't covered here (extra fields,
  new routes, auth). Small implementation details: decide and note it.
- After each phase of work: run lint, run tests, confirm both servers start cleanly,
  **and generate a scope and read it** — several real bugs passed their tests.
- Update `README.md` whenever setup steps change, and add an entry to
  `docs/PROJECT_LOG.md` whenever a decision, deviation or known gap changes.
