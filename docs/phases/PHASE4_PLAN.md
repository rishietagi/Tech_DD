# Phase 4 — Checklist (IRL document tracking)

**Status: BUILT**, with two pieces deliberately deferred to deployment (below).

## What this phase adds

The IRL tells the target *what to send*. Nothing tracked *what had arrived*. The
**Checklist** is that screen: one view of what is outstanding, what matters most, and
what has been received.

```
Intake → Scope of Work → Research → IRL → Checklist
                                          (what has actually arrived)
```

## Data model

One table, following the established child-table pattern:

`irl_document_status` — `(irl_id, question_id, status, document_type, notes,
matched_files, set_by_human)`, unique on `(irl_id, question_id)`.

Separate from `irl_response` on purpose: a **response** is what the client wrote, a
**status** is what the deal team observes about the documents. They move independently,
and the scanner will write status without touching anything the client typed.

**Rows exist only once a status is set.** Absence means `not_received`, so the IRLs that
already existed needed no backfill. Migration `0004_add_irl_document_status`.

## Ranking

Four levels, derived from data the engine already has — instant, explainable, stable:

| Level | Rule |
|---|---|
| **Critical** | the scope row carries `W-SEC`, `W-PROC` or `W-DATA` — security, privacy or regulatory evidence |
| **High** | seeded by a Tier 3 (Deep dive) row |
| **Medium** | seeded by a Tier 2 (Assess) row |
| **Low** | model-added supporting context; Legal/Finance additions are raised to High |

Every rank carries a one-line reason, shown as the badge's tooltip. A colour with no
explanation is not auditable, and a consultant should be able to disagree on stated
grounds.

**Calibrated against the real 45-request Meridian Analytics list.** The first version
made every deep-dive request critical, which put 24 of 45 items (53%) in one bucket and
left the colour meaningless. Reserving critical for sensitive areas gives a usable
spread: **9 critical / 25 high / 6 medium / 5 low**.
`test_the_scale_actually_discriminates` guards against a regression to one dominant
level.

The tier is **not stored on `IrlQuestion`** — only `source_row_id` — so the ranker joins
back to the scope payload. That keeps the IRL schema unchanged and means lists generated
before this feature ranked correctly without regeneration.

**LLM seam**: `rank_questions()` takes an optional `refiner`, unused today. Target-
specific judgement ("a Tier 2 security policy matters more than a Tier 3 diagram for
*this* deal") slots in there without touching a caller.

## API

```
GET   /engagements/{id}/checklist                the assembled view   404 no_irl
PATCH /engagements/{id}/checklist/{question_id}  set status/type/notes
POST  /engagements/{id}/checklist/scan           501 — see below
```

The checklist is **assembled on read**, never stored: questions + statuses + computed
ranks. Nothing to regenerate, nothing that can drift out of step with the IRL.

`PATCH` returns the whole checklist so the caller's summary counts stay consistent with
the row it just changed.

## Frontend

`/engagements/[id]/checklist` — three columns exactly as specified:
**Documents Requested | Document Type | Status**, with the priority badge beside the
document name and a legend above the table.

New colour tokens in `styles/tokens.css`, mapped in the `@theme inline` block of
`app/globals.css` (the house palette was blue/red/neutral only — a four-step ramp needs
a warm hue, and green appears only where "arrived" genuinely means good).

Nav gained **Checklist** in the Engagement section, after Initial request list.

---

## Deferred: shared-drive scanning

**Not built.** `services/checklist/scanner.py` holds the contract and the reasoning; the
endpoint returns a clear 501 rather than a missing route, so the shape is visible in
OpenAPI and the UI has something real to call.

**Rules it must follow when built** — these are the load-bearing ones:

1. **A scan never overwrites a human-set status.** `set_by_human` exists for this.
   Someone who has looked at a document outranks a filename match.
2. **Record what was matched** in `matched_files`, so a wrong call is visible and
   correctable rather than silent.
3. **Below the confidence threshold, propose nothing.** Leaving a request
   `not_received` is honest; marking it received on a weak match is not.
4. **Read-only over the drive.** Never delete or move client files.

Likely strategy: tokenise the filename and its folder, score against `seed_text` and the
question text (both already stored on every `IrlQuestion`), and treat the per-function
folder names as a strong hint.

**Test fixture**: `shared-drive/project-lighthouse/` — gitignored, 24 files across 6
function folders, built from the real Lighthouse IRL. Deliberately partial so every
status is demonstrable: clear matches, three files marked `-ONLY` that should read as
*received partially*, and roughly half the list with nothing at all.

## Deferred: email reminders

**Frontend stub only.** The panel shows the recipient field and a live preview computed
from real checklist data; Send is visibly disabled and the panel is badged "Not
connected yet". A button that looks functional and silently does nothing is worse in a
demo than one honestly marked pending.

To wire it, decide: trigger (scheduled vs manual), provider, where the consultant's
address comes from, and whether the mail carries the xlsx as an attachment.

---

## Verification

- backend `pytest` 300 · `ruff` · `mypy` clean (74 files)
- frontend `tsc` · `eslint` · `vitest` 19 clean
- drove it in a browser against the real 45-item Lighthouse list: correct columns,
  legend covering all four levels, **four distinct badge colours actually rendering**,
  status change persisted across a reload, summary counts updating, the reminder
  preview matching the table, Send disabled, and the scan surfacing its 501 message
