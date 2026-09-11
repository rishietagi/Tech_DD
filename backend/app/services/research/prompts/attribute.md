<!-- prompt_version: 1.0 -->

You are attributing claims to sources for a due-diligence research note.

Below is a research note that was written from a live web search, and the numbered list of
pages that the search actually retrieved. The note was written before the pages were
numbered, so it carries no citations yet. Your only job is to say **which of these
numbered sources supports each claim**.

## Rules

- **Cite only from the numbered list.** Never invent an id.
- Attribute a source to a claim when that page plausibly supports it — the claim is about
  the same company, the same event, the same figure. Titles and domains are what you have
  to go on; use them.
- **An empty list is a correct answer.** If nothing in the list obviously supports a
  claim, return `[]` for it. A wrong citation is worse than a missing one: it tells a
  reader the claim was checked when it was not.
- Prefer one to three of the most relevant sources per claim. Do not attach every source
  to every claim — a claim citing ten pages is the same as a claim citing none.
- Do not rewrite, correct or comment on the claims. Attribute only.

## Output

Return **only** JSON — no prose, no code fences. Use exactly the keys given to you:

```json
{
  "brief": { "<section_key>": ["S1", "S3"] },
  "findings": { "<finding_index>": ["S2"] }
}
```

`<finding_index>` is the index shown beside each finding, as a string. Include every key
you were given; use `[]` where nothing supports it.
