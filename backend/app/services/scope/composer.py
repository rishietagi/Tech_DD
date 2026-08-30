"""KpmgScopeComposer — assembles the deterministic scope-of-work document.

This produces a complete, publishable scope with the LLM entirely disabled: an
acceptance criterion in PHASE2_SCOPE_ENGINE §11. The LLM layer (step 8) rewrites the
prose inside this document; it never decides what the document contains.
"""

from app.schemas.classification import Classification, DdType
from app.schemas.intake import IntakeFull
from app.schemas.scope import (
    CostLine,
    CostPlan,
    ScopedRow,
    ScopeLine,
    ScopeOfWorkPayloadV2,
    SequencePhase,
    TeamShape,
)
from app.schemas.selection import TIER_NAMES, Exclusion, SelectedRow
from app.schemas.signals import FiredRule, Signal
from app.services.scope.library import get_scope_library
from app.services.scope.rules import get_scope_rules

# Which specialists a workstream implies, when it opens deep enough to need one.
_SPECIALIST_FOR = {
    "W-SEC": "Cyber security specialist",
    "W-DATA": "Data privacy and migration specialist",
    "W-PROD": "Product architecture reviewer",
    "W-INFRA": "Infrastructure and cloud cost specialist",
    "W-VEN": "Contracts and licensing analyst",
    "W-SPEND": "IT financial analyst",
    "W-INT": "Integration planning lead",
    "W-SEP": "Carve-out and TSA specialist",
}


def _deck_titles(classification: Classification) -> tuple[str, str]:
    library = get_scope_library()
    if classification.dd_type is DdType.blended:
        return "Technology Due Diligence", "Scope of Work — product and enterprise"
    deck = library.deck(classification.dd_type.value)
    return deck.deck_title, deck.deck_subtitle


def _engagement_summary(intake: IntakeFull, classification: Classification) -> str:
    """A factual opening paragraph. The LLM rewrites this in step 8; until then it
    must still name the target and the shape of the engagement rather than be generic."""
    target = intake.target.company_name or "The target"
    business = intake.target.line_of_business or "its stated line of business"
    weeks = intake.objectives.timeline_weeks
    stage = intake.context.deal_stage

    archetype = {
        DdType.product: "a Product Technology Due Diligence",
        DdType.enterprise: "an Enterprise IT Due Diligence",
        DdType.blended: "a blended Product and Enterprise IT Due Diligence",
    }[classification.dd_type]

    scoped = f"This engagement is scoped as {archetype}"
    if stage:
        scoped += f" at the {stage.lower()} stage"
    if weeks:
        scoped += f", across approximately {weeks} weeks"

    return f"{target} operates as follows: {business.rstrip('.')}. {scoped}."


def _objectives(intake: IntakeFull) -> list[str]:
    """The four sourced DD objectives (DD_master §1.1), plus the user's stated ones."""
    objectives = [
        "Identify previously unknown or undisclosed technology risks and opportunities.",
        "Establish the one-time technology costs the transaction will incur.",
        "Establish the impact on recurring technology costs to run the business.",
        "Evaluate technology-enabled synergy and efficiency opportunities.",
    ]
    stated = intake.objectives.dd_objectives or []
    for objective in stated:
        objectives.append(f"Address the buyer's stated priority: {objective.lower()}.")
    return objectives


def _sequencing(rows: list[SelectedRow], intake: IntakeFull) -> list[SequencePhase]:
    """DD_master §7's tiered, iterative model expressed against the available weeks."""
    weeks = intake.objectives.timeline_weeks or 6
    # The sweep covers everything; each later phase names only the rows that go
    # deeper than the phase before, so a row is not counted three times.
    screen = [r.row.id for r in rows if r.in_scope]
    deeper = [r.row.id for r in rows if r.tier == 2]
    deepest = [r.row.id for r in rows if r.tier >= 3]

    sweep_end = max(1, round(weeks * 0.3))
    assess_end = max(sweep_end + 1, round(weeks * 0.75))

    phases = [
        SequencePhase(
            name="Tier 1 — sweep",
            weeks=f"Weeks 1-{sweep_end}",
            focus=(
                "Document review across every area in scope, to surface issues at the "
                "lowest cost of effort before committing depth."
            ),
            row_ids=screen,
        )
    ]
    if deeper:
        phases.append(
            SequencePhase(
                name="Tier 2 — assess",
                weeks=f"Weeks {sweep_end + 1}-{assess_end}",
                focus=(
                    "Management interviews and order-of-magnitude sizing on the areas the "
                    "sweep flagged."
                ),
                row_ids=deeper,
            )
        )
    if deepest:
        phases.append(
            SequencePhase(
                name="Tier 3 — deep dive",
                weeks=f"Weeks {assess_end + 1}-{weeks}",
                focus="Artefact-level analysis and specialist input on the highest-risk areas.",
                row_ids=deepest,
            )
        )
    phases.append(
        SequencePhase(
            name="Reporting",
            weeks=f"Week {weeks}",
            focus="Findings, disposition and open matters requiring further investigation.",
            row_ids=[],
        )
    )
    return phases


def _cost_plan(rows: list[SelectedRow], signals: list[Signal]) -> CostPlan:
    """Cost language is always a range with an assumptions register (DD_master §8.3)."""
    required = any(s.detail.get("require_cost_model") for s in signals if not s.is_unknown)
    workstreams = {ws for r in rows if r.in_scope for ws in r.row.workstreams}

    lines: list[CostLine] = []
    if "W-SPEND" in workstreams:
        lines.append(
            CostLine(
                category="recurring",
                label="Normalised IT run-rate",
                basis="Historical IT budget and actuals, adjusted for known one-offs.",
            )
        )
    if "W-INFRA" in workstreams:
        lines.append(
            CostLine(
                category="one_time",
                label="Infrastructure remediation and end-of-life replacement",
                basis="End-of-life asset register and replacement cadence.",
            )
        )
    if "W-VEN" in workstreams:
        lines.append(
            CostLine(
                category="one_time",
                label="Licence transfer, assignment and re-licensing exposure",
                basis="Contract register and assignment provisions on critical agreements.",
            )
        )
    if "W-INT" in workstreams:
        lines.append(
            CostLine(
                category="one_time",
                label="Integration cost to achieve",
                basis="Application and infrastructure overlap against the integration model.",
            )
        )
    if "W-PROD" in workstreams:
        lines.append(
            CostLine(
                category="recurring",
                label="Engineering run-rate and infrastructure unit economics",
                basis="Engineering headcount cost and hosting cost per customer.",
            )
        )

    return CostPlan(
        approach=(
            "Cost estimates are presented as order-of-magnitude ranges with a stated "
            "assumptions register, never as point estimates. Where an assumption does not "
            "hold, the sensitivity of the estimate is stated alongside it."
        ),
        lines=lines,
        assumptions_register=[
            "Estimates assume the information provided in the data room is complete and current.",
            "Costs are indicative of the current estate and exclude any post-close strategy change.",
            "Third-party pricing is assumed at list unless a negotiated rate was disclosed.",
        ],
        required=required,
    )


def _team_shape(rows: list[SelectedRow], signals: list[Signal]) -> TeamShape:
    core = [
        "Engagement lead with M&A technology diligence experience",
        "Core reviewer covering applications, infrastructure and IT spend",
    ]
    specialists = sorted(
        {
            _SPECIALIST_FOR[ws]
            for r in rows
            if r.tier >= 2
            for ws in r.row.workstreams
            if ws in _SPECIALIST_FOR
        }
    )
    note = None
    if any(s.detail.get("flag_sma_required") for s in signals if not s.is_unknown):
        note = "The estate's complexity warrants subject matter advisers beyond the core team."
    return TeamShape(core_team=core, specialists=specialists, note=note)


def _notes(signals: list[Signal]) -> list[dict[str, object]]:
    """Content blocks injected by the C-rules."""
    notes = []
    for signal in signals:
        if signal.is_unknown or not signal.detail.get("inject"):
            continue
        notes.append(
            {
                "code": signal.detail["inject"],
                "label": signal.label,
                "text": signal.detail.get("text"),
                "citation": signal.citation,
                "provenance": signal.provenance,
            }
        )
    return notes


def _to_scoped_row(selected: SelectedRow) -> ScopedRow:
    row = selected.row
    provenance = "extended" if (row.dd_master_ref or "").endswith("[EXT]") else "sourced"
    return ScopedRow(
        id=row.id,
        sn=row.sn,
        deck=selected.deck,
        title=row.title,
        lines=[ScopeLine(text=line, source_provenance=provenance) for line in row.body_lines],
        tier=selected.tier,
        tier_name=TIER_NAMES[selected.tier],
        tier_reason=selected.tier_reason,
        adjustments=selected.adjustments,
        evidence_requests=row.evidence,
        triggered_by=selected.triggered_by,
        workstreams=row.workstreams,
        dd_master_ref=row.dd_master_ref,
        out_of_scope_note=selected.out_of_scope_note,
    )


def compose_scope(
    intake: IntakeFull,
    classification: Classification,
    rows: list[SelectedRow],
    signals: list[Signal],
    exclusions: list[Exclusion],
    diligence_risks: list[str],
    generator: str = "rules",
) -> ScopeOfWorkPayloadV2:
    """Assemble the complete deterministic scope."""
    library = get_scope_library()
    rules = get_scope_rules()
    deck_title, deck_subtitle = _deck_titles(classification)

    ordered = sorted(rows, key=lambda r: (r.deck != "product", r.row.sn))

    return ScopeOfWorkPayloadV2(
        generator=generator,
        library_version=library.manifest.library_version,
        rules_version=rules.rules_version,
        deck_title=deck_title,
        deck_subtitle=deck_subtitle,
        classification=classification,
        engagement_summary=_engagement_summary(intake, classification),
        objectives=_objectives(intake),
        rows=[_to_scoped_row(r) for r in ordered],
        sequencing=_sequencing(rows, intake),
        cost_plan=_cost_plan(rows, signals),
        team_shape=_team_shape(rows, signals),
        diligence_risks=diligence_risks,
        exclusions=exclusions,
        provenance=[FiredRule.from_signal(s) for s in signals if not s.is_unknown],
        notes=_notes(signals),
    )
