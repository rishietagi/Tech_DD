"""Markdown export of a generated scope.

Renders the same document the UI shows, in a form a practitioner can paste into a deck
or a document. Deterministic and dependency-free: the payload already holds everything,
so nothing is recomputed here.
"""

from typing import Any

from app.schemas.scope import ScopeOfWorkPayloadV2

_DECK_LABEL = {
    "product": "Product Tech DD",
    "enterprise": "Enterprise IT DD",
    "blended": "Blended",
}


def _classification_block(scope: ScopeOfWorkPayloadV2) -> list[str]:
    c = scope.classification
    lines = [
        "## Classification",
        "",
        f"**{_DECK_LABEL.get(c.dd_type.value, c.dd_type.value)}** — mix {c.dd_mix}/100 "
        f"({c.confidence} confidence)",
        "",
    ]

    if c.override_applied:
        lines.append(f"Archetype declared in the intake: **{c.override_source}**.")
        if c.dd_type is not c.computed_dd_type:
            lines.append(
                f"The engine derived **{_DECK_LABEL.get(c.computed_dd_type.value)}** "
                f"(mix {c.computed_dd_mix}) from the answers given. The declaration is used "
                "for this scope; the disagreement is recorded because it is informative."
            )
        lines.append("")

    fired = [s for s in c.signals if s.effect.value != "unknown"]
    if fired:
        lines.extend(["### Signals", ""])
        for signal in fired:
            delta = signal.detail.get("mix_delta")
            parts = [f"- **{signal.code}** {signal.label}"]
            if isinstance(delta, int):
                direction = "product" if delta > 0 else "enterprise"
                parts.append(f" ({delta:+d} toward {direction})")
            if signal.source_field and signal.source_value:
                parts.append(f" — {signal.source_field.split('.')[-1]} = {signal.source_value}")
            if signal.citation:
                parts.append(f" *[{signal.citation}]*")
            lines.append("".join(parts))
        lines.append("")

    if c.confidence_reasons:
        lines.extend(["### Confidence", ""])
        lines.extend(f"- {reason}" for reason in c.confidence_reasons)
        lines.append("")

    return lines


def _rows_block(scope: ScopeOfWorkPayloadV2) -> list[str]:
    lines = ["## Scope of work", ""]

    product = [r for r in scope.rows if r.deck == "product"]
    enterprise = [r for r in scope.rows if r.deck == "enterprise"]
    is_blended = bool(product) and bool(enterprise)

    for deck_rows, heading in ((product, "Product due diligence"), (enterprise, "Enterprise IT due diligence")):
        if not deck_rows:
            continue
        if is_blended:
            lines.extend([f"### {heading}", ""])

        for row in deck_rows:
            lines.append(f"#### {row.sn:02d}. {row.title}")
            lines.append("")
            lines.append(f"*{row.tier_name}* — {row.tier_reason}")
            lines.append("")
            lines.extend(f"{line.text}" for line in row.lines)
            lines.append("")

            if row.adjustments:
                lines.extend(f"- {adjustment}" for adjustment in row.adjustments)
                lines.append("")

            if row.edited_by_human:
                note = "Edited by hand"
                if row.original_tier is not None and row.original_tier != row.tier:
                    note += f" — the engine had this at Tier {row.original_tier}"
                if row.override_reason:
                    note += f". {row.override_reason}"
                lines.extend([f"> {note}", ""])

            if row.evidence_requests:
                lines.append("**Evidence requested**")
                lines.append("")
                lines.extend(f"- {item}" for item in row.evidence_requests)
                lines.append("")

            trail = []
            if row.triggered_by:
                trail.append(f"Triggered by {', '.join(row.triggered_by)}")
            if row.dd_master_ref:
                trail.append(row.dd_master_ref)
            if trail:
                lines.extend([f"*{' · '.join(trail)}*", ""])

            if row.out_of_scope_note:
                lines.extend([f"> {row.out_of_scope_note}", ""])

    return lines


def _bullet_section(title: str, items: list[str], intro: str | None = None) -> list[str]:
    if not items:
        return []
    lines = [f"## {title}", ""]
    if intro:
        lines.extend([intro, ""])
    lines.extend(f"- {item}" for item in items)
    lines.append("")
    return lines


def render_markdown(scope: ScopeOfWorkPayloadV2, deal_name: str | None = None, version: int | None = None) -> str:
    """The full scope as Markdown."""
    lines: list[str] = []

    title = scope.deck_title
    if deal_name:
        title = f"{deal_name} — {title}"
    lines.extend([f"# {title}", ""])
    lines.extend([f"*{scope.deck_subtitle}*", ""])

    lines.extend(_classification_block(scope))

    lines.extend(["## Engagement", "", scope.engagement_summary, ""])
    lines.extend(_bullet_section("Objectives", scope.objectives))
    lines.extend(_rows_block(scope))

    if scope.sequencing:
        lines.extend(["## Sequencing", ""])
        for phase in scope.sequencing:
            lines.append(f"**{phase.name}** — {phase.weeks}")
            lines.append("")
            lines.append(phase.focus)
            if phase.row_ids:
                lines.append("")
                lines.append(f"*{len(phase.row_ids)} area(s)*")
            lines.append("")

    lines.extend(["## Cost estimation", "", scope.cost_plan.approach, ""])
    if scope.cost_plan.lines:
        lines.extend(["| Type | Line | Basis |", "| --- | --- | --- |"])
        for line in scope.cost_plan.lines:
            category = "One-time" if line.category == "one_time" else "Recurring"
            lines.append(f"| {category} | {line.label} | {line.basis} |")
        lines.append("")
    lines.extend(_bullet_section("Assumptions register", scope.cost_plan.assumptions_register))

    team = scope.team_shape
    if team.core_team or team.specialists:
        lines.extend(["## Team", ""])
        lines.extend(f"- {member}" for member in team.core_team)
        if team.specialists:
            lines.extend(["", "**Specialists required**", ""])
            lines.extend(f"- {specialist}" for specialist in team.specialists)
        if team.note:
            lines.extend(["", team.note])
        lines.append("")

    notes_with_text = [note for note in scope.notes if note.get("text")]
    if notes_with_text:
        lines.extend(["## Notes", ""])
        for note in notes_with_text:
            lines.append(f"**{note['label']}** — {note['text']}")
            if note.get("citation"):
                lines.append(f"*{note['citation']}*")
            lines.append("")

    lines.extend(_bullet_section("Risks to the diligence itself", scope.diligence_risks))

    if scope.exclusions:
        lines.extend(
            [
                "## Exclusions",
                "",
                "A scope that does not say what it excludes is not a scope.",
                "",
            ]
        )
        for exclusion in scope.exclusions:
            entry = f"- **{exclusion.subject}** — {exclusion.reason}"
            if exclusion.rule_code:
                entry += f" ({exclusion.rule_code})"
            lines.append(entry)
        lines.append("")

    if scope.provenance:
        lines.extend(["## Provenance", "", "Every rule that shaped this scope.", ""])
        for rule in scope.provenance:
            entry = f"- **{rule.code}** {rule.label}"
            if rule.provenance == "extended":
                entry += " *(extended practice)*"
            if rule.citation:
                entry += f" *[{rule.citation}]*"
            lines.append(entry)
        lines.append("")

    footer = f"Library v{scope.library_version} · rules v{scope.rules_version}"
    if scope.prompt_version:
        footer += f" · prompt v{scope.prompt_version}"
    footer += f" · generated by {scope.generator}"
    if version is not None:
        footer = f"Version {version} · {footer}"
    lines.extend(["---", "", f"*{footer}*", ""])

    return "\n".join(lines)


def render_markdown_from_payload(
    payload: dict[str, Any], deal_name: str | None = None, version: int | None = None
) -> str:
    """Render a stored payload. Only schema v2 is exportable."""
    if payload.get("schema_version") != 2:
        raise ValueError("Only schema v2 scopes can be exported to Markdown")
    return render_markdown(ScopeOfWorkPayloadV2.model_validate(payload), deal_name, version)
