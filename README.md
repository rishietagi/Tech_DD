# Tech DD Platform

A Technology Due Diligence intake and scoping platform for investors (PE, VC,
corporate acquirers, family offices). See `CLAUDE.md` for the project
constitution and `initial_plan.md` for the Phase 1 build plan.

**Phase 1** (this build) ships the full routed application and the complete,
persisted eight-step intake, plus a `/engagements/{id}/scope` route that renders
a clearly-labelled **placeholder** scope of work. The real scope-derivation
engine is Phase 2 and is not built yet — see `initial_plan.md` §10.

## Stack

- Frontend: Next.js 15 (App Router) + React 19 + TypeScript (strict) + Tailwind v4
- Backend: FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic, SQLite in dev
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
`frontend\.env.local` matters to the frontend. The defaults in `.env.example`
work out of the box for local development.

## Run the app

Every command below assumes the `techdd` conda environment is activated
(`conda activate techdd`).

**Backend** (from `backend/`):

```powershell
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

Serves the API at `http://localhost:8000` and interactive docs at
`http://localhost:8000/docs`.

**Frontend** (from `frontend/`, in a second terminal — still with `techdd`
activated so it uses the conda-installed Node 20):

```powershell
cd frontend
npm run dev
```

Serves the app at `http://localhost:3000`.

Open `http://localhost:3000`, click **Start an intake**, and the intake wizard
walks through all eight steps, autosaving to the backend as you go. Filed
engagements appear at `/engagements`.

## Tests and quality gates

Backend (from `backend/`):

```powershell
pytest
ruff check .
mypy app
black --check .
```

Frontend (from `frontend/`):

```powershell
npm run typecheck
npm run lint
npm run test          # vitest
npm run test:e2e       # Playwright smoke test — needs both dev servers running
                        # (first run: npx playwright install chromium)
```

## Database

SQLite in dev, at `backend/techdd.db` (gitignored). To reset it:

```powershell
cd backend
del techdd.db
alembic upgrade head
```

To point at Postgres instead, set `DATABASE_URL` in `.env` and re-run
`alembic upgrade head`.

## Repository layout

See `CLAUDE.md` §4 for the full annotated layout.

```
Tech_DD/
├── backend/    FastAPI app, SQLAlchemy models, Alembic migrations, pytest
└── frontend/   Next.js app, components, zod schemas, vitest + Playwright
```

## Notes for Phase 2

The scope-of-work generation engine (signal extraction, Enterprise/Product mix
scoring, workstream selection) is intentionally not built. The seam is
`backend/app/services/scope/base.py` (`ScopeGenerator` protocol), currently
implemented only by `PlaceholderScopeGenerator`. See `initial_plan.md` §10.
