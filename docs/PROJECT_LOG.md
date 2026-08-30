# PROJECT_LOG.md

**Running log of decisions, deviations and state. Maintained by Claude; read this
first when picking the project up in a new session.**

Newest entries at the top. Each entry records what changed, *why*, and anything a
future session would otherwise get wrong.

---

## Current state — 2026-08-31

| | |
|---|---|
| **Phase 1 (intake)** | Done, committed, pushed |
| **Phase 2 (scope engine)** | Done, **not yet committed** |
| **Phase 3+** | Not started, not planned |
| **Backend** | pytest 204/204 · ruff clean · mypy clean (51 files) |
| **Frontend** | tsc clean · eslint clean · vitest 19/19 |
| **API** | 13 routes, OpenAPI clean |
| **Git** | `master`, remote `origin` = `git@github.com:rishietagi/Tech_DD.git` |

**Uncommitted:** the entire Phase 2 engine plus this restructure. Rishi does all
committing and pushing — never run `git push`.

### Run it

```powershell
conda activate techdd
cd backend && alembic upgrade head && uvicorn app.main:app --reload   # :8000
cd frontend && npm run dev                                            # :3000
```

`.env` at the repo root holds `GEMINI_API_KEY` and `SCOPE_GENERATOR`. Currently set to
`llm`, so every generation makes a real Gemini call (free tier).

---

## How the thing actually works

```
IntakeFull
  → SignalExtractor    signals.py      37 rules → signals, each with a citation
  → MixScorer          scoring.py      mix 0-100, band, confidence
  → ArchetypeResolver  scoring.py      user's declaration overrides, both retained
  → ModuleSelector     selection.py    which KPMG rows open, at what base tier
  → DepthCalibrator    depth.py        access caps, timeline gates, effort trade-offs
  → KpmgScopeComposer  composer.py     assembles the document
  → LlmScopeGenerator  llm.py          prose only; validated, falls back on any failure
```

**The load-bearing idea:** rules decide *coverage* (auditable, citable); the model
writes *prose* (specific, KPMG-voiced). The deterministic engine alone produces a
complete, publishable scope — the model is an improvement, never a dependency.

**Content lives in YAML, not Python.** A practitioner edits these without a developer:

- `backend/app/reference/kpmg_scope/product.yaml` — 10 Product DD objectives, verbatim
- `backend/app/reference/kpmg_scope/enterprise.yaml` — 9 Enterprise IT focus areas, verbatim
- `backend/app/reference/scope_rules.yaml` — all 37 rules, weights, citations
- `backend/app/services/scope/prompts/tailoring.md` — the LLM prompt, versioned

All validated at startup; a malformed file fails loudly.

---

## Decisions that override the specs

These were Rishi's calls. **Do not "fix" them back.** `CLAUDE.md` outranks
`docs/phases/PHASE2_SPEC.md`, and a later instruction outranks both.

### LLM provider is Gemini, not Anthropic (2026-08-30)

`PHASE2_SPEC.md` §8 specifies the Anthropic Messages API. Rishi is not paying for API
credits — a Claude Pro subscription does not include them — and Gemini has a free tier.
Now `google-genai`, model `gemini-2.5-flash`, key `GEMINI_API_KEY` from
aistudio.google.com/apikey. Recorded in `CLAUDE.md` §3. Swapping back means rewriting
`services/scope/llm.py` and re-pinning; nothing else depends on it.

*Note: Rishi's key starts `AQ.` rather than the `AIza` I expected. It works. I was
wrong to doubt it — Google has a newer key format.*

### Not a fixed skeleton (2026-08-30)

Rishi explicitly rejected the spec's framing where the LLM only fills prose into fixed
slots. Settled split: rules decide which areas open and at what depth; the LLM authors
the entire readable document. Structure is still enforced — the model cannot add,
remove or re-tier a row, and any deviation is rejected.

### Output uses KPMG's taxonomy, not DD_master's (2026-08-30)

The client-facing scope uses the headings from
`docs/reference/KPMG_SOW_LANGUAGE.md` — Product: 10 numbered `Objective` → `Scope of
Work` rows; Enterprise: 9 `Focus Area` → `Key considerations` groups. DD_master's 12
workstreams are the *internal* rule layer feeding the audit trail.

### Intake was deliberately trimmed (2026-08-30)

Rishi cut the intake from 8 steps to 6 and made almost everything optional. Removed:
the whole Investor step (firm name folded into Deal Context), `code_access`,
`carve_out_or_tsa`, `revenue_model`, `clean_team_constraints`, and the 100-day-plan and
cost-model deliverable formats. `dd_type_preference` was removed and then **re-added**
once the engine needed a user-declared archetype.

Only `target.sector` and `target.line_of_business` are required to file.

Rishi on code access: *"remove code access we will not need that to generate scope of
work anything code related we wont be using."*

### The §9.3 intake fields were declined (2026-08-30)

`PHASE2_SPEC.md` §9.3 asks for seven new fields (`deal_type`, `perspective`,
`integration_model`, `relative_size`, `it_landscape_complexity`, `shared_with_parent`,
`management_access`). Rishi chose not to add them, accepting reduced rule coverage for
a leaner form.

---

## Known gaps — deliberate, not bugs

**10 of 37 rules are dormant** (A7, A8, M4, D3, D9, D10, C2, C3, C4, C7). Their input
fields are not on the intake. They emit an "unknown" signal that is *reported* in the
scope's exclusions and confidence reasons, never an error. Adding the fields activates
them with no code change.

**Rule D1 is disabled** — it depended on `code_access`. Acceptance criterion **G2 is
therefore narrowed** to `access_level` only, and must be reported as *modified*, never
as met as written.

**Mix weights are a starting calibration.** `DD_master.md` §15.1 flags them as needing
tuning against real engagements. `tests/test_golden_cases.py` is what makes tuning
safe — change a weight, and the case that breaks tells you what you broke.

---

## Bugs found and fixed (worth remembering)

These all passed their tests while being wrong. Recorded so the same traps get checked
next time.

| Bug | How it hid |
|---|---|
| **Row overrides silently discarded** | `dict(payload)` is a *shallow* copy, so mutating a nested row edited the loaded value in place; SQLAlchemy saw no change and dropped the write. Endpoint returned 200. Fixed with `deepcopy` + `flag_modified`. Only caught because a test re-fetched from the API instead of trusting the response. |
| **Tests calling the live Gemini API** | `SCOPE_GENERATOR=llm` in `.env` meant API tests hit the network — slow, billable, non-deterministic. Suite took 52s. `conftest.py` now pins `rules` before config import and fails any test constructing a real client. Now 2.2s. |
| **Mix saturated to 0/100** | Raw deltas totalled +105/−70, so every realistic engagement clamped to an extreme and the "blended" band was unreachable. Added `damping: 0.55`. |
| **Confidence pinned to "low"** | The 10 dormant rules penalised *every* engagement identically, shifting the scale rather than discriminating. Now reported, not scored. |
| **Effort model assumed one person** | An 8-week engagement was being stripped to screens. A DD team is 3-4 people; `_DAYS_PER_WEEK` is 15. |
| **Objective boost lifted everything** | Matching *any* workstream meant one broad objective raised nearly every row. Now matches the row's *primary* workstream. |

**Lesson worth keeping:** several of these were found by *running the thing and reading
the output*, not by tests passing. Generate a scope and read it before declaring a step
done.

---

## Session log

### 2026-08-31 — Confidential PDF removed from tracking

The KPMG source deck (`docs/reference/KPMG Product and Enterprise Tech DD scope
v1.1.pdf`) is client-confidential and was being tracked. Removed from git tracking
(`git rm --cached`), added `*.pdf` to `.gitignore`, and backed the file up to
`Desktop\KPMG-scope-deck-BACKUP.pdf`. **The file is still on disk at its original
path** — only git no longer tracks it.

**Known and accepted exposure.** The PDF remains in commits `451ddac` and `61399a6`,
both already pushed to the **public** GitHub repo, so it is still recoverable via
`git show 451ddac:<path>`. Rishi chose "remove going forward only" over a history
rewrite; a full purge would need `git filter-repo` plus a force-push, which `CLAUDE.md`
§6 forbids Claude from performing.

The deck's *content* also remains public and tracked, by Rishi's explicit decision:
`docs/reference/KPMG_SOW_LANGUAGE.md` and `backend/app/reference/kpmg_scope/*.yaml`
carry all 19 objectives and focus areas verbatim. He judged the wording itself
non-sensitive. Those files are load-bearing — the engine reads the YAMLs at startup —
so do not remove them without replacing the loader.

**If this needs to change later:** making the repo private (GitHub → Settings → Danger
Zone → Change visibility) covers the PDF in history *and* the transcribed content in
one step, with no history rewrite.

### 2026-08-31 — Restructure and documentation

Reorganised a cluttered root into `docs/` and `assets/`, all moves via `git mv` so
history survives. Rewrote every internal reference (18 files). Created this log.

Restored `docs/reference/KPMG Product and Enterprise Tech DD scope v1.1.pdf` — it was
committed but missing from disk, so `git checkout` brought it back rather than losing
the source document.

### 2026-08-30 — Phase 2, steps 1-10

Built the scope engine end to end across ten numbered steps: intake field, KPMG YAML
library, rules + SignalExtractor, scoring/selection/depth, schema v2 + composer +
golden cases, API surface, scope page + live SignalPanel + methodology page, the LLM
layer, Markdown export, and the final check pass.

Verified live: `generator: llm`, schema v2, 10 tailored rows naming the target's real
stack (Python/Django, Postgres, Kafka, AWS) and its actual 5x-volume thesis. All seven
structural-integrity checks passed — the model changed nothing it wasn't allowed to.

Acceptance criteria: **9/9, with G2 marked modified** (see Known gaps).

### 2026-08-30 — KPMG rebrand and intake trim

Blue/white theme, left sidebar nav, standalone welcome screen, Manrope + Inter, every
sharp corner rounded. Intake cut to 6 steps, everything optional bar two fields.

### 2026-08-28 — Phase 1

Routed Next.js app, eight-step intake persisted end to end, placeholder scope behind
the `ScopeGenerator` seam. Committed and pushed.

---

## Working agreements

- **Rishi commits and pushes. Never run `git push`.**
- Read `CLAUDE.md` first; it outranks the phase specs. A later instruction from Rishi
  outranks everything.
- When a spec conflicts with an instruction, say so rather than silently picking.
- Content changes go in YAML, not Python.
- Never call the live LLM API from a test.
- After each step: run the checks, *and generate a scope and read it*.
