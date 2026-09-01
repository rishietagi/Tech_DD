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
4. **Initial Request List (IRL)** — from the scope, produce the list of artefacts the
   target must supply, grouped by business function and exported to Excel for the
   client to complete. Built in Phase 3 — see §9.
5. **Execution & reporting** — run the workstreams, collect findings, produce the
   report. *(Phase 4+, not planned yet.)*

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
| LLM (Phase 2) | **Google Gemini** (`google-genai`), model `gemini-2.5-flash` — see note below |
| ORM / DB | SQLAlchemy 2.0 (declarative, typed) + Alembic; SQLite in dev, Postgres in prod via `DATABASE_URL` |
| PDF export | **ReportLab** (`reportlab` + `pillow`) — pure Python, no system libraries |
| PPT export | **python-pptx** — pure Python. The primary client-facing artefact: a SOW is normally circulated as a deck |
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
│   ├── phases/
│   │   ├── PHASE1_PLAN.md     # Phase 1 build plan (intake)
│   │   ├── PHASE2_SPEC.md     # Phase 2 build spec (scope engine)
│   │   ├── PHASE2_PROMPT.md   # the Phase 2 handoff prompt
│   │   └── PHASE3_PLAN.md     # Phase 3 build plan (IRL + research)
│   └── reference/
│       ├── DD_master.md       # the domain authority (Roehl-Anderson 2013)
│       ├── KPMG_SOW_LANGUAGE.md  # house scope-of-work voice, from the source deck
│       │   # (the source PDF is gitignored — client-confidential, local only)
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
│   │   │                      #   composer, llm, export, export_pdf,
│   │   │                      #   export_pptx + prompts/
│   │   ├── irl/               # seeds, composer, llm, export_xlsx + prompts/
│   │   └── research/          # grounded web search + prompts/
│   │   └── reference/         # enums + kpmg_scope/*.yaml + scope_rules.yaml
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

**One rule-sourcing change worth knowing before you touch scoring** (2026-08-31): the
Technology Profile's "Is the software the product?" question was removed as redundant
with `dd_type_preference`, and rules **A1** (mix +35) and **M6** (W-PROD at Tier ≥ 2)
now read the declaration instead. Consequence: under "Let the platform decide" both are
silent by design and the computed mix rests on A2/A5/A6. Do not reintroduce the intake
field — tune those weights instead. Full reasoning in `docs/PROJECT_LOG.md`.

**Phase 3 — BUILT.** The Initial Request List and company research. The IRL derives from
the scope: every KPMG row's `evidence` list seeds a request, so each question traces to a
scope area a rule opened and the list generates with the LLM off. Research is a grounded
web search that **refuses rather than fabricating** — no grounding metadata, no stored
run — and feeds the IRL so its questions and function names fit the actual business. Plan
at `docs/phases/PHASE3_PLAN.md`.

**Each deliverable is its own versioned child table** hanging off `engagements`
(`scope_of_work`, `information_request_list`, `company_research`, plus `irl_response`).
Adding a module later is one more table + service + router — do not reshape what exists.

**Phase 4+ — not planned.** Execution, evidence collection, findings, reporting,
multi-user auth.

**Reference documents:**
- `docs/PROJECT_LOG.md` — decisions, deviations, known gaps, bugs worth remembering.
  **Read this first in a new session.**
- `docs/reference/DD_master.md` — the domain authority, built from Roehl-Anderson,
  *M&A Information Technology Best Practices* (Wiley, 2013). `[EXT]` marks modern
  practice added by us; `[DATED]` marks content needing modernising. That distinction
  survives into the product's output.
- `docs/reference/KPMG_SOW_LANGUAGE.md` — the house scope-of-work voice, transcribed
  verbatim from the KPMG source deck. This is what the generated document must sound
  like.

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
