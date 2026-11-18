# PROJECT_LOG.md

**Running log of decisions, deviations and state. Maintained by Claude; read this
first when picking the project up in a new session.**

Newest entries at the top. Each entry records what changed, *why*, and anything a
future session would otherwise get wrong.

---

## Current state — 2026-09-14

| | |
|---|---|
| **Phase 1 (intake)** | Done, committed |
| **Phase 2 (scope engine)** | Done. **Scope boundaries tightened 2026-09-14**: budgeting process not cost models, contracts and expiry not TSAs; product deck gained **product financials** and **AI readiness** rows |
| **Phase 3 (IRL + research)** | Done. Asks **questions as well as documents**; hand-editable; response upload. Research returns an **8-section business brief**, cited — the eighth being the **publicly visible technology stack** (2026-09-14); the research page was rebuilt to be scannable |
| **Phase 4 (checklist)** | Done. **The checklist page is gone** (2026-09-09) — it is all inside the IRL now; scanner built; email still deferred |
| **Phase 5 (assess)** | **COMPLETE — five of five processes defined.** P2P, O2C, Plan to Make, and **Hire to Retire and Record to Report** (2026-09-14). No process is named with nothing behind it |
| **Backend** | pytest 487/487 · ruff clean · mypy clean (85 files) |
| **Frontend** | tsc clean · eslint clean · vitest 19/19 |
| **API** | 46 routes, OpenAPI clean |
| **DB** | at `0007_add_scan_findings` |
| **Git** | `master`, at `c227afd` **plus uncommitted H2R/R2R work**. Rishi does all committing and pushing — never run `git push` |

**Uncommitted:** the two model documents, the two questionnaires, the registry flip, the
test extension and these doc updates. Everything before it is committed through the
2026-09-11 research brief and Plan to Make work.

**The Assess module's content is finished.** There is no next process to define, and the
`process_not_defined` 409 is no longer reachable through the API — see the entry below for
what that path is still for.

### Run it

```powershell
conda activate techdd
cd backend; alembic upgrade head; uvicorn app.main:app --reload   # :8000
cd frontend; npm run dev                                          # :3000
```

**`.env.local` currently points at `:8002`, not `:8000`.** An orphaned socket is holding
`:8000` (a LISTEN on a dead PID that cannot be bound or killed); it clears on reboot, after
which `.env.local` can go back to `:8000` — remember to clear `.next` when you change it.

**Two environment traps, both of which look like broken code and are not.** Both were hit
in the 2026-09-02 session:

1. **An orphaned socket.** A dead uvicorn can leave a LISTEN on a PID that no longer
   exists; `Stop-Process` cannot clear it and it does not time out. The frontend then
   renders its shell with **zero API calls and no console error**, because connections to
   that socket hang rather than failing fast.
2. **A stale Next.js build.** `NEXT_PUBLIC_*` is inlined at build time, so changing
   `.env.local` needs `.next` cleared *and* a restart. Deleting `.next` while the dev
   server is running produces an `ENOENT ... _document.js` runtime error — stop the server
   first, then delete, then restart.

**The signature for both: a blank page with no console error means the environment, not
the code.** Check the ports and the build before reading the source.

**Not in git, and intentionally so:** `shared-drive/` — the checklist scanner's test
fixtures, gitignored. Two of them, deliberately: `project-lighthouse/` (Product DD of a
SaaS company, 24 files) and `project-kiln/` (Enterprise DD of a distributor, 25 files,
added 2026-09-02). The two decks produce genuinely different request lists, so a scanner
calibrated only against Lighthouse would be tuned on half the problem. Each folder's
README records how to recreate it.

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

### What happens after the scope (Phases 3-4)

```
ScopeOfWork
  → build_seeds        irl/seeds.py       each row's `evidence` list -> seed requests
  → LlmIrlGenerator    irl/llm.py         seeds + research + intake context -> the IRL
                                          (may ADD questions, may never drop a seed)
  → render_xlsx        irl/export_xlsx.py Function | Question | Response

CompanyResearcher      research/generator.py   grounded web search; REFUSES if ungrounded
                                               feeds the IRL prompt

IRL + statuses
  → rank_questions     checklist/ranking.py    priority from the scope tier + workstream
  → build_checklist    checklist/service.py    assembled on read, never stored
```

**The same split holds throughout**: rules decide coverage, the model writes prose.
Every IRL question seeded from the scope traces back to a row a rule opened, and the
whole chain works with the LLM off — terser, never absent. Research is the one exception
and deliberately so: it refuses rather than falling back, because ungrounded "research"
is fabrication, not a degraded version of research.

### What happens after the checklist (Phase 5)

```
<process>.yaml            five of them, all defined as of 2026-09-14
  → get_questionnaire   assess/library.py   steps, questions, nudges, shape; validated
  → analyst answers     process_answer      not versioned - working notes
  → score_assessment    assess/scoring.py   weighted 0-100 index, bands, shape, pointers
  → LlmScoreGenerator   assess/llm.py       summary + BOUNDED step refinement (±1)
```

| Process | Steps | Questions | Nudges | Weighted by |
|---|---|---|---|---|
| `procure_to_pay` | 9 | 26 | 31 | transaction volume and financial exposure |
| `order_to_cash` | 8 | 28 | 30 | transaction volume and working capital |
| `plan_to_make` | 8 | 25 | 22 | the exposure each decision controls |
| `hire_to_retire` | 9 | 34 | 25 | **what breaks when the step is manual**, not volume |
| `record_to_report` | 8 | 23 | 16 | **close effort and misstatement risk**, not volume |

**Assess is the one place the model may touch a number**, on Rishi's explicit instruction.
Everywhere else it writes prose only. The deterministic score is always computed and always
stored beside the refined one — see the decision entry below for the bounds.

**Each deliverable is its own versioned child table** off `engagements`
(`scope_of_work`, `information_request_list`, `company_research`, `process_assessment_score`,
plus `irl_response`, `irl_document_status`, `process_answer` and `process_custom_question`).
Adding a module later is one more table + service + router.

**Content lives in YAML and prompt files, not Python.** A practitioner edits these
without a developer:

- `backend/app/reference/kpmg_scope/product.yaml` — 10 Product DD objectives, verbatim
- `backend/app/reference/kpmg_scope/enterprise.yaml` — 9 Enterprise IT focus areas, verbatim
- `backend/app/reference/scope_rules.yaml` — all 37 rules, weights, citations
- `backend/app/services/scope/prompts/tailoring.md` — the scope prompt, versioned
- `backend/app/services/irl/prompts/irl.md` — the request-list prompt, versioned
- `backend/app/services/research/prompts/research.md` — what the web research looks for
- `backend/app/reference/processes/*.yaml` — the five questionnaires, their weights,
  option scores, nudges and `shape` blocks
- `backend/app/reference/processes/_registry.yaml` — which business processes exist
  (no `defined: false` entry remains)

The YAML is validated at startup; a malformed file fails loudly.

---

## Decisions that override the specs

### Scope boundaries, two new product rows, and public technology research (2026-09-14)

Seven instructions from Rishi on what the generated scope covers and what the research
finds. Three of them **narrow** the scope, which matters more than the additions: a bullet
that promises work we do not do is a commercial problem, not a wording one.

| # | Instruction | Where it lives |
|---|---|---|
| 1 | IT financials reviews the **budgeting process, not a cost model** | `enterprise.yaml` EN-05, `product.yaml` PD-11, prompt Rule 2a |
| 2 | **State the financial review period** — three financial years by default | EN-05 and PD-11 bullets |
| 3 | **We do not review TSAs.** We look at contracts and their expiry | EN-09, prompt Rule 2a, `composer.py`, `investigation_questions.yaml` |
| 4 | IT org: the **in-house / outsourced mix**, skills, role structure, vendor count | EN-03 and PD-06 |
| 5 | Product DD needs **product financials** and **AI readiness** | New rows PD-11 and PD-12 |
| 6 | Organisation: **skills of the development team** | PD-06 |
| 7 | Research the **publicly available technology stack**; upgrade the research page | `research.md` v2.1, new `technology_profile` section, `research-summary.tsx` |

**The financial review period is a default, not a new intake field.** Asked where the
period should come from, Rishi chose three financial years stated in the scope text with
the practitioner overriding the row where a deal needs five years or a stub period, over
adding an intake field and a migration. So the bullets say "the last three financial
years" explicitly — the client then knows what is being asked for — and changing it is a
YAML edit.

**The two scope boundaries are enforced in the prompt as well as the content**, as
**Rule 2a**, and `tailoring.md` went **2.1 → 2.2**. The reason is the same one that put
`enforce_house_rules` behind the anonymisation rules: the row text is the model's input,
not its output, and a model asked to tailor a budgeting bullet can helpfully offer to
benchmark a cost model. Two library tests sweep **every client-facing string in both
decks** for "cost model", "TSA" and "transitional service" rather than checking only the
rows that were edited — the phrase would come back somewhere else.

**TSA was already dormant, which is why this was cheap.** Rules M4 and C7 both went
dormant on 2026-08-30 when `carve_out_or_tsa` left the intake, so no generated scope has
carried TSA language since. What remained was vocabulary: the W-SEP workstream title, the
`composer.py` specialist label ("Carve-out and TSA specialist"), and a worked example in
the prompt. All three now say contracts and expiry. **EN-09 gained the substance** — terms,
expiry, renewal dates, notice periods, change-of-control — so the carve-out question is
still asked, as a contract question.

### The AI row: found by reading the generated scope, not by the row count

PD-12 opens only where AI is material (rule A11) and is deliberately **not**
`always_in_scope`: a product with no AI must not carry a section explaining that it has
none, and the C8 injected note already covers the immaterial case.

**The first version carried `workstreams: [W-PROD, W-DATA]` and was wrong.** M6 forces
W-PROD open for *every* Product DD, so the mandatory path opened the row on every product
deal regardless of the trigger — precisely the behaviour it was written to avoid. The row
count looked plausible either way; it was visible only by generating a scope for a target
with no AI and seeing the section appear.

It now carries **`W-DATA` alone**, which is also the more honest mapping: what the row
examines is model and training-data rights, provenance and vendor dependence. W-DATA is
forced open only by M2 (sensitive data present), and an AI row on a target handling
regulated data is correct rather than spurious.
`test_g1_opens_the_ai_row_only_when_ai_is_material` pins both directions.

**PD-11 and PD-12 are additions, not KPMG source text**, and the deck says so in a comment
block. Rows 1-10 remain transcribed verbatim, and
`test_the_first_ten_product_objectives_are_still_verbatim_source_text` guards the wording
directly — a test that only counted rows would not notice an edit to one of them.

**Both new rows were rewritten after reading the deterministic output.** Each was
originally a single 60-word sentence, which the LLM path renders acceptably but the
rules-only fallback prints raw. They are now two or three short verb-led sentences. The
fallback is the audit artefact; it should read like the deck it stands in for.

### Public technology research, and why it is the most invention-prone section yet

`technology_profile` is the **eighth** brief section (`research.md` **2.0 → 2.1**). The
premise is that job adverts, engineering blogs, conference talks, open-source
repositories, status pages, partner directories and customer case studies routinely name a
stack, and that is a diligence input available **before the data room opens** — it tells
the team what to ask about, and where it later contradicts management, what to probe.

**It is also the section a model can most easily fabricate**, because a plausible stack
can be written for any company in any sector from no evidence at all. It therefore carries
a harder rule than the other seven, stated in the prompt: **name a technology only where a
source names it for this company** — not from the sector, not from the company's size, not
from what a competitor runs. An empty section is called out as the expected outcome for
many private mid-market targets.

**It goes to the IRL; `implications_for_diligence` still does not.** The distinction is
authorship: the technology profile is observed public fact about the target, which is what
makes a request specific. The implications section is the research module's own analysis,
and the request list takes its cues from the scope.

**Verified in both directions on live grounded runs:**

- **Project Kiln returned an empty technology section**, correctly — the target is
  fictional, so nothing public names its technology. Every other section populated.
- **Monzo Bank returned a cited one** (38 sources): *"cloud-native, API-driven platform...
  wide usage of open-source software"*, cited to four sources — and notably **did not**
  name Go, Kubernetes or Cassandra, which a model could trivially have guessed for Monzo.
  The restraint under exactly the conditions that invite invention is the evidence the
  rule works.

### The research page was rebuilt to be scannable

Rishi: *"upgrade the front end of the company research page, it's text and content heavy,
pointers and visualising things will be nice."* It was seven prose cards, an
undifferentiated findings list and a source list. Five changes, all presentation:

1. **A run-stats strip** — sources, findings, and brief sections present out of eight.
   Answers "how much did this run actually find?" before the reader commits; a four-source
   run and a thirty-eight-source run deserve different trust, and that was previously
   discoverable only by scrolling to the foot of the page.
2. **A jump rail** across the brief, listing the sections that exist. Which sections are
   **absent** is itself information.
3. **Section icons** — inline SVG, no icon dependency (five shapes do not justify a
   package, and the CDN allowlist would not cover one).
4. **The record is grouped by category with counts** — "Overview 5", "Market 3" — instead
   of one flat list with a pill on each row. A reader scanning for technology facts no
   longer reads every funding fact on the way, and `CATEGORY_ORDER` is typed
   `ResearchCategory[]`, so adding a category to the union is a compile error here rather
   than a group that silently fails to render.
5. **Uncited sections and findings are marked as such.** On the Kiln run this immediately
   exposed that five of eight findings and four of seven brief sections carried no
   citation — previously invisible, and on the technology section it is the whole point.

**Two responsive bugs fixed, both pre-existing on that page:** grounding-metadata source
"titles" are bare domains — single unbreakable tokens — which pushed the page sideways
(`break-all` + `min-w-0`); and the header's version line and "Run again" button sat in a
non-wrapping flex row. Phone-width overflow on the research route went **454px → 418px**.

**Phone width is not a design target for this app and was not made one.** Measured at
400px on 2026-09-14: scope 571, assess 481, IRL 478, research 418 — research is now the
best of the four. Making the whole app phone-ready is a separate piece of work and was not
started uninvited; the verification asserts research is no worse than the app's baseline
rather than pretending it is perfect.

### Verified by reading the output, not only the tests

- backend **pytest 487** (9 new) · ruff · mypy clean · frontend tsc · eslint · vitest clean
- **generated a live Enterprise scope on Kiln** (prompt 2.2) and read it: IT Financials
  says *"the technology budgeting process... over the last three financial years"*;
  IT Organisation says *"the mix of in-house and outsourced IT delivery, including team
  structure and vendor relationships"*; Contracts says *"expiry and renewal dates, notice
  periods, and change-of-control provisions"*. Swept the whole deck: **no "cost model", no
  "TSA", no "transitional service"**
- **generated a live Product scope** with AI material and read PD-06, PD-11 and PD-12. All
  three render with generic anonymised headings and expanded abbreviations — "Technology
  Organisation and Capabilities", "Technology Financials", "Artificial Intelligence
  Capabilities" — with the house rules holding
- **drove the research page in a browser**, 10 checks: the stats strip, the disclaimer
  still leading, 3 category groups, 5 section icons, 6 jump links each with a matching
  anchor, no desktop overflow, and phone overflow contained

**A trap worth recording, and it is the one the log keeps recording.** The scope YAML and
the prompts are `lru_cache`d, so **a running backend serves the old deck**. The first live
generation after editing `product.yaml` returned nine rows from the previous library and
looked like the edit had failed. Restart before reading the output — the row count and the
`prompt_version` in the payload tell you which library actually ran.


### Hire to Retire and Record to Report defined — the Assess module is complete (2026-09-14)

The last two processes. **Five of five are now defined**, `_registry.yaml` carries no
`defined: false` entry, and the "Not yet defined" badge no longer renders anywhere in the
product. `docs/reference/H2R_AUTOMATION_MODEL.md` and `R2R_AUTOMATION_MODEL.md` are the
new evaluation references, both `[EXT]`.

**Neither is a transaction cycle, and neither pretends to be.** The instruction was
explicit that §1 of each model document had to work out what kind of process it actually
is rather than opening with "this is the sibling of P2P". They are genuinely different:

- **H2R is an identity and obligation lifecycle.** Volume is trivial — 88 joiners and 71
  leavers a year against Kiln's invoice count — but each event changes four things at
  once: an HR record, a set of entitlements, a payment obligation and a legal position.
  So **weights follow what breaks when the step is manual, not volume.** Offboarding
  processes almost nothing and carries 14, because the exposure per missed event is
  unbounded. Payroll carries 16, the heaviest, because it must be right every period in
  every jurisdiction and the payroll-system count predicts separation cost.
- **R2R is a periodic close.** "Volume" barely applies at all; the currency is **days to
  close, manual journal count and reconciliation backlog**, and the weights follow what
  consumes the close and where misstatement risk sits. Reconciliations carry 16 despite
  producing no transactions. Tax carries 8 — not because it is unimportant but because it
  is largely annual and adviser-led, so it sits outside the mechanism being graded.

**The two rules that each process needed, and why they are in the option scores rather
than in prose.** Each model has one failure mode that would otherwise be scored away:

| Process | The rule | Where it lives |
|---|---|---|
| H2R | A documented offboarding process with **no measured revocation lag is a 2**, not a 4. Every management team has a checklist and the checklist evidences nothing — the failure mode is uneven execution, not absence of a process | `H2R-08-02` option scores, pinned by `test_a_documented_but_unmeasured_revocation_process_scores_as_a_two` |
| H2R | Access assigned by **copying a colleague** cannot exceed 2 whatever tooling raised the request — that is where entitlement creep begins, and it compounds | `H2R-02-01`, pinned by `test_copying_a_colleagues_access_cannot_score_as_integrated` |

These are the H2R analogue of P2M's MRP-reworked-in-Excel rule: the artefact is not the
process. **H2R is the only process in the module where the automation gap is also a cyber
finding** — joiner-mover-leaver is the mechanism every other control in the security
workstream assumes is working — so the questionnaire elicits the *measured lag in days*
and an orphaned-account reconciliation, not the existence of a checklist.

**R2R's shape note is deliberately narrower than the other four, and that was a
judgement, not an omission.** The brief said to consider whether a front/back split
carries a real commercial reading for a close and to be honest if it does not. It
partially does, so the block is written and three notes are authored — but the *even*
note says plainly that an even close is **the ordinary result** for this process rather
than a finding, because the steps of a close are sequentially dependent within one period:
a weak step 1 does not sit beside a weak step 8, it *causes* it. The two lopsided cases
are also **not mirror images**, which is the substantive difference from P2P and O2C:

- **front-loaded is the good news** — the expensive, risky part (reconciliations, journal
  control) is already right and what is manual is the reporting layer on top of
  trustworthy data, so the remediation is cheap and does not touch the ERP;
- **back-loaded is the serious one** — a polished pack on an unreconciled ledger, and the
  shape most likely to surprise a QoE team late, because the pack ties and the ledger
  does not.

`test_an_even_close_is_reported_as_ordinary_rather_than_as_a_finding` pins the honesty of
that note specifically, because it is the thing most likely to get "improved" into a
confident narrative by someone tidying the template.

**The QoE boundary is stated in R2R's §1 and it runs both ways.** This grades the
automation of the *mechanism*, not the correctness of the accounting — the same line
`O2C_AUTOMATION_MODEL.md` draws about revenue recognition. Whether a provision is adequate
is not our question; **how much of the reported result is assembled by hand** is, and it is
the measure of how much reliance the historical numbers can bear.

**DD_master was searched first and has nothing on either process.** Both §7 sections say
so explicitly rather than dressing up incidental mentions:

- HR appears only as a **data-room folder** [p. 83–84], as **"HR separation"** in the Day 1
  list [p. 253–254], and as **"IT human resources"** in the risk areas [p. 285] — the last
  of which is the IT function's own staffing, not the employee lifecycle.
- R2R has a **phrase collision worth knowing about**: **"financial close" in the source
  means *deal* close, not accounting close** [p. 5, 253] — "Day 1 (deal closed) — financial
  close; execution begins". A future session searching for close material will hit it, and
  citing it would give the model false provenance. The §7 section calls this out by name.

### Did "a new process is pure content" hold? Almost — twice, and both times honestly

The claim `PHASE5_PLAN.md` makes is that the ladder, the arithmetic, the banding, the API,
the prompt and the frontend are process-agnostic, and defining a process should touch none
of them. **For these two it held: `scoring.py`, `llm.py`, the routes and the frontend were
not edited, and the shape-note fix of 2026-09-09 was the last such gap.** Two things did
come up, and neither was a content problem:

**1. One test convention had to be respected rather than exempted.** Every scoring
question in the library has options whose scores *ascend down the list*, asserted per
process. H2R's payroll-fragmentation question (`H2R-04-02`) counts systems, where fewer is
better, so it naturally wanted to run 3,3,2,1. Rather than carve an exception into an
invariant that catches real authoring mistakes, the options were **reordered
fragmented-to-consolidated** so they ascend like everything else — which also reads better.
The ceiling is deliberately 3: a consolidated payroll estate is a *precondition* for an
automated payroll, not evidence of one, and the run itself is scored by `H2R-04-01`.

**2. Tests that asserted the old world had to be inverted, not deleted.**
`test_the_two_remaining_processes_are_named_but_not_defined` became
`test_every_registered_process_is_now_defined`, and the API 409 test became
`test_the_409_path_is_no_longer_reachable_through_the_api`. The 409 path itself is still
covered — `test_the_undefined_path_still_raises_a_409_rather_than_a_404` exercises it
against a **synthetic registry entry**, since there is no longer a real one. That matters:
the 409-not-404 distinction is what makes adding a sixth process safe, so it must stay
tested even though nothing reaches it today.

### Two gaps found by reading the output, both pre-existing, neither fixed here

Both surfaced because these are the **first scores where an LLM refinement actually moved
the index** — all three existing scores have `index == deterministic_index`, so neither
could have appeared before.

**1. The executive summary quotes the deterministic index, not the refined one.** The R2R
summary opens "an overall index of 26.0" while the stored, displayed index is 22.3. The
cause is ordering: the model writes the summary *before* its own refinements are applied,
so the only figure it can see is the deterministic one. **Not fixed**, because the fix is
in `llm.py` or the prompt — process-agnostic code this task was scoped out of — and the
harm is contained: the score view renders "Rules alone scored 26.0" directly beneath the
headline 22.3, so both numbers are on screen and reconcilable. But the summary presents it
as *the* index, which is wrong. Options when someone picks it up: have the model omit the
figure and let the UI carry it, or run a cheap second pass after refinement. **Worth
fixing; it will look like a bug to a reader.**

**2. A pointer may carry `step_key: null`.** Two R2R pointers do. This is **not a defect** —
the scoring prompt explicitly permits `"step_key": "string or null"` for a pointer about
the process as a whole — but no previous score had exercised it, so it is recorded here
before someone treats it as one.

**A third, unrelated and long-standing:** an **unregistered** process key raises
`ProcessLibraryError`, which is a plain `RuntimeError` rather than an `AppError`, so it
surfaces through the API as a **500 rather than a 404**. Previously masked because the only
wrong-key case anyone exercised was a registered-but-undefined one, which was a clean 409.
Left alone for the same reason as the others, and the test says so rather than asserting a
404 that does not happen.

### Verified by reading the output, not only the tests

- backend **pytest 475** (35 new) · ruff · mypy clean (85 files) · frontend tsc · eslint clean
- **generated real scores with the live model on Project Kiln**, 34 H2R answers and 23 R2R
  answers with remarks: **H2R 33.5 deterministic → 31.6 refined (Emerging)**, 9 of 9 steps
  assessed; **R2R 26.0 deterministic → 23.0 refined (Emerging)**, 8 of 8 assessed
- **read them.** The H2R summary led on the security finding, as the model document says it
  must, and used the analyst's own evidence — the 11-day mean revocation lag, three live
  mailboxes, the 640/651/694 headcount-payroll-AD split, 2.5 FTE, 30 hours a month of
  timesheet re-keying, the NL bureau TSA. The R2R summary used **days to close, the manual
  journal count and topside entries** — R2R's own vocabulary, not P2P's or O2C's — and
  correctly picked up the carve-out angle that the target has never reported standalone
- **the refinements did what they exist for.** R2R's journals step moved −1.0, at the bound,
  because the consultant's remark ("the group financial controller can and does post
  directly without a second pair of eyes") contradicted the option selected ("approval
  convention, enforced by practice"). That is precisely the case the ±1 rule was built for:
  the multiple-choice answer alone could not see it
- **the refined index is not reproducible run to run, and that is the accepted cost.**
  Re-scoring gave v2 at 28.8 and 22.3 against v1 at 31.6 and 23.0, while the **deterministic
  figures were identical at 33.5 and 26.0**. Versioning is why this is safe; the decision
  entry of 2026-09-02 records the trade
- **drove it in a browser**, 34 checks: five processes with **zero "Not yet defined"
  badges**, 9 and 8 step sections, 137 and 103 options, 48 and 32 remarks boxes, 26 and 19
  saved answers restored after reload, both authored shape notes rendered with their
  measured means, both step tables complete with each refinement showing its reason, the
  deterministic figure shown beside each refined index, and a **nudge revealing live on
  selection** with its FOLLOW UP badge — the unmeasured-revocation follow-up asking for the
  last ten leavers
- the nudge check ran on a **scratch engagement** that was deleted afterwards, since driving
  a questionnaire in a browser writes real answers

**Two selector traps cost time and are worth recording.** The score view's tabs are **plain
buttons, not `role=tab`**, and `getByRole("button", {name: /score/i})` matches **"Score this
process"** — the generate action — before **"Score & summary"**, so the view silently never
switches and every score assertion fails while the questionnaire ones pass. Match the exact
label. Separately, a nudge's text is **truncated in the rendered line**, so asserting on a
phrase from the middle of it fails; assert on the opening.


These were Rishi's calls. **Do not "fix" them back.** `CLAUDE.md` outranks
`docs/phases/PHASE2_SPEC.md`, and a later instruction outranks both.

### The checklist page was deleted into the IRL (2026-09-09)

Rishi: *"remove the checklist page and add all the features into the IRL page itself."*

The split had been defensible while the checklist was only a progress view — one screen
to record, one to chase. The shared-drive scan ended that: it writes follow-up questions,
document types and matched filenames that only mean anything **next to the request they
belong to**. The scan ran on the checklist page and its output appeared on the request
list. Two pages for one dataset had become one page for the button and another for the
result.

Everything moved and nothing was dropped:

- **progress** → a sticky summary rail with the collection percentage, a stacked
  received/partial bar, and the follow-up count;
- **the scan button and its pending state** → the rail's action group;
- **the reminder stub** → a collapsed section at the foot of the IRL, still honestly
  badged "Not connected yet". Rishi chose to keep it rather than delete it: PHASE4_PLAN
  records it as deferred-in-scope, and deleting it would have quietly dropped a planned
  feature along with its wiring notes.

`ChecklistTable` and `ChecklistLegend` were deleted outright — both had already been dead
code since per-request editing moved into the IRL on 2026-09-02. The `/checklist` route,
its nav entry and its link on the engagement overview are gone. **The backend was not
touched**: `GET/PATCH/POST /checklist` still exist and the scan still writes through them,
because the IRL reads its tracking from the same table. This was a presentation change.

### The shape note moved from code into YAML (2026-09-09)

Defining Order to Cash was supposed to be pure content — `PHASE5_PLAN.md` §5 of "Adding
the next process" says so explicitly, and it was almost true. One thing was not:
`scoring.py::_shape_note` hardcoded `sn <= 3` / `sn >= 7` (a nine-step assumption) *and*
P2P's vocabulary. An O2C score would have carried a shape note about "the requisition and
approval end", "the invoice and payment end" and "a procurement tool bought and never
fully rolled through to accounts payable".

Rishi chose to move the prose into YAML rather than reword it in code or force O2C to nine
steps. An optional `shape` block on the questionnaire now declares the front and back step
ranges and the three notes; `_shape_note` reads it and appends the measured means. **A
questionnaire without a `shape` block falls back to exactly the previous behaviour**, so
P2P is untouched and still declares none.

Why this is the right cut: the *arithmetic* of a shape is process-agnostic — compare the
early steps against the late ones — but the *commercial reading* is not. In P2P a
front-loaded cycle means a procurement tool that never reached accounts payable. In O2C it
means the working capital problem grows with revenue. That judgement is domain content and
belongs beside the weights a practitioner already edits.

This should be the last edit a new process needs to process-agnostic code. Plan to Make,
Hire to Retire and Record to Report are now genuinely content-only.

### The IRL now asks questions, not only requests documents (2026-09-02)

Rishi: *"an IRL won't just be asking you for documents, it will ask some questions also."*
Correct, and the engine was structurally incapable of it.

**What the research found.** `DD_master.md` §6 states that every workstream carries
**"areas of investigation (sourced questions where available)"** *and* **"evidence
requests"** — two distinct outputs. The seed builder read `evidence` and discarded the
questions, so the list asked for artefacts and never asked management to explain anything.
**50 page-cited questions across 7 workstreams were sitting unused.**

The book is also explicit about why they belong in the *list* rather than being saved for
the interview, and the reason is the target's patience, not convenience:

- *"prioritise questions because time with management is limited; avoid repeating
  questions across sessions"* [p. 84-85]
- *"do not go back repeatedly — the seller can become overwhelmed and even ultimately
  unresponsive"* [p. 83]

A question left out of the list costs a follow-up round the source warns against spending.

**Web research was checked and mostly did not help.** Generic M&A IRL guidance (legal,
financial) really is document-only — that convention is why the original design looked
reasonable. Tech-DD sources frame the work as *"establish the key questions to
investigate"* alongside evidence, but the public checklists turned out to be topic lists
rather than actual questions. `DD_master` is the better source here and the build leads
with it.

**What changed.** A seed now carries `kind`: `document` or `question`.
`reference/investigation_questions.yaml` holds the sourced questions with their page
citations; a scope row inherits the questions of its workstreams exactly as it inherits
its evidence. The workbook gained a **Type** column (Rishi's choice over separate sheets),
and tracking is kind-aware — "Received completely" against a prose answer is nonsense, so
questions read "Answered / Partially answered / Not yet answered" and have no document-type
field. The stored values are identical, so the checklist and the future scanner are
unaffected.

**Two bugs caught by reading the output rather than the counts:**

1. **Questions were asked up to three times.** `questions_for` de-duplicated within a row
   but not across rows, and three enterprise rows carry W-APP. That is precisely the
   "avoid repeating questions across sessions" failure. A question is now asked once, on
   the first in-scope row carrying its workstream.
2. **Markdown leaked into the client-facing text** — `**Application landscape**: What
   are...`. W-APP formats its questions as bold-labelled bullets *packing several questions
   into one*. The label is stripped and the bullet split, because three questions in one
   row means the client answers the first and skips the rest.

**The leading-question rule is the model's job.** The sourced questions are written as
internal research prompts, and several are leading as written — *"Is IT managed to deliver
value to the business?"* is exactly what p. 84-85 tells you not to ask. Prompt v3.0 carries
the book's own worked example and instructs the model to rephrase while keeping the
subject and the citation. On the live run **0 of 55 questions opened with a yes/no verb**.

**Five workstreams have no sourced questions** (W-SEC, W-DATA, W-SEP, W-INT, W-PROD).
Rishi chose "LLM writes them, marked as generated" over leaving those areas document-only.
They are listed in the YAML with an empty set so the gap is visible, and named to the model
as `unsourced_workstreams` so it writes questions there rather than assuming coverage.
Adding sourced questions later upgrades them with no code change.

**Verified on a live generation**: 90 requests — 35 documents, 55 questions (43 sourced,
12 model-written); zero leading questions; zero duplicates; zero markdown; no party names
leaked; every sourced question carrying its page. In the browser: 35 DOCUMENT and 55
QUESTION badges, 43 citations rendered, and a question row correctly showing "Not yet
answered" with no document-type field.

**The stale-cache trap bit again, differently.** `NEXT_PUBLIC_*` is inlined at build time,
so pointing `.env.local` at a different backend port needs `.next` cleared *and* a
restart — otherwise the page renders "Couldn't load" with **zero API calls**. Same
signature as the orphaned-socket case recorded below: a blank page with no console error
means the environment, not the code.

### Tracking moved into the IRL; Assess answers gained remarks (2026-09-02)

Two instructions from Rishi.

**1. The checklist's per-request tracking now renders inside the IRL.** Status, document
type and remarks sit beside each question, so the analyst works one screen instead of
cross-referencing two.

**Storage did not merge, and that is deliberate.** `irl_response` is what the *client*
wrote; `irl_document_status` is what the *deal team* observed. Different authors,
different lifecycles, and the shared-drive scanner will write status without touching a
client's typed answer. Merging the tables would have destroyed a distinction the scanner
depends on. Only the presentation merged: `IrlRead` gained a `tracking` map assembled on
read, exactly as the checklist already assembled its items.

**Priority is computed, never stored** — the IRL and the checklist both call
`rank_questions`, so the two views cannot disagree. `test_the_checklist_and_the_irl_agree_on_status`
pins it.

**None of it reaches the client workbook.** Status and remarks are the team's assessment
of the target's responsiveness; exporting them would hand the target our view of them.
`test_tracking_never_reaches_the_client_workbook` writes a sentinel string into remarks
and asserts it is absent from every cell of the export.

Asked what should happen to the checklist page, Rishi chose **"keep it, but strip it to
the reminder/summary only"**. It is now the chase-progress view: header counts, the email
reminder preview, and a link to the request list. Two views of one dataset is fine; two
places to *edit* it is how they drift. The `PATCH /checklist/{id}` endpoint was left in
place — the scanner will write through it, and removing it would take the scanner's
contract with it.

**2. Assess answers gained a remarks field.** Rishi: an option alone is not evidence.
"Data ingested" is the answer; *where from, by whom, how often* is what makes it
defensible in a report.

A column on `process_answer` rather than a second table — a remark has no meaning without
the answer it qualifies, and they are always written and read together. Migration
`0006_add_answer_remarks`.

`AnswerWrite` now takes `value` and `remarks` as **independently optional**: `None` means
"leave this field alone", an empty string clears it. The option and the remark are edited
by separate controls, so saving one must never wipe the other —
`test_saving_a_remark_never_clears_the_option` pins both directions.

**Remarks never move the deterministic score.** Scoring reads the selected options alone;
remarks reach the model as `consultant_remarks` and shape the narrative only. The scoring
prompt went 1.0 → 1.1 to say so, and to note that remarks *do* count as free-text evidence
for the ±1 refinement rule — they are often exactly where a contradiction shows up.

Asked where the box should appear, Rishi chose **"appears once an option is selected"** —
a remark before an answer has nothing to qualify, and 20 empty boxes would bury the form.

**Verified live, not only by tests**: set status/type/remarks through the API and
confirmed a status-only write kept the remark; exported the workbook and confirmed five
columns with no status or remarks text anywhere in it; saved an Assess remark, changed the
option, and confirmed the remark survived. In the browser: 46 rows with 46 status
selects, 46 priority badges and 92 textareas, the stripped checklist pointing at the IRL,
and 20 remarks boxes on the questionnaire.

**A trap worth recording.** A dead uvicorn left an orphaned listener on :8000 that never
released — `Get-NetTCPConnection` showed a LISTEN on a PID that no longer existed, and
`Stop-Process` could not clear it. The frontend then rendered its shell with **zero API
calls and no errors**, because connections to that socket hang rather than failing fast.
A blank page with no console error is the signature: check the port before the code.

### The IRL is editable, follows the SOW's headings, and reads responses back (2026-09-02)

Three instructions from Rishi.

**1. Add, edit and delete requests.** `POST /irl/questions`, `PATCH /irl/questions/{id}`,
`DELETE /irl/questions/{id}`. An edited question keeps the engine's wording in
`original_question` and is flagged `edited_by_human` — the same pattern the scope rows use
for overrides, so a reviewer can always see what a person changed. Deleting takes the
question's response and document status with it; an orphan response would be silently
resurrected by a later regeneration.

All three mutate `payload_json`, which is the shallow-copy trap already recorded below.
`_rewrite_payload` deep-copies and calls `flag_modified`, and the tests re-fetch from the
API rather than trusting the response.

**Manual work survives regeneration.** Rishi chose "carry them forward, keep edits" over
resetting. Added questions are re-appended; reworded ones keep the analyst's text with the
fresh generation stored as `original_question`. The trade, stated: an edited question can
drift out of step with a scope that has since changed. It is visibly flagged, and that is
the lesser harm against discarding someone's rewording.

**2. The IRL now groups by scope area.** Asked whether "follow the SOW's functions" meant
the deck's headings or the owning business function, Rishi chose **both**: the workbook
went from three columns to four — **Scope Area | Function | Question | Response**. Grouping
is by scope area, so every request sits under the area that opened it; `function` stays as
who answers, which is what makes the sheet routable.

`seed.row_title` was already the scope area, so provenance and grouping became the same
fact. Seeded questions take it from their row and **never from the model** — letting the
model reassign one would break the traceability the grouping exists to show. Model
additions covering HR, Legal and Finance land under "Additional requests", sorted last.

`_functions_of` had to change with it: it fed `payload.functions` back to the model as
"previous function names", and that list now holds scope areas. It reads the questions'
`function` field instead. Feeding scope areas back would have told the model to name its
owner column after the deck's headings — exactly the confusion the split exists to avoid.

The IRL prompt went **1.0 → 2.0** and gained the scope deck's house language rules: never
name a party, expand abbreviations (but not IT/HR/CRM), one request per question, open with
Provide/Confirm/Describe.

**3. Completed workbooks upload and auto-fill.** `POST /irl/import` reads the Response
column. Three rules carry the weight:

- **Matching is by request id first.** The export writes a hidden `Request ID` column, so a
  row matches even after the client reorders rows or rewords a question. The fallback is
  *exact* normalised question text — deliberately not fuzzy, because a near-miss that
  attaches an answer to the wrong request is the failure this must not have.
- **A blank cell never clears an existing answer.** The client leaving a cell empty means
  "not answered yet", not "delete what you have".
- **Unmatched rows are reported, not dropped.** An import that silently matched nothing
  looks identical to one that worked, and the analyst would not find out until they read
  the checklist.

**Test fixture**: `shared-drive/project-kiln/Kiln-IRL-COMPLETED-response-sheet.xlsx` — the
real 46-request Kiln list with 41 answered and **5 deliberately left blank**, so the
blank-cell rule is exercised rather than assumed. Gitignored with the rest of
`shared-drive/`.

`openpyxl` moved from a test-only to a runtime dependency, and `python-multipart` was added
for the upload.

**Verified by running it**, not only by tests: uploaded the dummy sheet against the live
API — 46 matched, 41 updated, 5 blanks skipped, 0 unmatched — then re-uploaded and confirmed
it changed nothing. Added, edited and deleted a question through the API and confirmed the
export reflected each immediately. In the browser: four columns, 46 rows, 41 response boxes
populated, Edit/Delete on every row, and the scope-area headings matching the deck's.

### The deck is anonymised, plain and shallow — enforced in code (2026-09-02)

Seven instructions from Rishi on the generated scope of work. Prompt `tailoring.md` went
**1.0 → 2.1**, and the load-bearing ones are enforced in `services/scope/llm.py` as well,
because a prompt is guidance and a deck that names the client is a real problem.

| # | Instruction | Where it lives |
|---|---|---|
| 1 | Headings generic, specifics in the bullets | Prompt Rule 2 |
| 2 | Never name the target or investor — "the Target", "the Acquirer", "the Parent" | Prompt Rule 1 **+ `_scrub_names`** |
| 3 | Plain language; expand abbreviations | Prompt Rule 3 |
| 4 | Bullets short, specific, shallow unless the deal asks for depth | Prompt Rule 4 |
| 5 | Open with Review/Assess/Evaluate/Identify, never "Gain" | Prompt Rule 5 **+ `_enforce_verb`** |
| 6 | Sequencing, cost and team → XXX | `export_pptx.py` |
| 7 | Drop the PDF and Markdown exports | Routes + frontend |

**Corrected on the same day, after Rishi checked the app.** The first pass got two of the
seven wrong:

1. **Sequencing/cost/team were only removed from the deck**, not from the on-screen scope
   document — `scope-document-v2.tsx` still rendered all three sections in full. Both
   surfaces now show the same Delivery approach table of XXX. The lesson is the one this
   log keeps recording: a change to "the SOW" means *every* surface that renders it, and
   checking only the artefact I happened to be editing is not checking.
2. **"Bullets" meant bullet formatting, not sentence length.** I read Rule 4 as being about
   brevity and rewrote the prose accordingly, but the lines were still rendering as plain
   paragraphs in all three exports. They are now `•` glyphs in the deck, `<li>` in the
   on-screen document, and `- ` in the Markdown. Both readings were wanted; only one was
   delivered.

**Names are scrubbed, not rejected.** A single leaked name should not discard an otherwise
good scope and fall back to the generic deterministic text — that is a worse document, not
a safer one. `enforce_house_rules` runs after `apply_tailoring`: it replaces names in the
summary and bullets, **strips** them from titles (a heading naming a party is wrong even
anonymised), and rewrites banned openers.

`_name_variants` also derives short forms — "Kiln Industrial Supply" leaks as "Kiln" — but
only where the first token is ≥4 characters and not generic, and matching is
``-anchored so "kilnworks" survives untouched. `test_a_word_merely_containing_the_name_is_not_scrubbed` pins that.

**The deal codename stays.** "Project Kiln" still appears in the running header — it is the
anonymising device deals already use, and stripping it would leave the deck with no
identifier. Only the *company* name is scrubbed. Verified: 7 occurrences in the deck, all
the codename, none the company.

**Sequencing/cost/team became one "Delivery approach" slide** with every value XXX, rather
than being dropped. An absent slide reads as "not applicable"; a slide of XXX reads as "not
yet decided", which is the truth — these are judgement calls the engagement team makes. The
data is still computed and still in the payload and Markdown export.

**Exclusions were rescued.** They shared the old Team slide, so removing it would have
silently dropped them — and DD_master G4 requires a scope to state what it does not cover.
They now have their own slide.

**PDF removed entirely** (`export_pdf.py`, its route, its tests, the `reportlab` pin and two
mypy overrides). **Markdown kept but unexposed**: it is the only artefact carrying the audit
trail — the signals, rule provenance and tier reasoning — so it is still served at
`/scope/export` with no button. `pillow` stays: python-pptx requires it.

**Two traps hit while doing this:**

1. A heredoc turned every `` in the new regexes into a **literal backspace byte** (0x08).
   The patterns parsed and the tests would have passed, but the name scrub would silently
   never match. Found by inspecting the file with `cat -A`. 14 occurrences fixed.
2. The first regeneration came back unchanged at `prompt v1.0`: `_load_prompt` is
   `lru_cache`d and uvicorn's `--reload` had not actually restarted. Restarting on a clean
   port fixed it. **If a prompt edit appears to do nothing, restart the process** — the
   version in the payload tells you which prompt actually ran.

**Verified by reading the regenerated scope**, not only by tests: no party names, zero
"information technology (IT)" expansions after the IT/HR/CRM exemption was added, no banned
openers, bullets averaging 14 words against a 25-word target.

### The model may move a step score in Assess — bounded (2026-09-02)

**The one place the model touches a number.** Everywhere else in this platform rules decide
and the model writes prose. Asked which he wanted for process scoring, Rishi chose *"LLM
also refines step scores"* over *"deterministic score, LLM writes summary only"*.

I flagged the cost before building: a refined index is **no longer perfectly reproducible**
from the answers, so re-scoring the same evidence can give a different number and the audit
trail weakens. Rishi's call stands; the cost is contained rather than accepted wholesale:

| Guard | Why |
|---|---|
| Deterministic score always computed and stored, on the payload *and* every step | A reader can always put the rules number back |
| Adjustment bounded to **±1** | A larger disagreement means the answers are wrong — that is a probe, not a silent edit |
| Reason required, ≥20 characters, citing the evidence | A colour or a number with no explanation is not auditable |
| Unassessed steps cannot be refined | No evidence means no score, not a guessed one |
| More than 3 refinements → **all** dropped | Moving many steps is second-guessing the ladder, not reading evidence |
| Rejection is per-adjustment | One bad refinement must not discard a good summary |

Rejections are logged with the reason. On the first live run the model refined **nothing** —
it read the free text, found it consistent with the multiple-choice answers, and left the
arithmetic alone, which is what the prompt says the expected outcome is.

**If this ever needs reverting**, it is one change: pass `RulesScoreGenerator` instead of
`LlmScoreGenerator` in `services/assess/service.py::_generator_for`. The summary degrades to
the deterministic one; nothing else moves.

### Assess is internal-facing, with the export seam left open (2026-09-02)

Asked who the score is written for, Rishi chose *"internal now, exportable later"*. So the
score view is frank and diagnostic — it names weak spots plainly and tells the analyst what
to probe next — rather than being written in the KPMG client voice the SOW deck uses.

A PPT/PDF export in the house voice is the obvious next step and the payload already carries
everything one would need. It was **not built rather than guessed at**, the same treatment
the shared-drive scanner got.

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

**`critical` is unreachable on an Enterprise engagement.** The checklist ranker reserves
`critical` for rows carrying `W-SEC`, `W-PROC` or `W-DATA` (Phase 4, calibrated against the
Product-deck Lighthouse list). But `reference/kpmg_scope/enterprise.yaml` has **no row
carrying any of those** — its nine focus areas are Applications, Strategy, Org,
Infrastructure, Financials, Projects, SDLC, Emerging Tech and Contracts. Product carries
them on 3 of 10 rows; Enterprise on 0 of 9.

So an Enterprise checklist tops out at `high`, however sensitive the deal. Observed
2026-09-02 on Project Kiln — a carve-out with GDPR data and a disclosed ransomware
incident — which produced `{high: 9, medium: 14, low: 20}` and not one critical item.

**This is a content gap, not a ranker bug**, and it traces back to the KPMG source deck:
the Enterprise section genuinely has no standalone security or privacy focus area. Two
honest fixes, both a decision for Rishi rather than something to pick silently:

1. Add a Security & Compliance focus area to `enterprise.yaml` — departs from the verbatim
   source deck, which `CLAUDE.md` §9 currently treats as authoritative.
2. Widen the ranker so Enterprise rows escalate on other evidence (regulated data in the
   intake, a disclosed incident) rather than on the workstream tag alone.

Left alone because it is outside what was asked and because option 1 changes transcribed
client content. Raise it before anyone runs a real Enterprise engagement and reads the
colour coding as meaningful.

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

### 2026-09-11 — A real company research brief, and Plan to Make

Two pieces of work, and the first turned up a bug that had been live since the research
module was built.

#### 1. Company research now produces a business brief

The old output was a 3-6 sentence summary and a flat list of findings: it answered "what
is on the record" but not "what does this company actually do, for whom, in what market".
A tech DD scope is a function of the business model, so that was the wrong thing to be
missing.

`business_brief` is a new optional block on the payload with seven cited sections:
executive summary (2-3 paragraphs), what they do, how they make money, customers and
markets, the sector, competitive position, and what it means for the diligence. Prompt
version 2.0. Optional so runs stored before today still load, and **any section the
sources do not support is omitted** rather than padded — the prompt is explicit that an
honest gap beats invented sector commentary.

The brief feeds the IRL generator too, so requests are specific to the business rather
than generic to the sector. `implications_for_diligence` is deliberately **excluded** from
what the IRL sees: it is the research module's own analysis, and letting it steer the
request list would have the IRL taking cues from a model's opinion rather than from the
scope the rules produced. It is the only analytical section and the UI labels it as such.

#### 2. The citation bug — **every run ever produced had zero citations**

Found by reading a live run, not by a test. Source ids (`S1`, `S2`, …) are assigned by
`generator.py` from the grounding metadata that comes back *with* the response — so at the
moment the model writes its answer, the ids do not exist and it cannot cite them. Every
`source_ids` array was empty on every finding of every stored run; the per-claim source
links rendered nothing and only the list at the foot of the page worked. It affected the
Kiln and Meridian runs equally, so it predates today's work entirely.

Fixed with a second, cheap model call: hand the model its own text alongside the now
numbered sources and ask only "which of these supports each claim?". No search tool on
that pass, so JSON output can be forced; temperature 0. It adds no new claims, and **if it
fails the run is still stored uncited** — a degraded research note is worth having, one
that was never stored is lost. Verified live: 10/10 findings and all seven brief sections
cited, where every previous run had none.

One limitation worth knowing: Gemini's grounding metadata gives only the **domain** as a
source title and the URLs are opaque redirects, so five pages on rsgroup.com all render as
"rsgroup.com". The source id is now shown beside each link so they can at least be told
apart and found in the list below.

#### 3. Plan to Make — the third Assess process

`docs/reference/P2M_AUTOMATION_MODEL.md`, eight steps summing to 100, heaviest on MRP (15)
and demand planning (14). `plan_to_make.yaml` has 25 questions (19 scoring) and 22 nudges.

Three things make P2M genuinely different from P2P and O2C, and the model document says so
rather than pretending the template fits:

- **It is a decision cycle, not a transaction cycle.** The cost of being wrong is
  inventory and service level simultaneously, not FTE effort.
- **A high rung is only credible if the output is used.** A configured MRP run whose
  output is exported to Excel, reworked and re-entered scores **2, not 3** — the system
  proposes and a human decides. That option is pinned by its own test, because scoring it
  as integrated would let a licence stand in for a working process.
- **It need not apply in full.** A distributor or service business has no scheduling, shop
  floor or quality process; those steps are left unanswered and their weight redistributes.
  A test covers exactly that case, because the alternative is an analyst inventing answers
  to make the questionnaire look complete.

**Verification.** pytest 440 (33 new) · ruff · mypy clean (85 files) · tsc · eslint clean.

**Read the generated score.** 35 answers on Kiln as a back-loaded distributor-assembler:
index **37.6 (Emerging)**, 8/8 steps assessed, planning at 0.7-1.0 against a floor at
2.5-3.7. The authored shape note survived with its measured means (front 0.9 / back 3.1)
and no P2P or O2C vocabulary leaked. The summary used the real evidence — the single demand
planner, three days a month assembling S&OP packs, the one-third override rate, the EUR
2.2m provision — and the model made the inference the model document says a reader should:
it attributed the growing provision to the demand-planning weakness rather than to the
inventory step, which scored well.

**Browser:** 2 honest "Not yet defined" badges, 103 options, 34 evidence and remarks
boxes, the score view with its 8-row table and ascending bar pattern making the shape
visible at a glance. No console errors.

### 2026-09-09 — One screen: the checklist folded into the request list

**What changed.** The `/checklist` route is deleted. Everything it did now happens on the
IRL page, which was rebuilt around the fact that it is the screen an analyst lives in.

**The table became cards.** The old five-column table was already 1,500px wide, and the
scan had just added follow-up questions, matched filenames and a reasoning line to every
row. A sixth column would have made a horizontal scrollbar the primary navigation. Each
request is now a three-column card — the request and its follow-ups on the left where
reading happens, the client's response in the middle, the team's own tracking on the
right where deciding happens — grouped under collapsible scope areas, with a coloured
left edge so status is legible without reading a word.

**New components:** `irl-summary-rail.tsx` (sticky header, progress, all whole-list
actions), `irl-request-card.tsx`, `irl-request-list.tsx` (grouping, filters, search).
`irl-table.tsx`, `checklist-table.tsx` and `checklist-legend.tsx` are gone — the last two
had been dead code since 2026-09-02.

**Filters answer the question an analyst actually arrives with:** All / Outstanding /
Needs follow-up / Received / Documents / Questions. "Needs follow-up" is the one that
matters — it is the chase list, and it did not exist before.

**Three problems found by rendering it and looking, not by a test:**

1. **Client responses were clipped mid-sentence.** `rows={2}` on a fixed textarea showed
   "Last refreshed March…" with no indication there was more, which is worse than a long
   row because the reader cannot tell anything is missing. Added `lib/use-autosize.ts`,
   bounded so one pasted email cannot push the next request off screen.
2. **Empty remarks rendered as grey slabs.** `TextArea`'s own `min-h-[104px]` is emitted
   in the same Tailwind layer as the `min-h-0` override, so the taller value won and
   ninety empty boxes were the loudest thing on the page. Fixed with `!min-h-0`; empty
   remarks are 47px now and grow on content.
3. **Search lied about spelling.** Typing "licence" returned **nothing** against nine
   matching requests — the model writes the list in US English while the team searching
   it is British, and the drive's own filenames are British too. Search now folds the
   common pairs and also covers the document type and matched filenames, so "licence"
   finds the row the scan filed under `Software-Licence-Inventory-SAP.xlsx`. "SAP" went
   from 11 matches to 13 for the same reason.

**Verification.** tsc · eslint · `next build` clean, `/checklist` absent from the route
list. Backend pytest 407 unchanged — nothing server-side was touched. Browser: the rail
with its six stats, 6 filter chips, search, collapsible groups (90 → 74 cards on collapse,
back to 90), 11 follow-up blocks, 19 auto-written document types, the "why this status"
disclosure revealing the matched filename, and no console errors.

**A trap for the next session:** deleting a route leaves stale types in `.next` and `tsc`
fails on a module it cannot find. Stop the dev server, `rm -rf .next`, re-run. That is the
environment, not the code — as already recorded for blank pages.

### 2026-09-09 — The shared-drive scanner, and the follow-up questions it writes

**What this closes.** The scanner was the oldest deferred item in the project: the stub
had held the contract and its four rules since Phase 4 while the endpoint returned 501.
It now walks the drive for real, and it does the thing the stub never promised — it
**reads each document and writes the follow-up question when what arrived is not enough**.

**The three outputs Rishi asked for**, all written automatically per request: the
**document type** ("Policy", "Architecture diagram", "Org chart"), the **receiving
status**, and the **follow-up questions** where a document is partial.

**How it decides — two stages, and the split is the point:**

1. **Deterministic shortlisting.** Token overlap between the filename, its folder and the
   request's own text picks up to four candidates per request. Cheap, reproducible, and it
   is what bounds the prompt — the model never sees 26 files against 90 requests.
2. **A model judgement per shortlisted request.** Given the candidates' names *and content
   excerpts*, it decides the status, names the document type, and writes the follow-ups.

**New files:** `services/checklist/extract.py` (read-only text extraction),
`services/checklist/scan_llm.py`, `services/checklist/prompts/scan.md`. Migration
`0007_add_scan_findings` adds `follow_up_questions`, `scan_reasoning` and `scanned_at` to
`irl_document_status`. `python-docx` added to `requirements.txt`.

**Rishi's three decisions** (asked before building, because they shape the schema):
follow-ups live on the status row rather than becoming real IRL requests; the extractor
reads xlsx/docx content rather than filenames alone; and the scan **writes** statuses
rather than only proposing them.

**The four rules from the stub, all kept and all tested:** a scan never overwrites a
`set_by_human` row; `matched_files` records what a status was inferred from; a
below-threshold match proposes nothing; the drive is never written to.

**Two things the design adds beyond the ask:**

- **Only `kind == "document"` requests are scanned.** An IRL also asks 55 questions on
  Kiln, and a question is answered in a meeting, not by a file appearing on a drive.
  Scanning them would mark them received the moment anything related turned up.
- **`unmatched_files`** — files nothing on the list asked for. On the fixture this
  surfaced the parent recharges, the ransomware summary and the headcount extract: real
  files that map only to *question*-kind rows, so a target sent material nobody requested.
  That is a fact about the deal, not noise to discard.

**Four bugs, three of them found by running it rather than by a test.**

1. **The first matcher matched 1 request in 35.** `_score` divided the overlap by the
   *request's* token count. A request is a sentence and a filename is three words, so it
   punished exactly the filenames that were obviously right —
   "Application-Inventory-SAP-and-Bolt-ons.xlsx" scored 25% against a request for an
   application inventory. Now measured against the **smaller** of the two sets, with a
   floor for two or three distinctive shared terms. 23 of 35 matched immediately after.
2. **The fixture's .xlsx and .docx files are plain text with Office extensions.** Real
   parsing raised `BadZipFile` on every one. `extract.py` now falls back to reading a
   mislabelled file as text, guarded by a printable-ratio check — which is also correct
   for real drives, where wrong extensions are ordinary.
3. **`ChecklistTable` is dead code.** The follow-up UI went in there first and rendered
   nowhere: per-request editing moved to the request list on 2026-09-02, so the checklist
   page is a summary only and nothing imports that component. Reverted, and the UI moved
   to `IrlTrackingCell`, which is what the analyst actually looks at. **Found by driving
   the browser** — the tests would never have caught it.
4. **A degraded scan looked identical to a good one.** Gemini returned a 503 mid-session;
   the fallback worked exactly as designed and logged `rules (llm failed)`, but the toast
   said only "26 files read · 16 requests updated". A consultant would have trusted a
   filename-only pass as though the documents had been read. The toast now says so
   explicitly and shows as an error.

**Verification.** pytest 407 (19 new) · ruff · mypy clean (85 files) · tsc · eslint clean.

**Read the actual output**, against `shared-drive/project-kiln`: 26 files, 35 document
requests, 25 updated, 19 follow-ups. The judgements discriminate — the fixture's
deliberate traps were all rejected with a stated reason (customer contracts → helpdesk
SLAs, employment agreements → DPAs, SDLC tools → the SAP licence inventory, PII data flow
→ the data-centre inventory), and `Infrastructure-Monitoring-2026Q1-ONLY.xlsx` came back
partial with a follow-up naming Q1 2026 and offering the "or confirm earlier data is not
retained" form the prompt asks for.

**Drove it in a browser:** the scan button, a pending state that explains the ~45-60s
wait, a toast reporting the walk, then on the request list 10 follow-up blocks, 18
auto-written document types, statuses split 9 partial / 7 complete / 19 not received, and
matched filenames with the scan's reasoning beneath each status. No console errors.

**A trap worth knowing:** a full scan takes **45–60 seconds** against 26 files, because
every shortlisted request is judged. A browser check that waits 15 seconds sees a button
stuck on "Reading the drive…" and looks like a hang. It is not.

### 2026-09-09 — Order to Cash: the second Assess process

**What this proves.** Phase 5 claimed a new process would be pure content. Defining O2C
tested that claim, and it was *almost* true — one genuine coupling point surfaced, and it
was found by reading generated output rather than by a failing test. Twice.

**The artefacts, in the order the plan prescribes:**

1. `docs/reference/O2C_AUTOMATION_MODEL.md` — written first, because scoring reads from it.
   **Eight** L1 steps, not nine: O2C has no equivalent of the sourcing event, and credit
   assessment and customer master data are one decision in practice. Weights sum to 100,
   heaviest on Invoicing & billing (18) and Cash application (15) — highest volume, and
   directly working-capital-bearing. Marked `[EXT]`.
2. `backend/app/reference/processes/order_to_cash.yaml` — 28 questions (21 scoring, 7
   free-text) and 30 nudges across the 8 steps, plus the `shape` block.
3. `_registry.yaml` — `defined: true`.
4. `tests/test_assess.py` — the three library invariants are now parameterised over both
   processes; 25 new tests, 388 passing overall.

**DD_master.md has nothing on order-to-cash.** Searched for order-to-cash, revenue,
billing, collections and credit before writing a word. The only adjacent material is
incidental: customer terms, customer-specific pricing and revenue-recognition policy in the
Day 1 data-protection list [p. 519], and "take orders, invoice customers, deliver product"
as an example at §3. Neither is a process model. The content is therefore `[EXT]` and says
so — it is **not** dressed up with page cites it does not have.

**Two bugs found by reading the generated score, not by tests.**

1. **The model was overwriting the authored shape note.** `llm.py` assigned
   `payload.shape_note` from the model unconditionally. The first real O2C score came back
   with the model's own paraphrase — "the cycle deteriorates from fulfilment onwards" —
   which discarded both the authored commercial reading *and* the measured `(front 2.9/5,
   back 1.0/5)` that evidences it. The YAML `shape` block would have been invisible in the
   one artefact anyone reads. Fixed: where a questionnaire declares a `shape` block, that
   block wins and the model writes prose only. Where it does not (P2P), previous behaviour
   is unchanged. Two tests now pin both halves.
2. **The model invented a vendor.** The first summary said "the licensed SAP billing
   capability" where the analyst's evidence said **Dynamics 365**. The scoring prompt bans
   inventing *numbers* ("Never invent a number") but says nothing about names, so a
   fabricated system name passes every check. **Not fixed — flagged for Rishi**, because
   tightening the prompt is a product decision, not a typo. It did not recur on the second
   run, which makes it harder rather than easier to catch: it is intermittent, so looking
   once proves nothing.

**Verification.** pytest 388 · ruff clean · mypy clean (83 files) · tsc clean · eslint
clean. `black --check` reports 37 files it would reformat, including files untouched by
this work (`test_irl.py` among them) — the repo is not black-formatted as a baseline, so
nothing was reformatted.

**Read the actual output**, per the plan. Answered all 40 O2C questions on Project Kiln
through the API as a front-loaded distributor — portal and EDI ordering, contract pricing
configured, then spreadsheet billing, cash application and collections. Deterministic index
**36.4 (Emerging)**, 8 of 8 steps assessed, one LLM refinement of −0.3 on Pricing, within
the ±1 bound and with a specific reason drawn from the indexation nudge. The executive
summary used the analyst's real evidence throughout — 78-day DSO against 45-day terms, the
8 days of internal DSO before the customer is asked to pay, EUR 640k unapplied cash, EUR
900k in dispute, 6,800 invoices against 5 FTEs, the 3.1% credit note rate against a 1%
target. Pointers named the right steps, heaviest-weighted first.

**Drove it in a browser.** Five processes with **three** honest "Not yet defined" badges;
the O2C questionnaire rendering 8 steps, 113 options and 42 remarks/evidence boxes; a nudge
appearing live on selection; the score view showing the index, the band and its meaning, the
authored shape note with its measured means, and an 8-row step table. `plan_to_make` gives
the honest 409 empty state.

**Three traps for the next session, none a code fault:**
- A **welcome gate** ("Continue") stands in front of the app on a fresh browser profile.
  A script that navigates straight to a deep route sees an empty shell and looks exactly
  like a data-loading failure. Click through it first.
- Options render as `[role=radio]` **buttons**, not `input[type=radio]`, and badges are
  uppercased by CSS. Selectors written against the obvious markup silently find nothing.
- Driving the questionnaire in a browser **writes real answers**. The check clicked the
  first option on `O2C-01-01` and clobbered a stored answer (index fell 36.4 → 32.4 until
  it was restored). Use a scratch engagement, or restore what you touch.

### 2026-09-02 — Phase 5: Assess (business process automation)

Where the diligence is actually performed. The first module whose content originates with
the **analyst in the data room** rather than being derived from the intake. Plan at
`docs/phases/PHASE5_PLAN.md`.

**Procure to Pay only, by instruction.** The other four processes (O2C, P2M, H2R, R2R) are
registered with `defined: false` — **listed rather than hidden**, so the shape of the module
is visible, and asking for one returns **409 `process_not_defined`**, not 404. A 404 would
wrongly imply the process does not exist; it does, its questions do not.

**The evaluation reference came first**, because scoring reads from it:
`docs/reference/P2P_AUTOMATION_MODEL.md` defines nine L1 steps weighted by transaction
volume and financial exposure (summing to 100), and a 0-5 ladder whose levels are defined by
**observable evidence** rather than adjectives, so two analysts land on the same number.
Invoice matching (17) and PO issuance (13) weigh heaviest — most transactions, most leakage.
Marked `[EXT]`: built for this platform, not from Roehl-Anderson, and explicitly a
calibration to be tuned, exactly as DD_master §15.1 says of the mix weights.

**Two scoring rules stop the number inventing findings.** Both were deliberate:

1. **An unanswered question is excluded from the denominator, never scored as zero.** A
   blank is an absence of evidence, not evidence of manual working.
2. **A step with no answered scoring questions is `not_assessed`** and drops out of the
   index, its weight redistributed. Otherwise a half-finished questionnaire produces a
   confident number.

Coverage is reported alongside the index ("scored on 20 of 20 questions, covering 9 of 9
steps") so a reader can tell a confident 34 from a thin one.

**The shape is reported, not just the level.** A front-loaded 52 and a uniform 52 imply
remediation costs an order of magnitude apart, so `_shape_note` names the pattern —
front-loaded (a procurement tool bought and never rolled through to AP), back-loaded
(finance modernised what it controls), or even.

**Nudges are data, not code.** `when: {equals | in | answered}` in the YAML, evaluated
**client-side** so the follow-up appears the instant an option is picked. They never score —
one that scored would double-count its parent. The loader **validates that every nudge fires
on an option that actually exists**: a nudge naming a stale label would silently never
appear, and nobody would notice the evidence was not being gathered.

**Custom questions are stored per engagement, not merged into the YAML** — the YAML is shared
content, and one engagement's addition must not appear on every other. They carry no options,
so they enrich the evidence without moving the number.

**Two decisions Rishi made when asked** — bounded step refinement, and internal-facing
output. Both recorded as decision entries above.

**Found by reading the output, not by a failing test** (the fourth session running):

- The fallback executive summary appended `_shape_note` verbatim, and the page renders the
  shape note separately — so the same paragraph printed twice. Now the summary names the
  unassessed steps instead, which is information the shape note does not carry.
- Every unassessed step's probe pointer claimed *"its answers would move the index most"* —
  which cannot be true of four different steps. Only the heaviest says it now.
- On the rendered score page the prose ran to ~110ch and the table extended past the
  summary's right edge, giving the page two competing widths. Constrained to a document
  measure.

**Verified with the live model, not only mocked.** A seeded industrial distributor with 25
answers returned `generator: llm` and an index of 34.0/100 (Emerging). The summary used the
analyst's actual evidence — 4,200 invoices, 9 AP FTEs, the missing callback verification, the
unlogged payment file, the blocked-invoice list nobody could produce — and derived **466
invoices per FTE per month**, which is precisely the metric the questionnaire's nudge was
written to elicit. That is the module working as designed.

**Verified in a browser**: 5 processes with 4 honest "Not yet defined" badges, Assess in the
nav, 9 step sections, 108 options, 20 answers restored after a reload, a nudge revealing live
on selection (14 → 15 follow-ups), the custom question tagged "Added", the score table with 9
rows and 7 pointers, and the 409 empty state for an undefined process.

**No new colour tokens.** The five bands reuse the existing priority/status ramp — low
maturity reads as the problem colour, high as the green already reserved for "arrived".

### 2026-08-31 — Phase 4: the Checklist

Tracks what has actually arrived against each IRL request. Plan at
`docs/phases/PHASE4_PLAN.md`.

**Named "Checklist", not "IRL Checklist".** Rishi's original wording was *"name this
feature IRL"*, but the request list already carries that name — two things sharing it
would be confusing in code, docs and conversation. Asked, and he chose the short name.

**The ranking needed recalibrating against real data, and that mattered.** The first
version made every Tier 3 (deep dive) request critical. Run against the real 45-request
Meridian Analytics list it put **24 of 45 items (53%) in one bucket** — at which point
the colour coding stops telling a consultant anything. Critical is now reserved for
security, privacy and regulatory evidence (`W-SEC`/`W-PROC`/`W-DATA`), where a gap is a
deal issue rather than a depth question; depth alone maps to high. The spread became
**9 / 25 / 6 / 5**. `test_the_scale_actually_discriminates` fails if any single level
ever swallows the list again.

Found by generating the thing and looking at the distribution — not by a failing test.

**The tier is not stored on `IrlQuestion`** (only `source_row_id` is), so the ranker
joins back to the scope payload. That avoided changing the IRL schema and means the
lists generated before this feature existed rank correctly with no regeneration.

**Status lives in its own table** (`irl_document_status`), separate from
`irl_response`: a response is what the client wrote, a status is what the deal team
observes. Rows exist only once a status is set, so absence means `not_received` and no
backfill was needed.

**`set_by_human` exists for the scanner that does not exist yet.** When the shared-drive
walk is built it must never overwrite a status a person set deliberately. Recording that
intent now is cheaper than retrofitting it later.

### Deferred, deliberately — both in scope, neither built

**Shared-drive scanning.** `services/checklist/scanner.py` holds the contract and the
four rules it must follow; the endpoint returns **501 with an explanation** rather than
being a missing route, so the shape is visible in OpenAPI and the UI has something real
to call. The matching rules need real files in front of us to calibrate, and a scanner
that guesses wrong is worse than none: it would mark a request satisfied when the
document is missing, and nobody would notice until the team went looking.

**Email reminders.** Frontend stub only — live preview from real data, Send visibly
disabled, panel badged "Not connected yet". A button that looks functional and silently
does nothing is worse in a demo than one honestly marked pending.

**Test fixture**: `shared-drive/project-lighthouse/` — **gitignored** (Rishi's call), 24
files across 6 function folders, built from the real Lighthouse IRL. Deliberately
partial so every status is demonstrable: clear matches, three files marked `-ONLY` that
should read as *received partially* (one quarter where the request asks for twelve
months, a register without its contracts, one year of attrition where two were asked
for), and roughly half the list with nothing at all.

**New colour tokens.** The house palette was blue/red/neutral only. A four-step priority
ramp cannot be carried by blue alone, so `--priority-*` and `--status-*` were added to
`tokens.css` and mapped in `globals.css` — green appears only where "arrived" genuinely
means good. No raw hex in components (CLAUDE.md §8).

**Verified in a browser**, not just by tests: correct three columns, legend covering all
four levels, four distinct badge colours actually rendering, a status change persisting
across a reload, summary counts updating, the reminder preview matching the table, Send
disabled, and the scan surfacing its 501 message.


### 2026-08-31 — Phase 3: Initial Request List and company research

The step after the scope: the **IRL** the buyer sends the target, and the **company
research** that informs it. Plan at `docs/phases/PHASE3_PLAN.md`.

**The engagement was NOT renamed to "project".** Rishi asked that a project hold its
name, intake, SOW, IRL and more later. The engagement already *is* that container; 66
files reference the name, so renaming would be a large cosmetic diff with real
regression risk and zero behaviour change. What it lacked was room for modules, so each
deliverable is now its own versioned child table hanging off `engagements` — the pattern
`scope_of_work` already used. **Adding a module later is one more table + service +
router.** Nothing existing has to change.

**Seeds are the reason the IRL is defensible.** Every KPMG scope row already carries an
`evidence` list, which reaches the payload as `ScopedRow.evidence_requests`. Those become
the deterministic seeds, so every seeded question traces to a scope area a rule opened,
and the IRL generates fully with the LLM off. The model rewrites seeds into client-ready
wording and *adds* questions for the non-tech functions a tech scope never reaches —
marked `source: "llm"` with no `source_row_id`, so a reviewer can always tell which is
which.

**The LLM contract differs from the scope engine in one way**: the model may *add*
questions (an IRL that only asks what a tech scope covers is not a real IRL), but may not
drop or invent a seed. Every seed id must come back exactly once, or the whole response
is discarded for the deterministic list.

**Research feeds the IRL.** Rishi confirmed mid-build that the questions must take the
research and the intake context as input. `LlmIrlGenerator` passes the research summary,
findings, and the full engagement context into the prompt;
`test_research_and_context_reach_the_model` asserts all three actually appear in what is
sent, rather than trusting the wiring.

**Responses live in their own table** (`irl_response`), not in `payload_json`. They are
user data with a different lifecycle from the generated document: regenerating must never
clobber typed answers. Answers on stable ids are carried forward to the new version;
`test_responses_survive_a_regeneration` pins it. This also avoids the shallow-copy /
`flag_modified` trap recorded below.

**Research refuses rather than fabricating.** Gemini's `GoogleSearch` grounding tool
returns the pages it actually read; if a response comes back with no grounding metadata,
the run is **rejected, not stored**. Ungrounded research with invented citations looks
identical to the real thing and would reach a deal team carrying the same authority.
There is deliberately **no deterministic fallback** here — unlike a scope, research
without web access is not a degraded version of itself, it is fabrication. Dangling
citation ids the model invents are stripped, so the UI never renders a source that does
not exist.

Every research payload **stores its own disclaimer** rather than relying on the page that
renders it, so a re-read or exported run still carries the warning.

**Excel**: `xlsxwriter` was already installed (a python-pptx dependency) and is now pinned
explicitly. Three columns exactly — `Function | Question | Response` — with Response blank
for the client, header frozen, autofilter on. Answers already typed in the app are written
back so the workbook round-trips. `openpyxl` was added as a **test-only** dependency to
read the workbook back and verify the columns rather than trusting the writer.

**Function names are model-invented per target** (Rishi's call over a fixed list), which
is what makes them fit the business — a manufacturer gets "Plant Operations", a bank
"Treasury". The consequence is drift between regenerations; mitigated by storing the
resolved list and feeding it back into the prompt. It reduces drift, it does not eliminate
it. If that proves annoying, the fix is a practitioner-editable `irl_functions.yaml`.

**Verified by running it**, not only by tests: generated a real IRL (30 questions, 8
functions, each traceable to a scope row), opened the exported workbook (three columns, 29
blank rows, 1 answer round-tripped), and drove the page in a browser — typed a response,
saw "Saved", reloaded, it persisted.

**Also fixed while here:** the sidebar's active-engagement regex only matched `/intake/`,
so the per-engagement section vanished on every `/engagements/{id}` route. Widened to
match both, with `/intake/new` excluded. The `Engagements` workspace link was tightened
from `startsWith` to an exact match so it stops highlighting inside a sub-route.


### 2026-08-31 — Tier badges removed from the client-facing scope

Rishi: *"i dont want this assess deep dive indicators in the SOW part of the generated
SOW like just remove it"* — the `DEEP DIVE` / `ASSESS` chips beside each scope row.

Removed from **all three** surfaces, on Rishi's call: the PPT deck, the PDF, and the
on-screen scope view. The PDF also loses the italic tier-reason line ("core coverage;
mandatory at Tier 2") that sat under each title.

**The tier itself is untouched.** It still governs which rows open and how deep, it is
still stored on every row, and it still drives the sequencing split. Only the *label*
is gone from the client-facing document — depth is an internal decision, and the scope
states the work rather than the engine's grading of it. The Markdown export keeps
`tier_name` and `tier_reason`, since that is the internal artefact.

The on-screen card also keeps the collapsible **"Why this depth"** panel, which carries
`tier_reason` and the adjustments. Only the coloured chip beside the title went.

**Cleanup that came with it:** `_tier_chip` and `Theme.tier_colors` (pptx), `_tier_badge`,
`_TIER_COLOR` and the `"tier"` paragraph style (pdf), `TIER_STYLE` (frontend). The PDF's
`_row_block` lost its `content_w` parameter — the header table existed only to hold the
badge, so the title is now a plain paragraph spanning the full width.

**Two test traps worth remembering**, both of which I hit:

1. A blanket `"DEEP DIVE" not in deck_text` fails, because **"Deep dive" is also a
   sequencing phase name** — the one Rishi's partner asked for. The assertion has to be
   scoped to the scope-of-work slides only.
2. A blanket `"ASSESS" not in pdf_text` fails on the KPMG source wording itself:
   *"key-person **assess**ment"*, *"**Assess** IT infrastructure"*. The PDF test now
   matches whole words with a word-boundary regex against `TIER_NAMES`.

### Noticed but not changed

The PDF still prints row adjustments verbatim, e.g. `+1 tier: you asked to "Validate
scalability"`. That is tier language on a client-facing document, so it may want the
same treatment — but it was outside what was asked, and it carries real information
(why an area got more depth), so it was left alone. Raise it if it should go.


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
