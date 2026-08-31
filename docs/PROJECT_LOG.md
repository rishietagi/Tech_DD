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
| **Phase 2 (scope engine)** | Done, committed (`62ac027`, `61399a6`) |
| **Phase 3+** | Not started, not planned |
| **Backend** | pytest 242/242 · ruff clean · mypy clean (53 files) |
| **Frontend** | tsc clean · eslint clean · vitest 19/19 · `next build` clean |
| **API** | 15 routes, OpenAPI clean |
| **DB** | at `0002_drop_tech_is_product` |
| **Git** | `master`, remote `origin` = `git@github.com:rishietagi/Tech_DD.git` |

**Uncommitted:** the UI fixes and the `tech_is_product` removal below. Rishi does all
committing and pushing — never run `git push`.

**Pre-existing, not introduced here:** `black --check` reports 13 backend files needing
reformatting. This is true on a clean checkout of `1848ec2` as well — it was not caused
by the current changes and was left alone rather than folded into an unrelated diff.
`ruff` and `mypy` are both clean.

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

### `tech_is_product` removed as redundant (2026-08-31)

Rishi: *"we ask this question if software is the product yes or no in technology
profile, but isnt this question redundant as we are asking for the engagement to be
product or enterprise in objective and logistics"* — correct, and it is now gone from
the intake.

The overlap was real but not total, so the fix was not a plain deletion. The field fed
two rules, one of them the heaviest in the engine:

| Rule | Was | Now |
|---|---|---|
| **A1** | `tech_is_product = yes` → mix **+35** | `dd_type_preference = Product Tech DD` → mix +35 |
| **M6** | `tech_is_product ∈ {yes, partly}` → W-PROD Tier ≥ 2 | `dd_type_preference ∈ {Product Tech DD, Blended}` → W-PROD Tier ≥ 2 |

Weights and page citations are unchanged; only the input moved. Declaring "Product Tech
DD" is a *stronger* statement of the same fact than the removed question was.

**The trade, stated plainly.** `dd_type_preference` is an override — it decides which
deck ships — while the mix decides which rows open and at what tier *within* that deck.
Under **"Let the platform decide"** no declaration exists, so A1 and M6 are now silent
by design and the computed mix rests on A2 (digital-native), A5 (in-house build) and
A6 (engineering share). That path is weaker than it was. It still classifies correctly
on ordinary evidence — `test_platform_decide_still_classifies_from_the_evidence` pins
this: G1's shape without a declaration still computes product at mix ≥ 66. If it ever
needs strengthening, the lever is A2/A5/A6 weights in `scope_rules.yaml`, not a new
intake field.

**G6's confidence moved `high` → `medium`, and that is correct.** G6 is G1 with the
declaration flipped to "Enterprise IT DD". A1 used to fire off `tech_is_product`
regardless of the declaration, so G6 scored the same four signals as G1. A1 now reads
the declaration, so on G6 it correctly does not fire, leaving `[A2, A5, A6]` — 3
signals, weight 50, the same profile that rates G2 "medium". G6 is precisely the case
where the user contradicts the evidence, which is when the engine *should* report less
confidence, not the same confidence as when they agree. The golden-case snapshot did
its job: it caught the change and named it.

**Also changed:** the Technology Profile step's hint no longer claims to be where
Enterprise vs Product is decided — it isn't, and hasn't been since `dd_type_preference`
was re-added. Migration `0002_drop_tech_is_product` strips the key from stored
`technology_json` (4 existing rows migrated); it must be stripped rather than ignored
because the section schemas are `extra="forbid"` and a stale key would fail validation
on the next read. The migration's `downgrade()` is a documented no-op — the answers are
not retained anywhere, and the field was optional in every version that had it.

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

**The "Archived" status filter returns nothing, ever.** `list_engagements` excludes
archived rows *before* applying the status filter, so the dropdown option ANDs two
contradictory conditions; `get_engagement` also 404s on archived. An archived engagement
is invisible and unrecoverable through the API. Found 2026-08-31 while adding the delete
button — pre-existing, documented, not yet fixed. Fix both together or archiving stays a
one-way disappearance.

**"Let the platform decide" is the weakest classification path**, since A1 and M6 were
re-sourced to `dd_type_preference` (2026-08-31). With no declaration, the computed mix
rests on A2/A5/A6 alone. This is a deliberate trade for removing a redundant question,
not an oversight — see the decision entry above. Tune A2/A5/A6 if it needs
strengthening; do not reintroduce the intake field.

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

### 2026-08-31 — Delete button on the engagements table

A **Delete** action on every row of the engagements table, backed by
`DELETE /engagements/{id}?permanent=true`.

**The endpoint was already misleading.** `DELETE /engagements/{id}` called
`archive_engagement` — a *soft* delete that sets status to `archived`. Rishi asked to
"delete from database", so permanent removal is now available behind `?permanent=true`.
Archiving stays the default so any existing caller keeps the behaviour it had.

Deletion cascades: `intake`, `denorm` and every `ScopeOfWork` version go with the
engagement, because all three relationships are `cascade="all, delete-orphan"`.
`test_permanent_delete_takes_the_children_with_it` checks the child tables directly
rather than trusting the 204.

**A guardrail was added and then removed, on Rishi's call.** The first version refused
to delete a `filed` or `scoped` engagement (409) and required archiving first. That
turned out to be **unreachable from the UI** because of the bug below, so Rishi chose to
allow deleting any status directly. The confirmation dialog is the only guard: it names
the deal and states that the intake and every scope version go with it. `Cancel` is
verified to destroy nothing.

`delete_engagement` deliberately does **not** use `get_engagement`, which treats an
archived row as a 404 — an already-archived engagement must still be deletable.

### Known bug, found here, deliberately not fixed

**The "Archived" status filter can never return anything.** `list_engagements` starts
with `where(Engagement.status != archived)` and *then* applies the status filter, so
selecting "Archived" in the dropdown ANDs two contradictory conditions. Combined with
`get_engagement` treating archived as a 404, an archived engagement is completely
invisible: not in the list, not fetchable by id, not restorable.

Archiving is therefore a **one-way disappearance** from the UI. That is why the
archive-first delete flow could not work, and why the Archive button was dropped from
the table rather than shipped as a trap.

Fixing it means letting `list_engagements` include archived rows when the caller asks
for them explicitly, and relaxing `get_engagement`. Left alone for now because it is
pre-existing and outside what was asked for — but it should be fixed before anyone
relies on archiving.


### 2026-08-31 — Review round: required markers, field help, AI-heavy stub, two-pass sequencing, PPT export

Six pointers from Rishi's review. All done.

**1. Required fields are marked.** `Field` gained a `required` prop rendering a red
asterisk with an `sr-only` "(required)" for screen readers. Only **two** fields carry
it — `target.line_of_business` and `target.sector` — because those are the only two the
backend actually enforces (`SECTION_REQUIRED_MODELS`). Marking anything else would be a
lie the API would not back up.

**2. Every intake field explains how it is used.** Hints on all six steps, written from
`scope_rules.yaml` rather than invented: a field that drives a rule names it and its
weight ("Rules A4/A5 — in-house pulls the mix toward Product (+15)"), and a field that
does not is honest about it ("Context only. Not currently a scoring rule."). That
distinction matters — it tells a user which answers actually change the output.

**3. AI-heavy Tech DD is a working stub.** Fourth card in step 06, persisted to the
intake and surviving a reload. `_PREFERENCE_TO_TYPE` in `scoring.py` deliberately omits
it, so it applies no override and the engagement classifies from the computed mix
exactly as "Let the platform decide" would. The lookup uses `.get()`, so an unmapped
declaration degrades rather than raising. **When the AI-heavy scope content is defined**,
the work is: a new `reference/kpmg_scope/ai_heavy.yaml`, an entry in
`_PREFERENCE_TO_TYPE`, and a `DdType` member. Nothing else should need to change.

**4. Empty draft fields read "No information entered"** in muted italics, replacing the
bare em-dash. `formatValue` in `cover-sheet.tsx` now returns `None` for empty rather
than a dash string, so the caller can style it — a dash is something the reader has to
interpret.

**5. Sequencing is now BROAD PASS → DEEP DIVE.** Rishi's partner's framing: the first
pass reviews every area at structural level and **its deliverable is the areas of
focus**; the deep dive then works only on those. `SequencePhase` gained an `output`
field so that handoff is stated rather than implied — a plan that lists the passes
without naming what moves between them reads as two unrelated activities. Surfaced in
the UI, the Markdown export and both binary exports. The Tier 1/2/3 depth model is
unchanged and still governs individual rows; only the phase vocabulary moved.

**6. PPT export — yes, and it is now the primary artefact.** Rishi confirmed a scope of
work is usually circulated as a deck. `python-pptx==1.0.2`, pure Python, no system
libraries — same profile as ReportLab. **Download PPT** is now the filled primary button
on the scope page; PDF is secondary.

`export_pptx.py` keeps **styling separate from content**: every colour, size and font
lives in the `Theme` dataclass and `build_deck` only decides what goes on which slide.
Rishi chose "build from scratch now, template later" — when a KPMG template .pptx
arrives, the change is to load it as the presentation base and map `Theme` onto its
masters. The slide-building code should not need to change.

**Found by reading the generated deck, not by a failing test:** the engagement summary
rendered as `"... per month.
. This engagement is scoped as ..."`. `_engagement_summary`
used `business.rstrip(".")`, which stops at a trailing **newline** and leaves the full
stop in place — then the template added its own. Every test passed while this was wrong.
Fixed by normalising whitespace before stripping;
`test_engagement_summary_survives_a_trailing_newline_in_the_business` pins it. That is
now three sessions running where reading the output caught something the suite did not.

**Verified in the browser, not assumed:** 2 required asterisks on the target step, 14
hint paragraphs, the AI-heavy card still selected after a reload, "No information
entered" with zero bare dashes remaining, both download buttons present, and a real PPT
downloaded by clicking. Backend 236/236, ruff and mypy clean; frontend tsc, eslint,
vitest 19/19.

**Note on mypy:** `pptx.Presentation` at package level is a *factory function*, not a
class, so it is not valid as a type annotation. The real class is
`pptx.presentation.Presentation`; the module imports both (the factory aliased as
`open_presentation`). Two `pyproject.toml` overrides handle the missing stubs, matching
the ReportLab precedent.


### 2026-08-31 — PDF export

A **Download PDF** button on the scope page, backed by
`GET /engagements/{id}/scope/export.pdf`. Renderer at
`backend/app/services/scope/export_pdf.py`.

**Two decisions Rishi made when asked:**

*ReportLab, not WeasyPrint or browser print.* WeasyPrint gives better typographic
fidelity by reusing the CSS, but needs GTK/Pango system libraries on Windows — that
would have broken the clean `conda env create` story in the README. Browser print needs
no dependencies but the output varies by viewer and cannot be produced by an API call.
ReportLab is pure Python and behaves identically on Windows and any Linux deploy. New
pins: `reportlab==5.0.1`, `pillow==12.3.0` (its image backend, for the cover logo).

*Client-facing content, not the full audit trail.* **This is the one thing to know
before editing this file.** The PDF deliberately omits the Signals and Provenance
sections that the Markdown export carries. Markdown is the internal artefact; the PDF
is what goes to a client. `test_the_internal_audit_trail_is_omitted` guards the split —
if that test starts failing, the PDF has silently become the Markdown export and the
"client-facing" claim in the module docstring is no longer true. Exclusions are *not*
part of the internal layer and are never dropped (DD_master G4).

**Notes for a future session:**

- The route is declared **before** `/{version}` in `routes/scope.py`. FastAPI matches in
  declaration order, so moving it below would make `export.pdf` parse as a version.
  `test_export_pdf_route_is_not_shadowed_by_the_version_route` pins this.
- ReportLab ships no type stubs, so under mypy `strict` every call into it is an
  untyped call. Handled with two targeted `pyproject.toml` overrides rather than
  scattered `# type: ignore`; the exporter's own signatures stay fully typed.
- `_escape()` is load-bearing. ReportLab's `Paragraph` parses a mini-HTML dialect, so an
  unescaped `&` or `<` in a company name raises mid-render and takes out the whole
  export. `test_special_characters_do_not_break_the_render` covers it.
- Tests set `reportlab.rl_config.pageCompression = 0`. ReportLab writes page streams as
  **ASCII85 + Flate**, which no simple regex can read back — `zlib.decompress` alone
  fails on it. With compression off the text stays as plain literals and the assertions
  can check what the document actually says. This changes only the byte encoding.
- The determinism test masks `/CreationDate`, `/ModDate` and the trailer `/ID` (a hash
  seeded from the timestamp). Everything else is byte-identical between renders —
  verified, not assumed.

**Found by looking at the output, not by the tests passing:** the bullet glyphs rendered
floating level with the ascenders (`bulletOffsetY=1` lifts the glyph *above* the
baseline; it needed a small negative value). Every test passed while this was wrong.
The same lesson as the Phase 2 bugs below — generate the artefact and *look at it*.

### 2026-08-31 — UI fixes and the `tech_is_product` removal

Four items from Rishi, all done.

**1. Sidebar logo.** `public/kpmg-logo-white.png` was the old 690×362 asset with heavy
internal padding, declared at those dimensions — hence the small, off-centre mark.
Replaced with Rishi's tight-cropped 336×140 file from `assets/`, dimensions corrected,
box height `h-8` → `h-9`.

**2. Content did not fill the screen.** Every page hard-capped at
`max-w-[880px]`/`[920px]`/`[1120px]`, which left the content marooned beside the 248px
rail on a wide monitor. Main working columns are now `max-w-[1600px]` with `w-full`.
Deliberately *not* changed: the `720px` centred error/empty/loading states, and the
`~70–72ch` prose measures inside the scope document — a scope row stretched to 1600px
is unreadable. Methodology went `760px` → `900px`; it is a pure prose page.

**3. Sidebar stopped on scroll.** It was `h-screen` in normal flex flow — exactly one
viewport tall, scrolling away with the page. Now `sticky top-0 … self-start`, with
`items-start` on the shell row (default `stretch` would defeat `position: sticky`) and
`min-h-screen` moved onto the content column so the footer still sits at the bottom.

**4. `tech_is_product` removed** — see the decision entry above for the rule
re-sourcing and the trade it makes.

**Verified, not assumed.** Backend 205/205 (was 204; one added), ruff and mypy clean.
Frontend tsc, eslint, vitest 19/19, and a clean `next build`. Migration applied to the
dev DB and the stored rows checked directly: 4 intake rows, 0 still carrying the key.
`/api/v1/meta/enums` no longer serves `techIsProduct`. A full engagement was created
through the API and a scope generated: classification `product`, mix 100, confidence
high, **A1 and M6 both firing from the declaration**, all 10 KPMG rows rendered at
correct tiers.

Two things worth knowing:

- The generated scope came back as `generator: "rules (llm error)"`. **Not a
  regression** — the Gemini free tier's 20-requests-per-day quota was exhausted
  (`429 RESOURCE_EXHAUSTED`). The fallback did exactly what it is designed to do: logged
  a warning, shipped the complete deterministic scope, and recorded the reason in the
  payload. The "model is an improvement, never a dependency" property held under a real
  failure rather than a mocked one.
- `position:sticky` was missing from the dev server's CSS bundle while every other new
  utility compiled. That was a stale incremental cache, not a code fault — confirmed by
  a clean `next build`, where it is present.

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
