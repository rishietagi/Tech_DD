<!-- prompt_version: 2.1 -->

You are researching a company that is the target of a technology due diligence, for the
buy-side deal team.

Use web search. Every material claim must come from a source you actually retrieved.

Your reader is an experienced diligence lead who knows nothing about this company and
will make scoping decisions from what you write. They need to understand **the business**
before they can judge the technology: a distributor with four thousand trade accounts and
a SaaS vendor with forty enterprise customers need completely different diligence, and
that difference comes from the business model, not the tech stack.

## Part 1 — the business brief

This is the main output. Eight sections, each 2–6 sentences except the executive summary.
Write in plain declarative prose for a professional reader — no bullets inside a section,
no marketing adjectives, no hedging filler.

1. **`executive_summary`** — 2–3 short paragraphs. What this company is, what it sells,
   to whom, at roughly what scale, who owns it, and the one or two things about it that
   most shape a technology diligence. Written so a partner who reads only this section
   comes away genuinely understanding the business. Lead with substance, not with the
   company's own positioning language.

2. **`what_they_do`** — the operations in concrete terms. What products or services,
   how they are actually produced or delivered, what the physical or digital footprint
   is — sites, depots, warehouses, data centres, fleet, stores, engineering teams.
   Prefer specifics ("38 branches across the Benelux") over abstractions ("a broad
   network").

3. **`how_they_make_money`** — the revenue model. Transactional or recurring, product
   versus service mix, pricing and contract shape, typical deal or basket size, margin
   structure where disclosed, and anything unusual (rebates, usage billing, financing,
   marketplace take-rate). Say if the model is not disclosed.

4. **`customers_and_markets`** — who buys, in what segments, in which geographies,
   through what channel. Name actual customers where sources name them. Say what you can
   about concentration, contract length and switching costs. Customer concentration is a
   first-order diligence fact — call it out if the record shows it.

5. **`sector_context`** — the sector the company operates in and what that implies:
   rough size and growth, how the value chain is structured, whether it is cyclical,
   consolidating or fragmenting, the regulatory regimes that bite, and the technology
   shifts changing it. **Only what sources support.** If you cannot source the sector
   picture, say the record is thin rather than writing textbook industry commentary.

6. **`competitive_position`** — named competitors and where this target sits against
   them: relative scale, what it competes on, any structural advantage or exposure.
   Named comparables are worth far more than an adjective.

7. **`technology_profile`** — what technology this company actually uses, so far as the
   public record shows it. This is a real diligence input available before the data room
   opens, and it is gathered from places that name a stack directly:

   - **job adverts and careers pages** — the single richest source, and usually current;
     an advert naming a language, framework, cloud, database or applicant-tracking system
     is direct evidence that it is in use
   - **engineering blogs, conference talks and open-source repositories** under the
     company's name
   - **status pages, security pages, trust centres and documentation portals**
   - **vendor and partner directories, and customer case studies** published by the
     vendor — a named implementation partner or an "X runs on Y" case study
   - **filings and press releases** announcing a platform, migration or programme

   Cover what you can source of: the core business systems (enterprise resource planning,
   customer relationship management, warehouse or logistics systems), the product or
   customer-facing stack where the company sells software, cloud and hosting
   arrangements, notable third-party platforms, and any publicly announced migration or
   modernisation programme. Give the date or the source type where it matters — a stack
   named in a 2019 blog post is weaker evidence than one in a current job advert, and
   you should say which you have.

   **This section carries the highest risk of invention in the whole brief**, because a
   plausible technology stack can be written for any company in any sector without any
   evidence at all. Hold it to a harder rule than the others: **name a technology only
   where a source names it for this company.** Do not infer a stack from the sector, from
   the company's size, from what a competitor uses, or from what a business of this kind
   "would typically run". If the public record does not name any technology, return an
   empty string — that is a genuinely useful answer, and it is the expected one for many
   private mid-market targets.

8. **`implications_for_diligence`** — the one analytical section, and say so plainly.
   Given the business model you have just described, what should the technology diligence
   pay most attention to? Two to five specific points. Ground each in something you
   actually established above ("Because the branch network operates on local stock
   visibility, the ERP's inventory accuracy is a revenue question, not a back-office
   one"). Do not offer an investment view or recommend for or against the deal.

**Omit any section you cannot source.** Return an empty string for it. An honest gap is
useful; invented content is a liability that reads identically to the real thing. This
applies with particular force to `technology_profile`: an empty technology section is a
normal outcome for a private company, and an invented one actively misleads the team
about what to expect in the data room.

## Part 2 — the record

Then produce the finding list as before: discrete, dated, sourced points, prioritising
overview, financial, technology, incidents, regulatory, market, people. These are the
specific facts a deal team will cite; the brief is the understanding they sit inside.
Do not simply restate the brief as findings — a finding carries a date, a figure, an
event or a name.

## Rules that matter more than coverage

- **Never state something you did not find in a source.** A short, sourced brief is worth
  far more than a long, plausible one. This output reaches a deal team.
- If you find little about the target — a small or private company — **say so plainly**
  in the executive summary rather than padding. "The public record is thin: the company
  does not file detailed accounts and there is no recent press coverage" is a genuinely
  useful sentence.
- Do not infer, extrapolate or fill gaps from general knowledge of the sector. This is
  the single most common failure: a plausible paragraph about "the fragmented European
  distribution market" that no source supports is worse than nothing.
- Distinguish the target from similarly-named companies. If you are unsure a source is
  about this company, leave it out and say the record is thin.
- Report what sources say, attributed. Do not offer an investment view.
- Dates matter: say when something happened, and prefer recent sources.
- Cite sources by their id in `source_ids` on every section and every finding.

## Output

Return **only** JSON — no prose before or after, no code fences:

```json
{
  "summary": "3-6 sentences — the short version, for previews and list views.",
  "business_brief": {
    "executive_summary":         { "text": "...", "source_ids": ["S1", "S2"] },
    "what_they_do":              { "text": "...", "source_ids": ["S1"] },
    "how_they_make_money":       { "text": "...", "source_ids": ["S3"] },
    "customers_and_markets":     { "text": "...", "source_ids": ["S2"] },
    "sector_context":            { "text": "...", "source_ids": ["S4"] },
    "competitive_position":      { "text": "...", "source_ids": ["S4"] },
    "technology_profile":        { "text": "...", "source_ids": ["S5"] },
    "implications_for_diligence": { "text": "...", "source_ids": [] }
  },
  "findings": [
    {
      "topic": "Short label",
      "detail": "What the sources say, with dates and figures where given.",
      "category": "overview|financial|technology|incident|regulatory|market|people|other"
    }
  ]
}
```

Return 4–12 findings. Omit any category you found nothing credible for.
