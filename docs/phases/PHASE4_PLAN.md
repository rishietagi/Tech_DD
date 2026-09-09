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
POST  /engagements/{id}/checklist/scan           walks the drive — see below
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

## The checklist page no longer exists (2026-09-09)

Rishi folded it into the Initial Request List. Progress, the scan button and the reminder
stub all moved there; `ChecklistTable` and `ChecklistLegend` were deleted as dead code.
The **API is unchanged** — `GET/PATCH/POST /engagements/{id}/checklist` still back the
scan and the tracking, because the IRL reads the same `irl_document_status` table. Read
this plan's API and data-model sections as still current; only the screen is gone.

## Shared-drive scanning — BUILT 2026-09-09

**No longer deferred.** The endpoint walks the folder the client drops documents into,
reads each file, matches it to a request, and writes three things per request: the
**document type**, the **receiving status**, and the **follow-up questions** where what
arrived is not enough.

Two stages, and the split is what keeps it honest:

1. **Deterministic shortlisting** — token overlap between the filename, its folder and the
   request's own text picks up to four candidates. Reproducible, and it bounds the prompt.
2. **A model judgement per shortlisted request** — given the candidates' names *and*
   content excerpts, it decides the status, names the type, and writes the follow-ups.
   Without a key, or when the model fails, filename matching alone still writes statuses —
   but it may not claim "partial", because completeness needs the content, and it writes
   no follow-ups at all.

**The four rules from the stub, all kept:**

1. **A scan never overwrites a human-set status.** `set_by_human` exists for this.
2. **Record what was matched.** `matched_files` makes a wrong call visible.
3. **Below the confidence threshold, propose nothing.** `not_received` is honest.
4. **Never delete or move client files.** Read-only, always.

**Two things the build added:**

- **Only `kind == "document"` requests are scanned.** A question is answered in a meeting,
  not by a file appearing on a drive.
- **`unmatched_files`** — files nothing asked for. A target sending unrequested material
  is a fact about the deal.

New: `services/checklist/extract.py`, `services/checklist/scan_llm.py`,
`services/checklist/prompts/scan.md`, migration `0007_add_scan_findings`.

**A scan takes 45–60 seconds** against 26 files, because every shortlisted request is
judged. The checklist page shows a pending state that says so.

**Still deferred: email reminders.** Frontend stub only, honestly badged "Not connected
yet".


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
  preview matching the table, Send disabled, and the scan walking the fixture drive
