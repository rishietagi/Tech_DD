# Claude Code prompt — Phase 2 (scope-of-work engine)

Run from `C:\Users\rishi\Desktop\Tech_DD` in plan mode. Paste everything below the line.

---

Phase 1 of this project is built and committed. You are now building **Phase 2: the
scope-of-work generation engine.**

Read these four files in full before writing anything:

1. `docs/reference/DD_master.md` — the domain authority. A technology due diligence reference built
   from Roehl-Anderson, *M&A Information Technology Best Practices* (Wiley, 2013).
   Its §6 (workstream library), §13 (intake fields), §14 (output structure) and §15
   (encodable decision rules) are the content you are encoding.
2. `docs/phases/PHASE2_SPEC.md` — the build spec for this phase: architecture, schemas,
   selection and depth algorithms, LLM boundaries, API and UI changes, tests.
3. `CLAUDE.md` — project constitution. Still governs stack, conventions and git.
4. `docs/phases/PHASE1_PLAN.md` — what Phase 1 built, so you know what already exists.

Precedence on conflict: `CLAUDE.md` > `docs/reference/DD_master.md` > `docs/phases/PHASE2_SPEC.md` >
`docs/phases/PHASE1_PLAN.md`. If you find a real conflict, tell me rather than picking silently.

**Before writing code**, give me a plan: the files you will create or change, the
library and rules file formats, the migration, the new API surface, and your commit
sequence. Wait for approval.

Then build it, following `docs/phases/PHASE2_SPEC.md` §12 in order, committing after each
numbered step.

The things that will make or break this phase:

1. **Deterministic core, generative surface.** `RulesScopeGenerator` must produce a
   complete, publishable scope with the LLM entirely disabled. `LlmScopeGenerator`
   only rewrites prose — engagement summary, workstream objectives, question phrasing
   — inside the fixed skeleton. It may never add, remove or re-tier a workstream,
   change the mix, or invent an evidence request. Validate its output against the
   skeleton and fall back to the rules output on any mismatch. No API key must mean
   graceful fallback, not an exception.

2. **Content lives in data, not code.** The workstream library goes in versioned YAML
   under `backend/app/reference/workstreams/`, the rules in
   `backend/app/reference/scope_rules.yaml`. A practitioner must be able to edit a
   question or a weight without touching Python. Validate both at startup and fail
   fast on a malformed file.

3. **Transcribe `docs/reference/DD_master.md` §6 faithfully.** The sourced question sets in there are
   quoted from the book. Do not paraphrase them, do not drop any, and carry the page
   citations into the YAML. Mark every module, question and evidence request with
   `source_provenance: sourced` or `extended` — `docs/reference/DD_master.md` §16 explains why that
   distinction has to survive into the output.

4. **Implement the whole rule set** in `docs/reference/DD_master.md` §15 — A1–A11, M1–M7, D1–D10,
   C1–C9 — with the rule ids preserved, so a signal in the UI maps back to a line in
   the reference document.

5. **Everything is auditable.** Every workstream carries the signals that triggered it
   and the reason for its depth tier. Every scope carries a provenance list of the
   rules that fired and a non-empty exclusions section. A scope a reviewer cannot
   interrogate is a scope they cannot defend.

6. **Respect the access gates.** `code_access = none` caps the product deep-dive.
   `access_level = public_only` caps everything at a screen. `management_access =
   none` strips interview-dependent evidence. Never emit a scope promising depth the
   engagement cannot reach — say so in the output instead.

7. **Add the intake fields first** (`docs/phases/PHASE2_SPEC.md` §9.3): `deal_type`,
   `perspective`, `integration_model`, `relative_size`, `it_landscape_complexity`,
   `shared_with_parent`, `management_access`. Nullable columns, migration included,
   zod schemas and form controls updated, existing filed engagements still loading. A
   missing value is an "unknown" signal that lowers confidence, never an error.

8. **Golden-case tests are the deliverable, not an afterthought.** Build the six cases
   in `docs/phases/PHASE2_SPEC.md` §10 as intake fixtures with snapshotted deterministic
   output. They are what makes the scoring weights safe to tune later. Never snapshot
   LLM output; never call the live API in a test.

9. **Cost language.** Anything the scope says about cost is an order-of-magnitude
   range with a stated assumptions register. Never a point estimate. This is a direct
   instruction from the source and it matters for defensibility.

10. **Git.** Commit locally in clean conventional-commit steps as you go. Never add a
    remote, never push, never open a PR, never rewrite history. I do all pushing.

When you finish, verify against the acceptance criteria in `docs/phases/PHASE2_SPEC.md`
§11 and report each as pass or fail honestly. Then run one real generation against a
realistic intake and show me the output so I can judge whether it reads like something
a partner would send a client. Then stop.
