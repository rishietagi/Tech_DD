# Phase 6 — Estate assessment: applications, data & technology, IT budget

**Status:** planned 2026-11-18 (Rishi). Extends Phase 3 (the IRL gains structured
intakes) and Phase 5 (Assess gains two tabs beside the business processes), and adds an
IT Budget module after Assess.

**Origin.** The structure is adapted from Rishi's EA assessment tool (`Desktop/cil`, "CIL
EA Navigator") — its Application Intake, Data & Technology Inputs, Rationalization,
Technical Health and Domain Gap Register. That tool is a single-client demo with seeded
JSON; **its logic is carried over, none of its client data is**. Agri-season, INR and
Azure-specific content does not belong in a diligence product.

Domain reference: `docs/reference/ESTATE_ASSESSMENT_MODEL.md`.

---

## 1. Decisions taken before the build (Rishi, 2026-11-18)

| # | Question | Decision |
|---|---|---|
| D1 | IT Budget shape | **Budgeting-process review**, inside the 2026-09-14 boundary. Budget vs actual over the stated review period, run/change mix *as reported*, and how the budget is defined, agreed and approved. **No % of revenue, no benchmark band, no cost model.** CIL's benchmark version was offered and declined. |
| D2 | Intake templates | **Extra sheets in the IRL workbook** (Application Inventory, Data Domains, Technology Platforms) round-tripped by a hidden ID, plus a standalone template per inventory. |
| D3 | Application scoring | **Fit + disposition + ladder.** Business fit × technical fit (1–5) gives the disposition; automation and AI level sit on 0–5 ladders so applications and business processes speak one language; technical health comes from intake facts. |
| D4 | LLM role | **Prose only.** Scores, dispositions, severities and gaps are deterministic. The ±1 refinement stays unique to business processes. |

## 2. Decisions taken during design (small, noted rather than asked)

- **Intake records facts; Assess records judgement.** CIL put the seven fit scores in the
  intake template. A diligence target must not score its own estate, so the template asks
  only what the target knows (vendor, version, hosting, contract end…) and the fit,
  automation and AI questions are the analyst's, in Assess.
- **The inventory belongs to the engagement, not to an IRL version.** Regenerating the
  request list must never wipe forty typed applications.
- **Applications map to business processes, not to a capability model.** Tech DD has no
  L0–L3 capability tree; it has the five Assess processes. Each application records which
  it supports. That yields portfolio gaps CIL could not make — *a process with no supporting
  system*, and *a process scored Manual or Emerging despite supporting systems* (bought but
  not used — the gap the Assess index page already names as "where diligence findings
  live").
- **Duplication is on application category, not on process.** An ERP, a procurement suite
  and an AP-automation tool all serve Procure to Pay and are complementary, not duplicates.
  Two in-scope applications of the same category are.
- **Gap edits are an overlay keyed on a stable gap key**, so re-scoring keeps a consultant's
  wording and severity (CIL's `SettingOverride` pattern, given its own table).
- **Assess tabs are a search parameter** (`/assess?tab=applications`), not sub-routes —
  `/assess/[processKey]` is already dynamic, and a sibling static segment would read as a
  process key to anyone reading the URL.

## 3. Data model (one migration, `0008_add_estate_assessment`)

| Table | Holds | Versioned |
|---|---|---|
| `inventory_item` | One application, data domain or technology platform. `kind`, a human `ref` (A01, D01, T01), `fields` JSON validated against the YAML field definitions. | No — working data |
| `estate_answer` | One analyst answer: `(engagement, domain, subject_id, question_id)` → value + remarks. `subject_id` is an inventory item id, or `estate` for estate-level checks. | No |
| `estate_assessment` | One scoring run per domain (`applications` / `data_tech`), payload JSON, headline index and band. | **Yes** |
| `estate_gap_note` | A consultant's edit to one gap (severity, description, hypothesis), keyed on the gap's stable key. | No — overlay |
| `it_budget` | The review period, budget and actual lines, and the budgeting-process answers. One row per engagement. | No — analysis computed on read |

## 4. Content (YAML, never Python)

- `reference/estate/inventory.yaml` — field definitions for the three inventories: key,
  label, type (`text`, `select`, `multi_select`, `date`, `yes_no`, `process_list`,
  `app_ref`), options, help. Drives the form, the template, the import validation.
- `reference/estate/applications.yaml` — the per-application questions (business fit ×3,
  technical fit ×4, automation level, AI level), their 1–5 / 0–5 descriptors, the
  disposition rules, the technical-health maps and the gap thresholds.
- `reference/estate/data_tech.yaml` — per-domain and per-platform questions, the estate
  checklist (resilience, engineering, cyber), section weights and gap thresholds.
- `reference/estate/it_budget.yaml` — line categories, the variance tolerance, the default
  review period, the budgeting-process questions and the findings each answer raises.

All validated at startup, like the scope library and the process questionnaires.

## 5. API (`/api/v1/engagements/{id}/…`)

```
GET    inventory?kind=                      list
POST   inventory                            add one item
PATCH  inventory/{item_id}                  edit fields (partial)
DELETE inventory/{item_id}
GET    inventory/{kind}/template.xlsx       standalone template, current rows pre-filled
POST   inventory/{kind}/import               upload → create/update, never clear
GET    estate/{domain}                       subjects + questions + answers
PATCH  estate/{domain}/answers               one answer (subject, question, value?, remarks?)
POST   estate/{domain}/score                 score → new version (+ gap register)
GET    estate/{domain}/score                 latest
PATCH  estate/{domain}/gaps/{gap_key}        overlay an edit
DELETE estate/{domain}/gaps/{gap_key}        revert to generated
GET    it-budget                             inputs + computed review
PUT    it-budget                             replace inputs
```

The IRL export gains the three inventory sheets; the IRL import reads them when present
and reports what it created and updated beside the response count.

## 6. Frontend

- **IRL page** gains a section switch under the summary rail: *Requests · Applications ·
  Data & technology*. Each inventory is a table, a row opens an edit panel generated from
  the YAML field definitions, with add, delete, template download and upload.
- **Assess** becomes three tabs: *Business processes* (unchanged), *Applications*, *Data &
  technology*. Each new tab: the inventoried subjects as a list → select one to answer its
  questions → **Score** → summary, per-subject results, gap register (filterable,
  editable).
- **IT Budget** — new sidebar entry after Assess: review-period grid (budget vs actual per
  line per year), budgeting-process questions, and the computed review (variances, run vs
  change mix, findings).

## 7. Out of scope for this round (recorded, not forgotten)

- The shared-drive scanner does not yet populate the inventories from an uploaded
  application register.
- No client-facing export of the application or data & technology scores — same decision
  as the business-process score.
- No architecture views, roadmap or rationalisation savings — CIL has them; a diligence
  report does not need them yet.

## 8. Done means

ruff, mypy, pytest, tsc and eslint clean; both servers start; and on Project Kiln:
inventory typed and round-tripped through the IRL workbook, both new tabs answered and
scored, gap registers **read**, IT Budget filled and its review **read**, all driven in a
browser.
