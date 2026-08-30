"""ModuleSelector and DepthCalibrator."""

from app.services.scope.depth import calibrate_depth
from app.services.scope.scoring import classify
from app.services.scope.selection import select_rows
from app.services.scope.signals import extract_signals
from tests.factories import make_intake

PRODUCT_HEAVY = dict(
    tech_is_product="Yes, the software is the product",
    digital_maturity="Digital native",
    build_vs_buy="Predominantly in-house build",
)


def pipeline(**overrides):
    """Run intake -> signals -> classification -> selection -> depth."""
    intake = make_intake(**overrides)
    signals = extract_signals(intake)
    classification = classify(intake, signals)
    rows = select_rows(intake, classification, signals)
    rows, exclusions, risks = calibrate_depth(rows, intake, classification, signals)
    return rows, exclusions, risks, classification


def ids(rows) -> set[str]:
    return {r.row.id for r in rows if r.in_scope}


def tier_of(rows, row_id: str) -> int:
    return next(r.tier for r in rows if r.row.id == row_id)


# ----------------------------------------------------------------------- selection


def test_product_declaration_emits_only_the_product_deck() -> None:
    rows, *_ = pipeline(dd_type_preference="Product Tech DD", **PRODUCT_HEAVY)
    assert {r.deck for r in rows} == {"product"}
    assert all(r.row.id.startswith("PD-") for r in rows)


def test_enterprise_declaration_emits_only_the_enterprise_deck() -> None:
    rows, *_ = pipeline(dd_type_preference="Enterprise IT DD")
    assert {r.deck for r in rows} == {"enterprise"}


def test_blended_declaration_emits_both_decks() -> None:
    """DD_master §3.4 — the archetypes are a weighting, never a menu."""
    rows, *_ = pipeline(dd_type_preference="Blended", **PRODUCT_HEAVY)
    assert {r.deck for r in rows} == {"product", "enterprise"}


def test_core_coverage_is_always_present() -> None:
    """DD_master G3 — the 80% core is never dropped for tailoring."""
    rows, *_ = pipeline(dd_type_preference="Enterprise IT DD")
    # Applications, IT org, infrastructure and IT financials.
    assert {"EN-01", "EN-03", "EN-04", "EN-05"} <= ids(rows)


def test_core_coverage_survives_a_compressed_timeline() -> None:
    rows, *_ = pipeline(dd_type_preference="Enterprise IT DD", timeline_weeks=1)
    assert {"EN-01", "EN-03", "EN-04", "EN-05"} <= ids(rows)


def test_every_selected_row_carries_an_audit_trail() -> None:
    """DD_master G5 — a scope a reviewer cannot audit is one they cannot defend."""
    rows, *_ = pipeline(dd_type_preference="Blended", **PRODUCT_HEAVY)
    for row in rows:
        assert row.tier_reason
        assert row.triggered_by or row.row.always_in_scope


def test_stated_objectives_lift_the_rows_that_serve_them() -> None:
    """DD_master §8.1 — explicit user priorities beat inferred ones."""
    without = pipeline(dd_type_preference="Enterprise IT DD", dd_objectives=["Confirm IP ownership"])[0]
    with_cost = pipeline(
        dd_type_preference="Enterprise IT DD", dd_objectives=["Size IT cost & run-rate"]
    )[0]
    # IT Financials (W-SPEND) should be deeper when the user asked to size IT cost.
    assert tier_of(with_cost, "EN-05") > tier_of(without, "EN-05")


def test_objective_boost_is_recorded_as_an_adjustment() -> None:
    rows, *_ = pipeline(dd_type_preference="Enterprise IT DD", dd_objectives=["Size IT cost & run-rate"])
    financials = next(r for r in rows if r.row.id == "EN-05")
    assert any("you asked to" in a for a in financials.adjustments)


# --------------------------------------------------------------------------- depth


def test_public_information_only_caps_everything_at_a_screen() -> None:
    """D2 / G2 — never promise depth the access level cannot deliver."""
    rows, _, risks, _ = pipeline(
        dd_type_preference="Enterprise IT DD",
        access_level="Limited or public information",
    )
    assert all(r.tier <= 1 for r in rows)
    assert any("public information" in risk for risk in risks)


def test_the_cap_reason_is_visible_on_each_row() -> None:
    rows, *_ = pipeline(
        dd_type_preference="Enterprise IT DD",
        access_level="Limited or public information",
    )
    capped = [r for r in rows if any("D2" in a for a in r.adjustments)]
    assert capped, "the D2 cap must be recorded on the rows it touched"


def test_compressed_timeline_allows_one_deep_dive() -> None:
    rows, _, risks, _ = pipeline(dd_type_preference="Product Tech DD", timeline_weeks=2, **PRODUCT_HEAVY)
    deep = [r for r in rows if r.tier >= 2]
    assert len(deep) == 1, "D4 permits exactly one area to keep depth"
    assert any("breadth over depth" in r or "timeline" in r for r in risks)


def test_strategic_integrator_floors_every_domain_at_assess() -> None:
    """D8 — Tier 2+ on every domain."""
    rows, *_ = pipeline(
        dd_type_preference="Enterprise IT DD",
        investment_type="strategic",
        post_close_intent="Integrate into existing platform",
        timeline_weeks=12,
    )
    assert all(r.tier >= 2 for r in rows if r.in_scope)


def test_effort_reconciliation_steps_down_and_records_the_tradeoff() -> None:
    """Never quietly truncate — each step-down is an explicit note."""
    rows, *_ = pipeline(dd_type_preference="Blended", timeline_weeks=2, **PRODUCT_HEAVY)
    stepped = [r for r in rows if any("stepped down" in a or "capped" in a for a in r.adjustments)]
    assert stepped, "a 2-week blended engagement must record trade-offs"


def test_generous_timeline_needs_no_stepdown() -> None:
    rows, *_ = pipeline(dd_type_preference="Product Tech DD", timeline_weeks=20, **PRODUCT_HEAVY)
    assert not any("stepped down" in a for r in rows for a in r.adjustments)


def test_a_normal_engagement_is_not_trimmed_to_screens() -> None:
    """Reconciliation catches an over-committed scope; it must not gut a normal one."""
    rows, *_ = pipeline(
        dd_type_preference="Product Tech DD",
        timeline_weeks=8,
        dd_objectives=["Validate scalability"],
        **PRODUCT_HEAVY,
    )
    screens = [r for r in rows if r.tier == 1]
    assert len(screens) <= 2, "an 8-week engagement should not collapse to screens"


def test_each_row_records_one_net_stepdown_not_a_running_commentary() -> None:
    rows, *_ = pipeline(dd_type_preference="Blended", timeline_weeks=1, **PRODUCT_HEAVY)
    for row in rows:
        stepdowns = [a for a in row.adjustments if "stepped down" in a]
        assert len(stepdowns) <= 1, f"{row.row.id} stacked {len(stepdowns)} step-down notes"


def test_objective_boost_targets_the_primary_workstream_only() -> None:
    """A broad objective must not lift every row — that makes the boost meaningless."""
    rows, *_ = pipeline(
        dd_type_preference="Product Tech DD",
        dd_objectives=["Assess team & key-person risk"],
        timeline_weeks=12,
        **PRODUCT_HEAVY,
    )
    boosted = [r.row.id for r in rows if any("you asked" in a for a in r.adjustments)]
    assert boosted == ["PD-06"], "only the technology-team row serves key-person risk"


def test_no_objectives_means_no_boosts() -> None:
    rows, *_ = pipeline(dd_type_preference="Product Tech DD", dd_objectives=[], timeline_weeks=12)
    assert not any("you asked" in a for r in rows for a in r.adjustments)


# ---------------------------------------------------------------------- exclusions


def test_exclusions_are_never_empty() -> None:
    """DD_master G4 — a scope that does not say what it excludes is not a scope."""
    _, exclusions, _, _ = pipeline(dd_type_preference="Product Tech DD", **PRODUCT_HEAVY)
    assert exclusions


def test_uncaptured_inputs_are_stated_not_hidden() -> None:
    _, exclusions, _, _ = pipeline(dd_type_preference="Product Tech DD", **PRODUCT_HEAVY)
    unknown_exclusion = next(
        (e for e in exclusions if "not captured" in e.subject), None
    )
    assert unknown_exclusion is not None
    assert unknown_exclusion.rule_code  # names the dormant rules


def test_low_confidence_surfaces_as_a_diligence_risk() -> None:
    _, _, risks, classification = pipeline(dd_type_preference="Let the platform decide")
    assert classification.confidence == "low"
    assert any("confidence is low" in risk for risk in risks)
