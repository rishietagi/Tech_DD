# CLAUDE.md — Tech DD Platform

Project constitution. Read this file **and** `initial_plan.md` before writing any code.
Rishi edits this file; treat it as authoritative over your own preferences.

---

## 1. What this product is

An end-to-end **Technology Due Diligence** platform for investors (PE, VC, corporate
acquirers, family offices).

The flow the product owns:

1. **Intake** — capture the transaction: deal context, rationale, structure
   (strategic vs financial, majority vs minority), investor details, investor
   objectives, target company details, target technology profile, engagement
   logistics.
2. **Scope of Work generation** — from that intake, produce a tailored technical
   diligence scope: which workstreams open, at what depth, what evidence is
   requested, what the key questions are. *(Phase 2 — see §9. Do not build the
   generation logic in Phase 1.)*
3. **Execution & reporting** — run the workstreams, collect findings, produce the
   report. *(Phase 3+, not planned yet.)*

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
- **Deal stage & access level** → determine depth (red-flag vs confirmatory) and
  whether code-level review is even possible.

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

**LLM provider — recorded deviation (2026-08-30).** `PHASE2_SCOPE_ENGINE.md` §8 and
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
├── CLAUDE.md                  # this file
├── initial_plan.md            # the build plan
├── README.md                  # setup + run instructions
├── .gitignore
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
│   │   ├── api/v1/            # router.py + routes/{engagements,intake,scope,meta}.py
│   │   ├── services/          # business logic — routes stay thin
│   │   └── reference/         # seed data: sectors, workstream library, enums
│   ├── alembic/
│   └── tests/
└── frontend/
    ├── package.json  next.config.ts  tsconfig.json  tailwind.config.ts
    └── src/
        ├── app/               # routes (see initial_plan.md §4)
        ├── components/        # ui/ (primitives) + intake/ + engagement/
        ├── lib/               # api client, zod schemas, store, formatting
        ├── types/             # shared TS types mirroring backend schemas
        └── styles/            # tokens.css + globals.css
```

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

The v0 single-file mockup is preserved at `reference/mockup_v0.html` as a
**visual** reference for the toggle cards, ledger rail, stamp and cover sheet.
Read it for the look; ignore its architecture entirely.

Load fonts with `next/font/google`, not `<link>` tags. Keep the motifs that carry
meaning: section numbering (`§01`), the ledger/progress rail, the status stamp
(Draft → In Progress → Ready to File → Filed), the confirmation "cover sheet".

---

## 9. Phasing — what is in scope right now

**Phase 1 (build this now):** the full routed application shell and the complete
intake experience, persisted end to end. Every screen real, every field real, data
saved to and read from the API. The Scope-of-Work screen is built as a real route
that renders a scope returned by the API — but the API returns a clearly-marked
**deterministic placeholder** scope. See `initial_plan.md`.

**Phase 1 status: BUILT** (commit `feat: Phase 1 Tech DD platform`). The routed app,
the eight-step intake and the placeholder scope are in place.

**Phase 2 (build when instructed):** the actual SOW derivation engine — signal
extraction, Enterprise/Product mix scoring, workstream module library, LLM
narrative tailoring. Rishi will explicitly say when to start this. Phase 1 must
leave a clean seam for it: a single `ScopeGenerator` service interface behind
which the placeholder sits, so Phase 2 is a swap, not a rewrite.

**Phase 3+ (not planned):** execution, evidence collection, findings, reporting,
export, multi-user auth.

If a Phase-1 task tempts you into Phase-2 logic, stop and leave a `TODO(phase-2)`
comment instead.

**Phase 2 reference documents (read both before touching the scope engine):**
- `DD_master.md` — the technology due diligence domain authority: process, workstream
  library, decision rules, benchmarks and provenance conventions. Built from
  Roehl-Anderson, *M&A Information Technology Best Practices* (Wiley, 2013).
  Content marked `[EXT]` is modern practice added by us, not sourced; content marked
  `[DATED]` is in the book but needs modernising. That distinction must survive into
  the product's own output.
- `PHASE2_SCOPE_ENGINE.md` — the build spec for the engine.
- `PHASE2_PROMPT.md` — the handoff prompt for that phase.

---

## 10. Working agreements

- Read `initial_plan.md` fully before the first file. If something in it conflicts
  with this file, this file wins — and say so rather than silently choosing.
- Plan first, then build. Show the plan for approval before large file changes.
- Ask before inventing product decisions that aren't covered here (extra fields,
  new routes, auth). Small implementation details: decide and note it.
- After each phase of work: run lint, run tests, confirm both servers start
  cleanly, then commit.
- Update `README.md` whenever setup steps change.
