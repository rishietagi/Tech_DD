# Phase 3 — IRL (Initial Request List) + Company Research

**Status: BUILT.** See `docs/PROJECT_LOG.md` for the decisions and the known gaps.

## What this phase adds

The platform owned two steps: **Intake** → **Scope of Work**. Phase 3 adds what comes
next in a real deal — the **Initial Request List** the buyer sends the target, and the
**company research** that informs it.

```
Intake  →  Scope of Work  →  Company research  →  Initial Request List  →  Excel
                    (what we will cover)   (what is publicly known)   (what we need from you)
```

## The load-bearing idea, extended

Phase 2's split — *rules decide coverage, the model writes prose* — carries into the IRL.

Every KPMG scope row in `reference/kpmg_scope/*.yaml` already carries an `evidence` list
("Architecture diagrams and system documentation", "Known technical debt register"),
which reaches the payload as `ScopedRow.evidence_requests`. Those lists are the
deterministic **seed** for the request list:

- every seeded question traces back to a scope area that a rule opened;
- the IRL generates completely with the LLM switched off;
- the model's job is to rewrite seeds into client-ready wording, and to add the
  non-technology functions (HR, Finance, Legal) a tech scope never reaches.

Rows at tier 0 are skipped — there is no point requesting evidence for an area the
engine deliberately did not open.

## Data model

Each deliverable is its own versioned child table hanging off `engagements`, exactly as
`scope_of_work` already is. **Adding a further module later is one more table + service +
router**, with no change to anything existing.

| Table | Holds |
|---|---|
| `information_request_list` | one generated IRL version |
| `irl_response` | one answer against one question |
| `company_research` | one grounded research run |

`irl_response` is **separate from the payload on purpose**: responses are user data with
a different lifecycle from the generated document, so regenerating an IRL never clobbers
answers someone has typed. Answers on stable ids are carried forward to the new version.

Migration: `0003_add_irl_and_research`.

## Backend layout

```
services/irl/
├── seeds.py        scope evidence -> seed requests (deterministic)
├── composer.py     the deterministic list, incl. the fallback function mapping
├── llm.py          Rules/Llm generators, validation, fallback
├── export_xlsx.py  Function | Question | Response
├── service.py      versioning, response upsert, carry-forward
└── prompts/irl.md  versioned prompt

services/research/
├── generator.py    one grounded Gemini call; rejects if ungrounded
├── service.py      versioning and persistence
└── prompts/research.md
```

## API

```
POST   /engagements/{id}/research            run research
GET    /engagements/{id}/research            latest              404 no_research
POST   /engagements/{id}/irl                 generate            409 not_scoped
GET    /engagements/{id}/irl                 latest              404 no_irl
GET    /engagements/{id}/irl/export.xlsx     the workbook
PATCH  /engagements/{id}/irl/responses/{qid} save one answer
GET    /engagements/{id}/irl/versions        version list
```

`export.xlsx` is declared **before** `/{version}` — FastAPI matches in declaration
order, the same trap already recorded for `export.pdf` and `export.pptx`.

## Frontend

| Route | What it is |
|---|---|
| `/engagements/[id]/research` | summary, findings with sources, disclaimer |
| `/engagements/[id]/irl` | the grouped table with inline autosaving responses |

The sidebar gained an **Engagement** section (Overview / Scope of work / Company
research / Initial request list) shown whenever an engagement is active — this is what
makes "a project contains its modules" visible rather than only true in the schema.

## Verification

- backend `pytest` 284 · `ruff` · `mypy` clean
- frontend `tsc` · `eslint` · `vitest` 19 clean
- generated a real IRL: 30 questions, 8 functions, each traceable to a scope row
- opened the exported workbook: three columns, header frozen, 29 rows blank for the
  client, 1 pre-filled answer round-tripped
- drove it in a browser: typed a response, saw "Saved", reloaded, it persisted
