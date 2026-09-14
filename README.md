# KPMG Tech Diligence Tool

A Technology Due Diligence intake and scope-of-work platform. An analyst captures the
transaction through a six-step intake; the platform derives a tailored, defensible
scope of work from it.

**Picking this up mid-project?** Read `docs/PROJECT_LOG.md` first — it records the
decisions that override the phase specs, the known gaps, and the state of things.

`CLAUDE.md` is the project constitution. `docs/reference/DD_master.md` is the domain
authority; `docs/reference/KPMG_SOW_LANGUAGE.md` is the house scope-of-work voice.

## What it does

**Phase 1 — intake.** A routed application and a fully persisted six-step intake:
Deal Context, Rationale, Deal Structure, Target Company, Technology Profile, and
Objectives & Logistics. Autosaves as you type; resumable by URL.

**Phase 2 — the scope engine.** A filed intake becomes a scope of work:

- **Rules decide coverage.** 37 encoded rules from `docs/reference/DD_master.md` §15 (26 active, 10
  dormant, 1 disabled) pick which KPMG scope areas open and at what depth. Every
  decision carries the rule id and page citation that produced it.
- **The model writes the prose.** With `SCOPE_GENERATOR=llm`, Gemini rewrites the
  wording so it names the target's actual stack, systems and thesis — inside a
  document the rules already fixed. It cannot add, remove or re-tier an area; any
  deviation is rejected and the deterministic scope ships instead.
- **Everything is auditable.** Classification, signals, tier reasoning, exclusions and
  a provenance footer, all exportable to Markdown.
- **Three exports, deliberately different.** Markdown is the internal artefact and
  carries the whole audit trail. **Download PPT** (the primary deliverable — a scope of
  work is normally circulated as a deck) and **Download PDF** produce the client-facing
  document: the same scope, sequencing, cost, team and exclusions, but without the
  signals and rule provenance. See `docs/PROJECT_LOG.md` before changing what any of
  them contains.

The deterministic engine produces a complete, publishable scope with the LLM entirely
disabled. The model is an improvement to the wording, never a dependency.

**Phase 3 — the request list.** A scoped engagement can produce the **Initial Request
List**: the document the buyer sends the target, listing every artefact the team needs.

- **It derives from the scope.** Each KPMG row's evidence list seeds a request, so every
  question traces back to an area the scope opened — and the list generates with the LLM
  switched off.
- **Company research informs it.** A grounded web search over the target returns a
  seven-section **business brief** — what they do, how they make money, who they sell to,
  the sector, the competition — alongside dated findings, every claim carrying real source
  links. The brief shapes the questions and the function names. If the model returns no
  sources the run is refused, not stored.
- **Excel out.** Three columns — Function, Question, Response — with Response blank for
  the client to fill and return.

**Phase 4 — tracking what arrived.** Every request carries its status, document type and
remarks, ranked Critical/High/Medium/Low. The ranking comes from the scope — security and
regulatory evidence is critical, deep-dive areas are high — so it is explainable rather
than a guess. This began as a separate checklist page; on 2026-09-09 it was folded into
the request list itself, because the shared-drive scan's findings only mean anything
beside the request they belong to. One screen: what was asked, what came back, what to
chase.

**The shared-drive scan** reads every file the client has dropped in a folder, matches it
to a request, and writes the document type, the receiving status, and — where what arrived
is only part of what was asked for — the **follow-up questions** that close the gap. It
never overwrites a status a human has set, records which files it matched so a wrong call
is visible, and only scans requests that ask for a document: a question is answered in a
meeting, not by a file appearing on a drive.

**Phase 5 — assessing the processes.** The first question a tech DD asks of an operating
business is how automated its core processes actually are — because licences reveal what
was bought, and process automation reveals what is used. The gap between the two is where
findings live.

- **All five processes are defined**: Procure to Pay (9 steps), Order to Cash (8), Plan to
  Make (8), Hire to Retire (9) and Record to Report (8). Each has its own evaluation
  reference in `docs/reference/`.
- **They are not all the same kind of process, and the weights say so.** P2P and O2C are
  transaction cycles, weighted by volume and financial exposure. Plan to Make is a decision
  cycle, weighted by the exposure each decision controls. **Hire to Retire is an identity
  lifecycle**, weighted by what breaks when a step is manual — offboarding handles almost
  no events and carries one of the heaviest weights, because a leaver whose access is never
  revoked is a live credential. **Record to Report is a periodic close**, where volume
  barely applies and the currency is days to close, manual journal count and reconciliation
  backlog.
- **Hire to Retire is the one process whose automation gap is also a security finding.**
  Joiner-mover-leaver is where access is granted and revoked, so the questionnaire asks for
  the **measured revocation lag in days**, not whether an offboarding checklist exists — a
  documented but unmeasured process scores 2, not 4.
- **A questionnaire with nudges.** Conditional follow-ups declared as data: pick an option,
  and the question that makes that answer defensible appears beneath it.
- **A deterministic 0-100 index**, banded Manual to Optimised, with the **shape** reported
  beside the number — a front-loaded 52 and a uniform 52 imply remediation costs an order
  of magnitude apart.
- **An unanswered question is never scored as zero.** A blank is an absence of evidence,
  not evidence of manual working, so it drops out of the denominator. A step with nothing
  answered drops out of the index entirely and its weight redistributes.

Adding a process is **content, not code**: a model document, a questionnaire YAML, a
registry flip and tests — no change to the ladder, the arithmetic, the banding, the API or
the frontend. The last two processes needed none, which is the evidence the claim holds.
See `docs/phases/PHASE5_PLAN.md`.

**Email reminders to the consultant** remain deliberately deferred — a frontend stub,
honestly badged "Not connected yet", with a live preview built from real counts. See
`docs/phases/PHASE4_PLAN.md`.

## Stack

- Frontend: Next.js 15 (App Router) + React 19 + TypeScript (strict) + Tailwind v4
- Backend: FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic, SQLite in dev
- LLM: Google Gemini (`google-genai`), `gemini-2.5-flash` — see the note in `CLAUDE.md` §3
- Env: a single conda environment named `techdd` with Python 3.11 and Node 20

## Setup (Windows, PowerShell)

Run these in order from the repo root (`Tech_DD/`).

```powershell
# 1. Create and activate the conda environment (Python 3.11 + Node 20)
conda env create -f environment.yml
conda activate techdd

# 2. Install backend dependencies into the activated env
pip install -r requirements.txt -r requirements-dev.txt

# 3. Install frontend dependencies
cd frontend
npm install
cd ..

# 4. Configure environment variables
copy .env.example .env
copy .env.example frontend\.env.local
```

`.env` (repo root) is read by the backend; only `NEXT_PUBLIC_API_BASE_URL` in
`frontend\.env.local` matters to the frontend. The defaults work out of the box.

### Optional: enable LLM prose tailoring

The engine runs without an API key. To have the model tailor the wording:

1. Get a free key at <https://aistudio.google.com/apikey> (no card required).
2. In `.env`, set:

   ```
   GEMINI_API_KEY=your-key-here
   SCOPE_GENERATOR=llm
   ```

An absent or invalid key is not an error: the generator falls back to the
deterministic scope with a logged warning, and the payload records which happened
(`llm`, `rules (llm tailoring rejected)`, `rules (llm error)`, `rules (llm unavailable)`).

`.env` is gitignored. Never commit a key.

### Optional: point the shared-drive scan at a folder

The request list can walk the folder a client drops documents into, match each file to a
request, and write the document type, the receiving status and any follow-up questions.
It defaults to the local test fixture:

```
SHARED_DRIVE_ROOT=../shared-drive/project-kiln
```

A relative path resolves against the repo root, because the backend runs from `backend/`.
At deployment set an absolute path to the real share. **The scan is read-only** — it never
writes to, moves or deletes anything on the drive.

Without `GEMINI_API_KEY` the scan still runs, matching on filenames alone. It then cannot
judge completeness, so it never reports "received partially" and writes no follow-up
questions; the response's `generator` field says `rules` rather than `llm`, and the UI
says so too. A full scan of ~26 files takes 45-60 seconds, because every shortlisted
request is judged individually.

## Run the app

Every command assumes the `techdd` environment is activated (`conda activate techdd`).

**Backend** (from `backend/`):

```powershell
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

API at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

**Frontend** (from `frontend/`, second terminal, `techdd` still activated so it uses
the conda-installed Node 20):

```powershell
cd frontend
npm run dev
```

App at `http://localhost:3000`.

Click **Start an intake**, work through the six steps, then **File engagement**. The
scope page offers **Generate scope**, and the result can be regenerated (each run is a
new version, prior versions are never destroyed), downloaded as a client-facing PPT or
PDF, or exported to Markdown with the full audit trail.

## Tests and quality gates

Backend (from `backend/`):

```powershell
pytest                 # 300 tests
ruff check .
mypy app
black --check .
```

Frontend (from `frontend/`):

```powershell
npm run typecheck
npm run lint
npm run test           # vitest
npm run test:e2e       # Playwright — needs both dev servers running
                       # (first run: npx playwright install chromium)
```

The test suite never calls the live LLM API. `tests/conftest.py` pins
`SCOPE_GENERATOR=rules` before config import and fails any test that constructs a real
client; the LLM layer is covered by mocked tests in `tests/test_llm.py`.

## How the scope engine is put together

```
IntakeFull
  → SignalExtractor    services/scope/signals.py    rules → signals, with citations
  → MixScorer          services/scope/scoring.py    mix 0-100, band, confidence
  → ModuleSelector     services/scope/selection.py  which KPMG rows open
  → DepthCalibrator    services/scope/depth.py      caps, floors, trade-offs
  → KpmgScopeComposer  services/scope/composer.py   the document
  → LlmScopeGenerator  services/scope/llm.py        prose only, validated + fallback
```

**Content lives in data, not code.** A practitioner can edit any of these without
touching Python:

| File | What it holds |
| --- | --- |
| `backend/app/reference/kpmg_scope/product.yaml` | The 10 Product DD objectives, verbatim |
| `backend/app/reference/kpmg_scope/enterprise.yaml` | The 9 Enterprise IT focus areas, verbatim |
| `backend/app/reference/scope_rules.yaml` | All 37 rules, weights and citations |
| `backend/app/services/scope/prompts/tailoring.md` | The LLM prompt, versioned |

All are validated at startup; a malformed file fails loudly rather than producing a
quietly wrong scope.

## Database

SQLite in dev, at `backend/techdd.db` (gitignored). To reset:

```powershell
cd backend
del techdd.db
alembic upgrade head
```

For Postgres, set `DATABASE_URL` in `.env` and re-run `alembic upgrade head`.

## Repository layout

See `CLAUDE.md` §4 for the fully annotated layout.

```
Tech_DD/
├── docs/
│   ├── PROJECT_LOG.md    running log of decisions, gaps and state
│   ├── phases/           the Phase 1 and Phase 2 plans and specs
│   └── reference/        DD_master, the KPMG source deck and house voice
├── assets/               brand assets
├── backend/              FastAPI app, scope engine, YAML libraries, Alembic, pytest
└── frontend/             Next.js app, components, zod schemas, vitest + Playwright
```

## Known gaps

Recorded honestly rather than left to be discovered:

- **The shared-drive scan's matching is a calibration, not a solved problem.** Filename
  and folder overlap shortlists candidates; the model decides. On the Kiln fixture 26 of
  35 document requests shortlist, and the model correctly rejects the wrong candidates —
  but a request whose wording shares no distinctive words with the filename will not
  shortlist at all, and is left `not_received` rather than guessed at. Files nothing
  claimed are reported as `unmatched_files` so the gap is visible from either side.

- **The "Archived" status filter never returns anything.** `list_engagements` excludes
  archived rows before applying the filter, and `get_engagement` 404s on them, so an
  archived engagement is invisible and unrecoverable. Delete from the engagements table
  is permanent and works on any status; archiving is best avoided until this is fixed.
- **10 of 37 rules are dormant.** They depend on intake fields that were deliberately
  not added (`deal_type`, `perspective`, `integration_model`, `relative_size`,
  `it_landscape_complexity`, `shared_with_parent`, `management_access`) or removed
  (`code_access`, `carve_out_or_tsa`, `investor_type`). They record an "unknown"
  signal that is reported in the scope, never an error. Adding the fields activates
  them with no code change.
- **Rule D1 is disabled** and acceptance criterion G2 is correspondingly narrowed to
  `access_level` only, because `code_access` is not captured. See `scope_rules.yaml`.
- **"Let the platform decide" is the weakest classification path.** Rules A1 and M6
  were re-sourced to `dd_type_preference` on 2026-08-31 when the redundant
  "Is the software the product?" question was removed from the intake. With no declared
  archetype they stay silent by design, so the computed mix rests on digital maturity,
  build-vs-buy and engineering share alone. A deliberate trade, pinned by
  `test_platform_decide_still_classifies_from_the_evidence`.
- **Mix weights are a starting calibration.** `docs/reference/DD_master.md` §15.1 flags them as
  needing tuning against real engagements. The golden-case tests in
  `tests/test_golden_cases.py` are what make tuning safe — change a weight, and the
  case that no longer holds tells you what you broke.
