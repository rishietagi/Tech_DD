"""The deterministic report — every section built from earlier modules, nothing invented.

Pure: `build(inputs, config)` returns a payload with no database access and no model call.
This is the floor the report-narrative and report-executive-summary skills improve on when
the AI is on, and it is a complete, exportable report on its own.
"""

import re
from datetime import UTC, datetime

from app.schemas.report import (
    Context,
    Cover,
    GlossaryEntry,
    ReportConfig,
    ReportPayload,
    ScopeArea,
)
from app.services.report.findings import (
    Area,
    build_areas,
    collect,
    executive_rows,
    inventory_limitations,
    irl_limitations,
    limitation_rows,
    route_findings,
)
from app.services.report.inputs import ReportInputs
from app.services.report.sections import appendix_sections, supporting_sections


# Which inputs count as evidence for an area's workstream, so an area with no findings
# reads "no material gaps" rather than "not assessed" when something was reviewed.
def _evidence(inputs: ReportInputs) -> dict[str, int]:
    dt = inputs.data_tech_score or {}
    checks = [c for c in dt.get("checks", []) if c.get("status") not in ("unanswered", "unknown")]
    return {
        "W-APP": len(inputs.items("application")),
        "W-PROD": len(inputs.items("application")),
        "W-INFRA": len(inputs.items("platform")) + sum(1 for c in checks if c["section"] == "resilience"),
        "W-SEC": sum(1 for c in checks if c["section"] == "cyber"),
        "W-PROC": sum(1 for c in checks if c["section"] == "engineering"),
        "W-DATA": len(inputs.items("data_domain")),
        "W-OPS": len(inputs.items("it_role")),
        "W-VEN": len(inputs.items("it_contract")),
        "W-SPEND": 1 if inputs.budget_saved else 0,
    }


def _month_label(inputs: ReportInputs) -> str:
    return inputs.today.strftime("%B %Y")


def _date_label(value: object) -> str:
    return value.strftime("%d %B %Y").lstrip("0") if hasattr(value, "strftime") else str(value)


def _context(inputs: ReportInputs, config: ReportConfig, areas: list[Area], with_findings: list[str]) -> Context:
    c = config.context
    dd_label = config.dd_labels.get(inputs.dd_type, config.dd_labels["enterprise"])
    if any("W-SEC" in a.workstreams for a in areas) or any(a.title == "Cyber Security" for a in areas):
        dd_label = dd_label.replace("Due Diligence", "and Cyber Due Diligence")
    target = inputs.target_name or "the target"
    template = c["objective"] if inputs.investor_name else c["objective_no_investor"]
    objective = template.format(investor=inputs.investor_name, dd_label=dd_label, target=target).strip()
    sessions = (c.get("sessions") or {}).get(inputs.access_level, "")
    approach = c["approach"].format(sessions=sessions).strip()
    titles = [a.title for a in areas]
    gap_titles = with_findings or titles
    areas_text = (
        ", ".join(gap_titles[:-1]) + f" and {gap_titles[-1]}"
        if len(gap_titles) > 1
        else (gap_titles[0] if gap_titles else "technology estate")
    )
    # With no findings the report cannot claim to "highlight gaps" — it says what it covers.
    outcome = (c["outcome"] if with_findings else c["outcome_no_findings"]).format(areas=areas_text).strip()
    cutoff = c["cutoff"].format(date=_date_label(inputs.cutoff or inputs.today)).strip()
    return Context(objective=objective, approach=approach, outcome=outcome, key_areas=titles, cutoff=cutoff)


def _glossary(text: str, config: ReportConfig) -> list[GlossaryEntry]:
    found = [
        GlossaryEntry(term=term, expansion=expansion)
        for term, expansion in config.glossary.items()
        if re.search(rf"(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", text)
    ]
    return sorted(found, key=lambda g: g.term.lower())


def build(inputs: ReportInputs, config: ReportConfig) -> ReportPayload:
    areas = build_areas(inputs)
    route_findings(collect(inputs), areas, config)
    irl_limitations(inputs, areas, config)
    inventory_limitations(inputs, areas, config)
    evidence = _evidence(inputs)
    for area in areas:
        area.evidence += sum(evidence.get(ws, 0) for ws in area.workstreams)

    executive = executive_rows(areas, config)
    scope_by_id = {r["id"]: r for r in inputs.scope_rows}
    in_scope = [
        ScopeArea(
            area_id=a.area_id,
            title=a.title,
            considerations=[line["text"] for line in scope_by_id[a.area_id].get("lines", [])],
        )
        for a in areas
        if a.from_scope
    ]
    supporting = supporting_sections(inputs, config)
    appendix = appendix_sections(inputs, config)
    context = _context(
        inputs,
        config,
        [a for a in areas if a.from_scope or a.findings],
        [r.title for r in executive if r.include],
    )
    limitations = limitation_rows(areas)

    corpus = " ".join(
        [context.objective, context.approach, context.outcome]
        + [line for s in in_scope for line in s.considerations]
        + [item for limitation in limitations for item in limitation.items]
        + [text for row in executive for text in [*row.findings, row.implication, *row.actions]]
        + [s.panel for s in supporting]
        + [
            " ".join([b.title, b.text, *b.items, *b.columns, *[c for r in b.rows for c in r]])
            for s in [*supporting, *appendix]
            for b in s.blocks
        ]
    )

    return ReportPayload(
        generator="rules",
        skill_versions={},
        generated_at=datetime.now(UTC),
        dd_type=inputs.dd_type,
        dd_mix=inputs.dd_mix,
        target_name=inputs.target_name,
        investor_name=inputs.investor_name,
        cover=Cover(
            codename=inputs.deal_name,
            title=config.cover["title"],
            subtitle=config.cover["subtitle"],
            date_label=_month_label(inputs),
        ),
        context=context,
        glossary=_glossary(corpus, config),
        in_scope=in_scope,
        limitations=limitations,
        executive_title=config.executive_titles.get(inputs.dd_type, config.executive_titles["enterprise"]),
        executive=executive,
        supporting=supporting,
        appendix=appendix,
        source_line=config.source_line,
    )
