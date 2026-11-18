# Phase 7 — Report generation, the intelligence pipeline, and edit-before-export

**Status:** approved 2026-11-18 (Rishi). Built in the order of "Execution order" below.

## Context

The platform produces every input to a diligence (scope, IRL, research, three assessments,
IT budget) but not the deliverable. Rishi shared a real KPMG IT DD draft report
as the target shape: Cover → ToC → Context setting → Glossary → In-scope areas →
Data limitations → Executive summary (per diligence area: findings + implication, RAG risk,
recommended actions, investment impact) → Supporting analysis (applications, landscape
diagram, infrastructure, people & skills) → Appendix (application, team and network detail).

He also asked that **every generator be deterministic now but LLM-ready**: one pipeline,
a SKILL.md of instructions per generation task, switched on later by a key.

### Decisions taken (Rishi, 2026-11-18)
| # | Decision |
|---|---|
| D1 | **Investment impact = XXX** for the engagement team, editable. **Everything exportable is editable before export** — app-wide rule. |
| D2 | **The report names the investor and the target** (it is written after engagement, when names are known). My follow-through: the **scope deck stays anonymised** — it is a proposal artefact that circulates before engagement and follows the KPMG source deck's convention; the IRL already names the target. Recorded in PROJECT_LOG, no other feature changes. |
| D3 | **Add IT team and IT contracts inventories** to the IRL (template + upload + form). |
| D4 | **`AI_MODE` setting, default `off`**: deterministic everywhere even with a key; `auto` turns the LLM on for every skill whose key is present. |

### Confidentiality
The sample report is client material (client, target and employee names). It is used for
**structure only**: `docs/reference/REPORT_STRUCTURE.md` records sections, columns and
conventions with no names, figures or client text.

---

## Part A — The intelligence pipeline (every generator)

**Skills.** `backend/app/skills/<skill>/SKILL.md`: YAML frontmatter + the prompt body (single
source of truth — existing prompts move here verbatim, versions kept).

Frontmatter: `name`, `description`, `version`, `mode` (`prose_only` | `bounded_refinement` |
`grounded_search` | `judgement`), `deterministic_fallback` (the rules function), `inputs`,
`outputs`, `may_change`, `must_not_change`, `house_rules`.

| Skill | Today | Deterministic floor |
|---|---|---|
| `scope-tailoring` | `scope/prompts/tailoring.md` | RulesScopeGenerator |
| `irl-generation` | `irl/prompts/irl.md` | RulesIrlGenerator |
| `company-research` + `research-attribution` | `research/prompts/*.md` | **manual entry** (new, Part C) |
| `process-scoring` | `assess/prompts/scoring.md` | `score_assessment` |
| `drive-scan` | `checklist/prompts/scan.md` | filename matching |
| `estate-summary` | `estate/prompts/estate_summary.md` | `rules_summary` |
| `budget-commentary` | new | rules findings text |
| `report-narrative` | new | report builder (Part D) |
| `report-executive-summary` | new | report builder |

**Runtime** — `app/services/intelligence/`:
- `skills.py` — load, validate (required frontmatter, prompt_version present), registry; validated at startup with the estate content.
- `mode.py` — `use_llm(skill, requested=None)`: explicit request wins (tests, dev); else `settings.ai_mode == "auto" and key present and skill not in AI_DISABLED_SKILLS`.
- Every existing call site (`scope/factory.py`, `irl/service.py:_generator_for`, `assess/service.py:_generator_for`, `estate/service.py:_use_llm`, `checklist/scan_llm.py`, research) resolves through `use_llm` and reads its prompt from the skill. `SCOPE_GENERATOR` is retired in favour of `AI_MODE` (kept readable for `placeholder` only); `.env.example` + README updated.
- Every generated payload records `generator` + `skill` + `skill_version` (already true for most; added where missing).
- `GET /api/v1/meta/intelligence` — mode, key present, per-skill status and description.

**Frontend** — Workspace › "AI & skills" page: mode, key status, each skill with its status and its SKILL.md rendered read-only.

## Part B — Two new inventories (D3)

Pure content in `reference/estate/inventory.yaml` + adding the kinds to `INVENTORY_KINDS`:
- **`it_role`** (IT team): name (optional), designation, function/vertical, key skills, responsibilities, experience (years), qualifications, length of service, engagement (In-house / Outsourced / Contractor), applications supported (`app_refs`).
- **`it_contract`**: contract, counterparty, scope/description, type (Support / Licence / SaaS / Managed service / AMC / Telecom / Other), start, end, annual value, payment basis, notice period, change-of-control or assignment clause (Yes/No/TBD), parent-group dependency (Yes/No/TBD), applications covered (`app_refs`).

They travel in the IRL workbook automatically (the sheet writer loops the kinds); the IRL page gains an **"IT team & contracts"** section. Facts only — the inventory-has-no-scores test extends to them.

## Part C — Edit before export (D1)

- **Scope deck**: extend `PATCH /scope/{version}/rows/{row_id}` to edit bullets (`lines`); new `PATCH /scope/{version}` for engagement summary, objectives, sequencing, cost-plan lines and team shape. Original preserved beside each edit (same pattern as row overrides). Scope page gains inline editing; the PPTX and Markdown exports read the edited payload.
- **Research**: `PATCH /research` edits brief sections and findings; `POST /research/manual` creates a `generator: manual` version so research exists with AI off.
- **Report**: fully editable (Part D).

## Part D — The report

**Content** — `reference/report/report.yaml` (practitioner-editable):
section order; supporting-analysis sections per `dd_type` (enterprise / product / blended);
workstream map for every finding source (gap categories, budget, contracts, people → `W-*`);
fallback area labels for findings whose workstream has no scope row (e.g. W-SEC on an
enterprise deck → "Cyber Security"); implication and action templates per category; data-
limitation phrasing; glossary dictionary (abbreviation → expansion; only terms used appear).

**Deterministic builder** — `app/services/report/builder.py` (pure: inputs in, payload out):
| Section | Source |
|---|---|
| Cover | deal codename, "IT Due Diligence", Draft, month |
| Context setting | Objective (investor + target + DD type from intake), Approach (access level, sources used, information cut-off date = latest IRL activity), Outcome; key assessment areas = scope row titles |
| Glossary | terms detected in the report text ∩ dictionary |
| In-scope areas | scope rows: title → its bullets |
| Data limitations | per scope area: IRL requests not received / partial (by `scope_area`), open follow-up questions, inventory gaps ("hosting/vendor not provided for N applications"), assessments with no evidence |
| Executive summary | one row per area with findings: top findings (gaps mapped by workstream, severity-ranked), implication (template), **risk = highest severity**, recommended actions (from gap hypotheses + templates, de-duplicated), **investment = XXX**. An area with no evidence reads "Not assessed — see data limitations"; **no finding is ever dropped** (unmapped → fallback area) |
| Supporting analysis | enterprise: Applications (overview, key applications, contracts, landscape diagram) · Infrastructure (platforms, hosting, resilience & backup checks) · Cyber · Data · People & skills · IT budget · Process automation. product: Architecture & platforms · Engineering practice · Product security · Engineering team · Data & AI · Product financials · Business systems. blended: union, ordered by `dd_mix` |
| Appendix | full application, team, contract, platform, domain tables; target-supplied diagrams |

**Diagrams** — generated from the inventories, never invented:
1. **IT landscape overview** (as in the sample): applications grouped by category, ERP-managed functions from the ERP's processes; infrastructure panel of platforms by category/location with the applications each hosts; backup platforms. One layout model rendered as SVG in-app and native shapes in the PPTX.
2. **Network diagrams**: the platform holds no topology data, so the target's own diagrams are **uploaded as images** (stored in `report_asset`) and placed in the appendix "as provided by the target"; absent → a data limitation.

**LLM hook** — skills `report-narrative` / `report-executive-summary` (prose only): may rewrite context paragraphs, section overviews, finding bullets and implications; may not change areas, risk levels, actions' targets, numbers or XXX. Validated after the call (count, risk, XXX preserved), deterministic text kept on failure.

**Storage** — migration `0009_add_report`: `report` (versioned payload, generator), `report_edit` (overlay keyed on stable element keys, e.g. `exec.EN-01.findings`, `limitations.EN-04`, `context.approach`, plus include/exclude toggles — survives regeneration, revertible), `report_asset` (uploaded diagram images, bytes + mime).

**API** — `/engagements/{id}/report`: `POST` generate · `GET` latest (overlay applied) · `PATCH /elements/{key}` · `DELETE /elements/{key}` (revert) · `POST /assets` · `DELETE /assets/{id}` · `GET /export.pptx`.

**PPTX** — `report/export_pptx.py`, reusing the scope deck's theme and helpers (`scope/export_pptx.py`: `Theme`, `_table`, `_cover_slide`, `_footer` — lifted into a shared `services/pptx_kit.py`): breadcrumb nav strip and DRAFT stamp per slide, blue summary side-panel on supporting slides, RAG dots, tables paginated, "As per information provided by target" source line.

**Frontend** — new sidebar entry **Report** (after IT budget): section rail; each section previewed as a slide-like card; every text block inline-editable with Edited / Revert; include toggles; RAG risk editable; XXX cells editable; diagram rendered as SVG; image upload; Generate / Regenerate / Export PPTX.

## Execution order
1. Docs: `docs/phases/PHASE7_PLAN.md`, `docs/reference/REPORT_STRUCTURE.md` (structure only).
2. Part A backend (settings, skills dir with migrated prompts, registry, resolver, rewired call sites, meta endpoint) + tests.
3. Part B inventories + IRL section.
4. Part C scope and research editing (backend + frontend).
5. Part D backend: YAML, migration, builder, diagrams model, LLM hook, service, routes, PPTX + tests.
6. Part D frontend: Report page.
7. AI & skills page.
8. Verify, then PROJECT_LOG, CLAUDE.md §9, README, `.env.example`.

## Verification
- ruff, mypy, pytest; tsc, eslint, vitest; both servers start; migration at head.
- Key tests: `AI_MODE=off` with a key never constructs a client; every call site maps to a registered skill; every gap reaches an executive-summary area; XXX survives the LLM path; report edits survive regeneration; the report names target and investor while the scope deck stays anonymised; new inventories round-trip through the workbook; scope bullet edits reach the PPTX.
- **Read the output**: generate on Kiln (enterprise) and on an engagement with a product dd_type; dump the PPTX text slide by slide and read it; render slides to images if LibreOffice is available, else read the shapes; drive the Report and AI pages in a browser with no console errors.
