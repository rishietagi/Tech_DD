# The IT due diligence report — structure and conventions

**Source:** a KPMG IT due diligence draft report Rishi shared on 2026-11-18 as the shape of
the final deliverable. **It is client material.** This file records its *structure and
conventions only* — no client, target or employee names, no figures, no client text. Do not
add any.

The report is a 16:9 PowerPoint deck. Its job is to tell the investor what was found, how
bad it is, what to do about it, and what could not be verified.

---

## 1. Section order

| # | Section | What it holds |
|---|---|---|
| — | **Cover** | Deal codename, "IT Due Diligence", "Draft Report", month and year. Full-bleed image. |
| — | **Table of contents** | Numbered sections with page numbers. |
| 1 | **Context setting** | Three numbered blocks — **Objective** (who asked KPMG to do what on which target), **Approach** (what was relied on: management information, number of sessions; limitations flagged in their sections), **Outcome** (the areas in which the report highlights gaps). Then a **Key assessment areas** grid of the focus areas. Footnote: the information cut-off date. |
| 2 | **Glossary of terms** | Two columns of abbreviation → expansion, alphabetical, only terms used. |
| 3 | **In-scope areas** | Table, paginated "(1/2)": **Focus area** → **Key considerations** (bullets, verb-led). |
| 4 | **Data limitations** | Table, paginated: **Focus area** → **Data limitations** — what the target did not provide, or provided only in part ("screenshots of the report were shared; the complete report was not"). |
| 5 | **Executive summary** | Table, paginated, titled by the DD type: **S.no · Diligence area · Key findings · Risk level · Recommended actions · Investment impact**. Findings are bullets followed by an *Implication:* bullet. Risk level is a RAG dot against a Low/Medium/High legend. Investment impact is a range with a footnote that it is indicative. |
| — | Section divider | "Supporting Analysis" on a full-bleed image. |
| 6 | **Supporting analysis** | One topic per slide: a **blue summary side panel** (3–6 sentence synopsis) on the left, detail on the right — overview prose, inventory tables (key applications, contracts, roadmap, assets by year, support SLAs), and the **current IT landscape overview diagram**. Each slide carries "As per information provided by target". |
| — | Section divider | "Appendix". |
| 7 | **Appendix** | Full detail tables (every application with its attributes; the IT team; contracts) and the target's own **network diagrams**. |

## 2. Conventions on every content slide

- **Breadcrumb strip** across the top naming every section, the current one bold.
- **DRAFT** stamp top right.
- Slide title large, in the brand blue; "(1/2)" when a table runs over.
- Footer: logo, legal line, classification, page number.
- Source line "As per information provided by target" on supporting and appendix slides.

## 3. The executive summary row

```
S.no | Diligence area | Key findings                       | Risk | Recommended actions   | Investment
  2  | IT Core Apps   | • finding                          |  ●   | • action              | XXX
     |                | • finding                          |      | • action              |
     |                | • Implication: what it means       |      |                       |
```

- One row per diligence area that has something to say.
- Findings are specific (systems, numbers, what is integrated with what), then one
  *Implication* bullet saying why it matters to the investor.
- Risk is one of three levels. The platform takes the highest severity among the area's
  findings, and the analyst can override it.
- Investment impact is left **XXX** for the engagement team (Rishi, 2026-11-18), editable.

## 4. The current IT landscape overview diagram

Two panels:
- **IT applications** — functions managed in the ERP as a row of boxes; then grouped
  bands (product and design applications, enterprise and support systems) of
  *function → product* pairs; custom-developed tools listed.
- **IT infrastructure** — backup and restoration targets; workload distribution (which
  host or platform runs which systems); IT assets (servers, switches, firewall, ISPs).

The platform draws this from the inventories. It never draws what the inventories do not
contain.

## 5. Where the platform's report departs from the sample, and why

- **IT financials.** The sample reviews "IT budget as a percent of annual revenue". The
  platform does not: the 2026-09-14 boundary limits IT financials to the budgeting process,
  so the report shows budget against actual and the budgeting-process findings only.
- **Network diagrams** are not generated. The platform holds no topology data, so the
  target's own diagrams are uploaded and placed in the appendix as provided.
- **Enterprise and product reports differ in their supporting analysis** — see
  `reference/report/report.yaml`. The sample is an enterprise report.
