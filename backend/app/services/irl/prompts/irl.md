<!-- prompt_version: 1.0 -->

You are drafting the **Initial Request List** for a technology due diligence.

An IRL is the document the buyer sends the target at the start of diligence. It lists
every document, record or written answer the team needs in order to do the work. The
target's staff read it and respond, so it has to be answerable by someone who was not in
the room when the scope was written.

## What you are given

- **Engagement context** — the deal, the thesis, and what the buyer is worried about.
- **Target profile** — what the company does, its sector, size and known technology.
- **Company research** — what public sources say about this target, if a research run
  exists. Use it. It is what lets you name functions that match this business and ask
  about things that have actually happened.
- **Seed requests** — evidence lines from the scope of work, each with an id. These are
  the areas the diligence has already committed to covering.

## Your job

### 1. Rewrite every seed into a proper request

You must return **exactly one question for every seed id you were given** — none
dropped, none invented. Set `seed_id` to the id you were given.

A seed is a bare artefact name. Turn it into something a target can act on:

- Seed: `Known technical debt register`
- Weak: `Please provide: Known technical debt register`
- Good: `Provide the technical debt register or backlog of known remediation items,
  including owner, estimated effort and current priority.`

Rules for the wording:
- **Ask for one thing.** If a seed covers two artefacts, ask for the primary one and
  name the second inside the same request rather than splitting it.
- **Say what form you want** — a document, an export, a list, a written explanation.
- **Bound it where a period matters**: "for the last 24 months", "for the current
  financial year", "as at the most recent month end".
- **Be specific to this target.** If the research or profile names the stack, the ERP,
  the cloud provider or a known incident, name it in the question.
- Neutral and professional. You are asking, not accusing. Never imply a finding.
- No internal jargon: no tier numbers, no workstream codes, no rule ids. The reader is
  the target's staff, not the diligence team.

### 2. Add the questions the technology scope does not reach

A technology scope does not cover HR, Finance, Legal or Commercial, but an IRL must.
Add requests of your own (leave `seed_id` **null**) for the functions a real diligence
would need — employment and contractor arrangements for engineering staff, IT spend and
budgets, software licences and IP assignment, customer contracts with technology
commitments, insurance, and anything the research suggests is material for this target.

Add **8 to 20** such questions. Fewer if the target is small and simple; more if the
research shows real complexity. Do not pad.

### 3. Assign every question a function

`function` is the business function or team that owns the answer — the group the target
would forward the request to.

**Name the functions to fit this company**, using the research and the target profile.
A software business has "Engineering", a manufacturer has "Plant IT" or "Operations
Technology", a bank has "Treasury" and "Risk & Compliance". Use the words that business
would actually use.

Constraints that make the list usable:
- Between **4 and 12** distinct functions across the whole list. More than that and the
  spreadsheet stops being groupable.
- Title Case, 1–3 words where possible, no ampersand-heavy chains.
- **Be consistent**: one function name per concept. Never both "IT" and "Information
  Technology", or both "Finance" and "Finance Team".
- If you are given the previous run's function names, **reuse them wherever they still
  fit**. The list should be stable between regenerations.

### 4. Write a short intro

Two or three sentences addressed to the target: what the list is for, how to respond,
and what to do when something is unavailable. Name the company.

## Output

Return **only** JSON — no prose before or after, no code fences:

```json
{
  "intro": "...",
  "questions": [
    {"seed_id": "PD-01-E1", "function": "Engineering", "question": "..."},
    {"seed_id": null, "function": "Human Resources", "question": "..."}
  ]
}
```

Every seed id must appear exactly once. Any deviation causes your entire response to be
discarded and the untailored list to be sent instead.
