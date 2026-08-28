# PHASE2_SCOPE_ENGINE.md — Scope-of-Work Generation Engine

Phase 2 of the Tech DD platform. Read `DD_master.md` first — it is the domain
authority and this document only says how to encode it. `CLAUDE.md` still governs
stack, conventions and git rules. Phase 1 is built and committed; this phase replaces
`PlaceholderScopeGenerator` behind the existing `ScopeGenerator` protocol.

---

## 1. Objective

Turn a filed engagement intake into a **defensible, tailored, auditable scope of
work** for a technology due diligence — one a partner could hand to a client without
rewriting it.

Three properties, in priority order:

1. **Defensible.** Every workstream and every depth tier traces to a named signal in
   the intake and, where possible, to a citation in `DD_master.md`. A reviewer can ask
   "why is W-SEP at Tier 3?" and get an answer.
2. **Tailored.** No generic output. The source's own instruction: *"Don't simply apply
   a predefined standard due diligence approach and scope. You should adapt to the
   specific transaction context."* (`DD_master.md` §11).
3. **Repeatable.** The same intake produces the same deterministic skeleton. Only the
   prose layer varies, and it varies inside a validated schema.

---

## 2. Architecture — deterministic core, generative surface

```
IntakeFull
    │
    ▼
┌──────────────────┐   signals: [Signal(code, source_field, value, effect, weight, citation)]
│ SignalExtractor  │────────────────────────────────────────────────┐
└──────────────────┘                                                │
    │                                                               │
    ▼                                                               │
┌──────────────────┐   dd_mix (0-100), dd_type, confidence          │
│ MixScorer        │────────────────────────────────────────────────┤
└──────────────────┘                                                │
    │                                                               │
    ▼                                                               │
┌──────────────────┐   selected modules + base tiers                │
│ ModuleSelector   │◀─── WorkstreamLibrary (versioned YAML)         │
└──────────────────┘                                                │
    │                                                               │
    ▼                                                               │
┌──────────────────┐   final tiers, caps applied, cap reasons       │
│ DepthCalibrator  │────────────────────────────────────────────────┤
└──────────────────┘                                                │
    │                                                               │
    ▼                                                               │
┌──────────────────┐   injected content blocks (carve-out Qs, ERP note, …)
│ ContentInjector  │────────────────────────────────────────────────┤
└──────────────────┘                                                │
    │                                                               │
    ▼                                                               ▼
┌────────────────────────┐                              ┌──────────────────────┐
│ RulesScopeGenerator    │  ScopeOfWorkPayload (complete, publishable as-is)   │
└────────────────────────┘                              │  ProvenanceRecord    │
    │                                                    └──────────────────────┘
    ▼  (optional, config-gated)
┌────────────────────────┐
│ LlmScopeGenerator      │  tailors PROSE ONLY inside the fixed skeleton
└────────────────────────┘  validated → on any failure, return the rules output
    │
    ▼
ScopeOfWorkPayload v2  ─────────►  persisted as a new scope_of_work version
```

**Non-negotiable:** the LLM may **never** add, remove or re-tier a workstream, change
`dd_mix`, or invent an evidence request. It rewrites objectives, question phrasing and
narrative to fit the target's line of business, and nothing else. Every LLM output is
schema-validated and diffed against the deterministic skeleton; a diff outside the
allowed prose fields is a rejection, and the rules output ships instead.

---

## 3. The workstream library

**Location:** `backend/app/reference/workstreams/` — one YAML file per module, plus
`_library.yaml` holding the library version and module order.

**Why YAML, not code:** the library is domain content, not logic. It must be editable
by a practitioner without touching Python, diffable in git, and versioned
independently of the engine. Load it once at startup, validate it against a Pydantic
model at load time, and fail fast on a malformed file.

### 3.1 Module schema

```yaml
id: W-VEN
name: Vendors, Contracts and Licensing
short_name: Vendors & Contracts
archetype_affinity: 0          # -100 pure enterprise … +100 pure product; 0 = neutral
library_version: "1.0"
summary: >
  Establishes what the target buys, on what terms, what transfers with the deal, and
  what it costs to move or replace.
objectives:
  - text: Determine which third-party contracts and licences transfer, and on what terms.
    source: "Roehl-Anderson 2013, p. 73"
  - text: Size assignment, relicensing and termination exposure before it becomes a Day 1 problem.
    source: "Roehl-Anderson 2013, p. 199-200"
key_questions:
  - text: What services are provided by external vendors?
    tier: 1
    source: "p. 73"
  - text: How flexible are the current vendor contracts? Are all software licences current?
    tier: 1
    source: "p. 73"
  - text: Which licences cannot transfer with the transaction?
    tier: 2
    applies_when: "deal_type in [carve_out, divestiture_sell_side]"
    source: "p. 78"
  - text: What is the change-of-control or assignment position on each critical supplier agreement?
    tier: 3
    source: "p. 199-200"
evidence_requests:
  - text: Full contract register with counterparty, term, renewal date, annual value and assignment clause.
    data_room_folder: Legal
    tier: 2
    source: "p. 84"
  - text: Software licence inventory with entitlement counts and true-up position.
    data_room_folder: Legal
    tier: 2
interview_targets:
  - role: CIO or Head of IT
    topics: [vendor management, licence position, known disputes]
  - role: Procurement lead
    topics: [contract register completeness, renewal calendar]
    tier: 3
common_findings:
  - Non-current software licences.
  - Expired contracts.
  - Contracts that are non-transferable.
red_flags:
  - code: VEN-LEADTIME
    text: Suppliers need lead time of up to six months to grant contractual rights; a close inside that window is a live Day 1 compliance risk.
    source: "p. 222"
effort_bands:            # indicative person-days by tier
  1: [1, 2]
  2: [3, 6]
  3: [8, 15]
depends_on: [W-APP, W-INFRA]
mandatory_when:
  - "deal_type != minority_growth"
source_provenance: sourced      # sourced | extended | mixed
```

**`source_provenance` is required on every module and every question.** `DD_master.md`
§16 explains why: the platform must be able to show a reviewer which content comes
from a cited methodology and which is modern practice the platform added.

### 3.2 Modules to ship in v1

Build all twelve from `DD_master.md` §6, keeping its ids:

`W-OPS`, `W-VEN`, `W-PROC`, `W-STRAT`, `W-SPEND`, `W-APP`, `W-INFRA`, `W-SEC`,
`W-DATA`, `W-SEP`, `W-INT`, `W-PROD`.

`W-PROD` carries sub-modules `P1`–`P10` (`DD_master.md` §6.12). Model sub-modules as
a `submodules:` list inside the module file with the same question/evidence shape, so
the product deep-dive can be tiered per sub-module rather than as one block.

Content for each module is already written in `DD_master.md` §6 — including verbatim
sourced question sets. **Transcribe it faithfully; do not paraphrase sourced questions
and do not silently drop any.** Where `DD_master.md` marks content `[EXT]`, set
`source_provenance: extended` on that item.

---

## 4. Signal extraction

`backend/app/services/scope/signals.py`

```python
class Signal(BaseModel):
    code: str                 # "A2", "M4", "D1" — matches DD_master.md §15 rule ids
    label: str                # "Target is digital-native"
    source_field: str         # "target.digital_maturity"
    source_value: str
    effect: SignalEffect      # mix_delta | force_module | cap_tier | inject_content
    detail: dict              # {"mix_delta": 25} / {"module": "W-SEP", "min_tier": 2}
    citation: str | None      # "Roehl-Anderson 2013, p. 76-77"
    provenance: Literal["sourced", "extended"]
```

Rules live in `backend/app/reference/scope_rules.yaml`, not in Python — same reasoning
as the library. Implement the full rule set from `DD_master.md` §15: **A1–A11**
(archetype mix), **M1–M7** (mandatory modules), **D1–D10** (depth and access gates),
**C1–C9** (content injection).

The extractor is pure: `IntakeFull -> list[Signal]`. No I/O, no randomness, trivially
testable.

---

## 5. Mix scoring and classification

`backend/app/services/scope/scoring.py`

- Start at **50** (neutral). Apply every `mix_delta` signal. Clamp to 0–100.
- Bands: `0–34 enterprise`, `35–65 blended`, `66–100 product`.
- **Confidence** — report `high` / `medium` / `low` from: how many mix signals fired,
  whether they agree in direction, and whether the fields that drive the strongest
  rules were actually answered. Low confidence must be surfaced in the UI, not buried.
- **Override.** If `objectives.dd_type_preference != auto`, the user's choice is the
  `dd_type` used for output, the engine's own computation is retained alongside it as
  `computed_dd_type` / `computed_dd_mix`, and `dd_type_override_reason` is displayed
  in the scope. Never silently discard the computed value — the disagreement is
  informative.

The weights in `DD_master.md` §15.1 are a **starting calibration**, explicitly flagged
there as needing tuning. Keep them in the YAML so they can be tuned without a code
change, and write the golden-case tests (§10) so tuning is safe.

---

## 6. Module selection and depth calibration

`backend/app/services/scope/selection.py`, `.../depth.py`

**Selection order — do not reorder:**

1. **Floor.** M1 puts `W-OPS`, `W-APP`, `W-INFRA`, `W-SPEND` in at Tier ≥ 1, always.
   `DD_master.md` guardrail G3: the 80% core is never dropped to make room for
   tailoring.
2. **Mandatory triggers.** M2–M7 force modules in at their minimum tiers.
3. **Affinity weighting.** Remaining modules are included and base-tiered by how
   closely `archetype_affinity` matches `dd_mix`.
4. **Objective boost.** Modules matching the user's `dd_objectives` get +1 base tier.
   The user's stated priorities beat inferred ones (`DD_master.md` §8.1).
5. **Complexity adjustment.** D9/D10 raise tiers where the estate is complex or the
   target is comparable in size.

**Then calibrate down:**

6. **Access gates (D1–D3).** Hard caps. `code_access = none` caps `W-PROD` at Tier 2;
   `access_level = public_only` caps everything at Tier 1; `management_access = none`
   strips interview-dependent evidence.
7. **Time and stage gates (D4–D8).** `timeline_weeks <= 3` collapses to a Tier 1 sweep
   plus one Tier 3 module. Early stage → breadth. Confirmatory → depth on flagged
   areas plus a mandatory cost model. Financial buyer → sweep then targeted depth.
   Strategic buyer integrating → Tier 2+ on every domain.
8. **Effort reconciliation.** Sum `effort_bands` for the resulting tiers. If the total
   materially exceeds what `timeline_weeks` and `budget_band` support, step down the
   lowest-signal modules one tier at a time and **record each step-down as an explicit
   trade-off note in the scope**. Never quietly truncate.

Every cap and every step-down writes a `reason` onto the workstream. That reason
appears in the UI.

---

## 7. Output schema

Extend `backend/app/schemas/scope.py`. Keep `ScopeOfWorkPayload` as the persisted
shape and add a `schema_version: 2` discriminator so Phase 1 placeholder rows still
deserialise.

```python
class ScopedQuestion(BaseModel):
    text: str
    tier: int
    source: str | None
    provenance: Literal["sourced", "extended"]

class EvidenceRequest(BaseModel):
    text: str
    data_room_folder: str | None      # Exhibit 5.9 mapping
    tier: int
    blocked_by_access: bool = False   # true when access level makes it unobtainable

class ScopedWorkstream(BaseModel):
    id: str
    name: str
    tier: int
    tier_reason: str
    archetype_affinity: int
    objective: str                    # tailored prose
    summary: str
    key_questions: list[ScopedQuestion]
    evidence_requests: list[EvidenceRequest]
    interview_targets: list[InterviewTarget]
    common_findings: list[str]
    red_flags: list[RedFlag]
    effort_days: tuple[int, int]
    depends_on: list[str]
    out_of_scope_note: str | None
    triggered_by: list[str]           # signal codes

class Classification(BaseModel):
    dd_type: DdType
    dd_mix: int
    confidence: Literal["high", "medium", "low"]
    computed_dd_type: DdType
    computed_dd_mix: int
    override_applied: bool
    override_reason: str | None
    signals: list[Signal]

class ScopeOfWorkPayload(BaseModel):
    schema_version: Literal[1, 2]
    is_placeholder: bool
    generator: str
    library_version: str
    rules_version: str
    classification: Classification | None
    engagement_summary: str            # tailored, references line of business
    objectives: list[str]
    workstreams: list[ScopedWorkstream]
    sequencing: list[SequencePhase]    # week-banded plan
    cost_estimation_plan: CostPlan     # one-time + recurring lines, assumptions register
    team_shape: TeamShape              # core team + required SMA specialisms
    diligence_risks: list[str]         # access gaps, timeline risk, info asymmetry
    exclusions: list[Exclusion]        # what is out, and why
    provenance: list[FiredRule]        # every rule that fired, with its citation
```

`exclusions` and `provenance` are **required, non-empty** in any non-placeholder
scope. `DD_master.md` guardrails G4 and G5.

---

## 8. The LLM layer

`backend/app/services/scope/llm.py`

**Scope of its authority:** rewrite `engagement_summary`, each workstream's
`objective`, and the *phrasing* of `key_questions` so they name the target's actual
line of business, systems and thesis. Nothing else.

**Implementation:**
- Anthropic Messages API. Model id and API key from settings/env; never hard-coded.
  Absent key ⇒ `LlmScopeGenerator` is unavailable and the factory falls back to
  `RulesScopeGenerator` with a logged warning, not an exception.
- Input: the deterministic skeleton plus the intake's narrative fields
  (`line_of_business`, `context_narrative`, `rationale_narrative`, `known_concerns`,
  `deal_breakers`, `known_tech_stack`, `ma_history`).
- Request structured JSON matching a strict `LlmTailoring` model: a list of
  `{workstream_id, objective, questions: [{index, text}]}` plus `engagement_summary`.
- **Validation, in this order:** parse → schema-validate → assert the workstream id set
  is identical to the skeleton's → assert question counts and indices match → assert
  no question changed tier. Any failure: log, discard the tailoring, return the rules
  output, and mark `generator: "rules (llm tailoring rejected)"`.
- Deterministic where it can be: `temperature` low and configurable, and cache by a
  hash of (skeleton, narrative inputs, model, prompt version) so re-opening a scope
  does not re-bill.
- Prompt lives in `backend/app/services/scope/prompts/tailoring.md`, versioned, with
  the version recorded in the payload.

**Do not** let the LLM produce the cost plan, the sequencing or the exclusions. Those
are computed.

---

## 9. API and UI

### 9.1 Backend
| Endpoint | Change |
|---|---|
| `POST /api/v1/engagements/{id}/scope` | Accept `{"generator": "rules"\|"llm"\|null, "force_regenerate": bool}`. Creates a new version. |
| `GET /api/v1/engagements/{id}/scope` | Unchanged contract, richer payload. |
| `GET /api/v1/engagements/{id}/scope/versions` | Unchanged. |
| `POST /api/v1/engagements/{id}/scope/preview` **(new)** | Classification only, from a **draft** intake. Powers the live SignalPanel. Must tolerate incomplete intakes and return `confidence: low` rather than erroring. |
| `PATCH /api/v1/engagements/{id}/scope/{version}/workstreams/{ws_id}` **(new)** | Human tier override and objective edit. Stores `edited_by_human: true` and preserves the original. |
| `GET /api/v1/meta/workstreams` **(new)** | The library, for the methodology page. |

`SCOPE_GENERATOR` setting gains `rules` and `llm`; default becomes `rules`.

### 9.2 Frontend
- **`/engagements/[id]/scope`** — rewrite. Classification header (dd_type, mix as a
  slider-style readout, confidence chip, override banner where applicable);
  "why this classification" disclosure listing signals with their source fields and
  citations; workstream cards with tier chip, tier reason, collapsible questions and
  evidence checklists; sequencing timeline; exclusions section; provenance footer.
  Remove the placeholder banner.
- **`SignalPanel`** in the intake shell — wire it to `/scope/preview`, debounced. It
  becomes live instead of static. Show the forming mix and the top three signals.
- **`/about/methodology`** — render the library from `/meta/workstreams`, with
  sourced/extended badges, so the methodology page is generated from the same data
  the engine uses rather than duplicated prose.
- **Export** — `deliverable_format` drives a Markdown export of the scope. Do not
  build DOCX/PDF in this phase.

### 9.3 Intake additions (required before the engine can run)
Add these fields, per `DD_master.md` §13, with an Alembic migration and matching zod
schemas and form controls:

| Section | Field | Enum |
|---|---|---|
| structure | `deal_type` | full_acquisition · carve_out · joint_venture · merger_of_equals · divestiture_sell_side · minority_growth |
| structure | `perspective` | buy_side · sell_side |
| structure | `integration_model` | consolidation · combination · transformation · preservation · undecided |
| structure | `relative_size` | target_much_smaller · comparable · target_larger |
| technology | `it_landscape_complexity` | low · medium · high |
| technology | `shared_with_parent` | free text, shown only when `carve_out_or_tsa` is true |
| objectives | `management_access` | none · cio_only · cio_plus_team · full |

Existing filed engagements must survive the migration: make the new columns nullable,
and have the engine treat a missing value as "unknown" — a signal that lowers
confidence rather than an error.

---

## 10. Testing

This is the phase where tests carry real weight, because the output is a judgement.

**Unit**
- `SignalExtractor`: one test per rule in `DD_master.md` §15 — fires when it should,
  does not fire when it should not.
- `MixScorer`: clamping, band boundaries (34/35, 65/66), confidence downgrades on
  sparse or conflicting input.
- `DepthCalibrator`: every cap in D1–D10; effort reconciliation step-downs recorded.

**Golden cases** — `backend/tests/golden/`, one JSON intake fixture and one snapshot
per case. These are the tests that catch a bad weight change:

| Case | Intake shape | Expected |
|---|---|---|
| G1 | Digital-native B2B SaaS, VC minority growth, full code access, 8 weeks | product-heavy (mix ≥ 70); `W-PROD` Tier 3 with sub-modules; `W-SEP` absent |
| G2 | Industrial manufacturer carve-out from a corporate parent, PE majority, ERP-heavy, 6 weeks | enterprise-heavy (mix ≤ 30); `W-SEP` and `W-VEN` Tier ≥ 2; ERP 80%-of-cost note injected; carve-out questions verbatim |
| G3 | Healthtech platform, PHI + HIPAA, strategic acquirer integrating | blended; `W-SEC` and `W-DATA` Tier ≥ 2; `W-INT` present; every domain Tier ≥ 2 per D8 |
| G4 | Same as G1 but `code_access = none`, `timeline_weeks = 2`, `deal_stage = pre_IOI` | `W-PROD` capped at Tier 2 with an explicit limitation note; Tier 1 sweep; red-flag posture; diligence-risk section names the access gap |
| G5 | Sparse intake — most optional fields empty | `confidence: low`; no crash; unknown-value signals recorded |
| G6 | `dd_type_preference = enterprise` on a G1-shaped intake | override applied; `computed_dd_type` still product; override reason surfaced |

Snapshot the deterministic payload (rules generator only — never snapshot LLM output).

**LLM layer**
- Mock the client. Test: valid tailoring applied; tailoring that adds a workstream
  rejected; that drops one rejected; that changes a tier rejected; malformed JSON
  rejected; missing API key falls back cleanly. Never call the live API in tests.

**Frontend**
- Vitest on the classification readout and workstream card.
- One Playwright pass: file an engagement → generate scope → see classification,
  signals, tiers, exclusions → override the dd_type → regenerate → see version 2.

---

## 11. Guardrails, restated as acceptance criteria

- [ ] No generated scope contains a workstream objective that would read identically
      for a different target. (G1)
- [ ] No workstream is tiered above what `access_level` / `code_access` /
      `management_access` permit, and every cap is visible in the output. (G2)
- [ ] `W-OPS`, `W-APP`, `W-INFRA`, `W-SPEND` are present in every scope. (G3)
- [ ] `exclusions` and `provenance` are non-empty in every non-placeholder scope. (G4, G5)
- [ ] A human tier override or objective edit always survives regeneration as a
      recorded prior version, and `dd_type_preference` always wins. (G6)
- [ ] Cost language is order-of-magnitude with an assumptions register — never a point
      estimate. (`DD_master.md` §8.3)
- [ ] Every question and evidence request carries `provenance` and, where sourced, a
      citation.
- [ ] The rules generator produces a complete, publishable scope with the LLM disabled.
- [ ] `pytest`, `vitest`, `ruff`, `mypy`, `eslint`, `tsc --noEmit` all clean.

---

## 12. Sequence of work

1. Intake additions + migration + zod/form updates (§9.3). Verify existing engagements
   still load.
2. Workstream library YAML + loader + validation model, all twelve modules (§3).
3. `scope_rules.yaml` + `SignalExtractor` + unit tests (§4).
4. `MixScorer` + `ModuleSelector` + `DepthCalibrator` + unit tests (§5, §6).
5. Output schema v2 + `RulesScopeGenerator` + golden-case tests (§7, §10).
6. API changes incl. `/scope/preview` and the workstream PATCH (§9.1).
7. Scope page rewrite + live SignalPanel + methodology page from the library (§9.2).
8. `LlmScopeGenerator` + validation + fallback + mocked tests (§8).
9. Markdown export.
10. Full check pass, README update, commits. **Rishi pushes.**

Commit after each numbered step. Do not begin step *n+1* with step *n* failing.
