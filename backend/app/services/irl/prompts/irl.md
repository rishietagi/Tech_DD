<!-- prompt_version: 3.0 -->

You are drafting the **Initial Request List** for a technology due diligence.

An IRL is the document the buyer sends the target at the start of diligence. The
target's staff read it and respond, so every item has to be answerable by someone who was
not in the room when the scope was written.

**It asks for two different things, and both matter:**

* **Document requests** — an artefact the target hands over: a diagram, a register, an
  inventory, a contract, an export.
* **Questions** — something only management can explain: how a process actually works,
  what is planned, where the constraints are. A document tells you what exists; a
  question tells you what it means and whether it is used.

A request list that only asks for documents is a filing exercise. The diligence findings
come from the gap between what the documents show and what management says.

## What you are given

- **Engagement context** — the deal, the thesis, and what the buyer is worried about.
- **Target profile** — what the company does, its sector, size and known technology.
- **Company research** — what public sources say about this target, if a research run
  exists. Use it. It is what lets you name functions that match this business and ask
  about things that have actually happened.
- **Seed requests** — each with an id, and each marked `kind`:
  - `kind: "document"` — an evidence line from the scope of work.
  - `kind: "question"` — an area of investigation from the reference methodology, carrying
    a page `citation`. These are written as *internal* research questions and usually need
    rephrasing before they are put to a client (see §1b).

  Seeds are the areas the diligence has already committed to covering.

## Your job

### 1a. Rewrite every document seed into a proper request

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

### 1b. Rewrite every question seed so it is not leading

Question seeds come from the reference methodology's internal *areas of investigation*.
They are written for the diligence team to think with, not for a client to answer, and
several are leading as written. **Rephrase them into focused, non-leading questions.**

The source's own worked example:

> **Wrong:** "Does your department deliver value to the business?"
> **Right:** "Have you had any challenges meeting business requirements, or know of
> challenges that may develop in the near future?"

A leading question collects agreement, not evidence. Nobody answers "no, my department
delivers no value". Rewrite so that an honest answer is the easy answer:

| Seed as given | Ask instead |
|---|---|
| Is IT managed to deliver value to the business? | How is IT's contribution to the business measured, and what has that measurement shown over the last year? |
| Is the IT organization sufficient to support expected growth? | Where do you expect the current IT team to be stretched by the growth plan, and what roles would you add first? |
| Is IT leadership capable and well suited to driving the strategy? | How is the IT leadership team structured, and which parts of the strategy is each person accountable for? |

Keep the **subject** of the seed — you are changing how it is asked, not what is asked.
Do not drop a question because it is awkward: rephrase it.

Also:
- **Ask one thing per question.** If a seed packs two, ask the primary one and let the
  second follow naturally.
- **Prefer questions that invite specifics** — numbers, names, dates, examples — over
  questions answerable with yes or no.
- **Never imply the answer.** "How do you handle X?" not "Do you have a proper X?"

### 2. Add the questions the technology scope does not reach

A technology scope does not cover HR, Finance, Legal or Commercial, but an IRL must.
Add requests of your own (leave `seed_id` **null**) for the functions a real diligence
would need — employment and contractor arrangements for engineering staff, IT spend and
budgets, software licences and IP assignment, customer contracts with technology
commitments, insurance, and anything the research suggests is material for this target.

Add **8 to 20** such requests. Fewer if the target is small and simple; more if the
research shows real complexity. Do not pad.

Set `kind` on each addition: `"document"` where you are asking for an artefact,
`"question"` where you are asking management to explain something.

### 2b. Cover the areas the methodology gives no questions for

The reference methodology supplies questions for most areas but **none** for these, and
they are named in your input as `unsourced_workstreams`:

- **Security** — how incidents are detected and handled, what testing is done and what it
  found, who is accountable.
- **Data and privacy** — what personal data is held, where it sits, on what legal basis,
  and what would move in a separation.
- **Separation / carve-out** — what is shared with the parent today and what breaks on day one.
- **Integration** — what would have to connect to the buyer, and what is in the way.
- **Product** — for a product deal: roadmap credibility, technical debt, release practice.

Where the scope opens one of these areas, **write questions for it yourself** and set
`kind: "question"`. These are yours rather than sourced, and the payload records that
distinction — write them to the same standard as §1b: focused, specific, not leading.

### 3. Assign every question a function and a scope area

Two separate fields, and they answer different questions.

**`scope_area`** — which heading of the scope of work this request belongs to. Every seed
you are given already carries its `scope_area`; **copy it through unchanged**. For your own
additions, use a scope area only if the request genuinely belongs to one; otherwise leave
it as an empty string and it will be filed under "Additional requests".

**`function`** — the business function or team that owns the answer, i.e. the group the
target would forward the request to. This is what makes the workbook routable.

Name the functions to fit this company, using the research and the target profile. A
software business has "Engineering", a manufacturer has "Plant Operations", a bank has
"Treasury". Use the words that business would actually use.

Constraints that make the list usable:
- Between **4 and 12** distinct functions across the whole list. More than that and the
  spreadsheet stops being groupable.
- Title Case, 1–3 words where possible, no ampersand-heavy chains.
- **Be consistent**: one function name per concept. Never both "IT" and "Information
  Technology", or both "Finance" and "Finance Team".
- If you are given the previous run's function names, **reuse them wherever they still
  fit**. The list should be stable between regenerations.

### 3a. House language — the same rules as the scope of work

The request list goes to the client alongside the scope of work and must read as the same
document family. These rules are identical to the scope prompt's:

- **Never name the target, the investor or any party.** Write "the Target", "the
  Acquirer", "the Parent". A company name in a request is wrong even in the intro.
- **Plain language.** Write for a reader who is not a technologist. **Expand every
  abbreviation on first use** with the short form in brackets — enterprise resource
  planning (ERP), disaster recovery (DR), software development lifecycle (SDLC), end of
  life (EOL). **Do not expand IT, HR or CRM**; they are universally understood and
  expanding them adds noise.
- **Short and specific.** One request per question, ideally under 30 words. Ask for one
  thing. Two artefacts in one line means the client supplies one and you chase the other.
- **Open with a request verb**: *Provide*, *Confirm*, *Describe*, *Detail*, *Share*. Not
  "Gain", not "We would like to understand".
- **No hedging, no marketing adjectives, no "comprehensive".**

### 4. Write a short intro

Two or three sentences addressed to the target: what the list is for, how to respond,
and what to do when something is unavailable. **Do not name the company** — write "the
Target", per the house language rules above.

## Output

Return **only** JSON — no prose before or after, no code fences:

```json
{
  "intro": "...",
  "questions": [
    {"seed_id": "PD-01-E1", "kind": "document", "scope_area": "IT Infrastructure", "function": "IT", "question": "..."},
    {"seed_id": "PD-01-Q1", "kind": "question", "scope_area": "IT Infrastructure", "function": "IT", "question": "..."},
    {"seed_id": null, "kind": "question", "scope_area": "", "function": "Human Resources", "question": "..."}
  ]
}
```

Every seed id must appear exactly once. A seed's `kind` is fixed — return it unchanged;
you may rewrite the wording of a question but not turn a question into a document request
or the reverse. Any deviation causes your entire response to be discarded and the
untailored list to be sent instead.
