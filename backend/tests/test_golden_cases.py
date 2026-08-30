"""Golden cases — PHASE2_SCOPE_ENGINE §10.

Six representative engagements with asserted deterministic output. These are what make
the weights in scope_rules.yaml safe to tune: change a weight, and the case that no
longer holds tells you what you broke.

Adapted from the spec's table for the intake as it actually stands: G4's `code_access`
condition is dropped (the field was removed at Rishi's request, taking rule D1 with it),
and G2's carve-out is expressed through post-close intent rather than the absent
`deal_type`. Deviations are noted per case.

Never snapshot LLM output — these cover the rules generator only.
"""

import pytest

from app.schemas.classification import DdType
from app.services.scope.rules_generator import RulesScopeGenerator
from tests.factories import make_intake

GENERATOR = RulesScopeGenerator()


def scope_for(**overrides):
    return GENERATOR.generate(make_intake(**overrides))


def row(scope, row_id: str):
    return next((r for r in scope.rows if r.id == row_id), None)


def row_ids(scope) -> set[str]:
    return {r.id for r in scope.rows}


# ----------------------------------------------------------------------------- G1

G1 = dict(
    deal_name="Project Beacon",
    company_name="Northwind Software",
    line_of_business="Sells a B2B SaaS workflow platform to mid-market logistics operators.",
    dd_type_preference="Product Tech DD",
    tech_is_product="Yes, the software is the product",
    digital_maturity="Digital native",
    build_vs_buy="Predominantly in-house build",
    engineering_share_pct=50,
    hosting_model="Public cloud",
    stake="minority",
    timeline_weeks=8,
    access_level="Full (data room and management sessions)",
)


def test_g1_digital_native_saas_is_product_heavy() -> None:
    """Digital-native B2B SaaS, minority growth, 8 weeks -> product-heavy."""
    scope = scope_for(**G1)
    assert scope.classification.dd_type is DdType.product
    assert scope.classification.computed_dd_mix >= 70
    # The product deck ships; no enterprise rows.
    assert all(r.deck == "product" for r in scope.rows)
    # Nine of ten rows open. PD-05 (IT Regulatory aspects) correctly stays out: this
    # target named no compliance regimes, so M3 does not fire and the row is not
    # always-in-scope. Tailoring means rows can be absent, not that all ten always run.
    assert row(scope, "PD-05") is None
    assert len(scope.rows) == 9


def test_g1_opens_the_product_platform_rows_deeply() -> None:
    scope = scope_for(**G1)
    architecture = row(scope, "PD-01")
    assert architecture is not None
    assert architecture.tier >= 2, "the architecture row must be assessed, not screened"


def test_g1_has_no_separation_workstream() -> None:
    """W-SEP is carve-out only; a minority growth deal must not open it."""
    scope = scope_for(**G1)
    assert not any("W-SEP" in r.workstreams for r in scope.rows)


# ----------------------------------------------------------------------------- G2

G2 = dict(
    deal_name="Project Foundry",
    company_name="Kestrel Industrial",
    line_of_business="Manufactures and distributes industrial fastening components to OEM customers.",
    dd_type_preference="Enterprise IT DD",
    tech_is_product="No, software supports the business",
    digital_maturity="Traditional",
    build_vs_buy="Predominantly COTS/packaged (ERP, CRM, etc.)",
    core_systems=["SAP", "Salesforce"],
    hosting_model="Predominantly on-premise",
    investment_type="strategic",
    post_close_intent="Carve-out from parent",
    stake="majority",
    timeline_weeks=6,
)


def test_g2_erp_heavy_carveout_is_enterprise_heavy() -> None:
    """Industrial carve-out, PE majority, ERP-heavy, 6 weeks -> enterprise-heavy.

    Deviation from the spec: `deal_type = carve_out` is not on the intake, so M4/C3
    cannot fire and W-SEP does not open. Recorded as a known gap, not a passing test.
    """
    scope = scope_for(**G2)
    assert scope.classification.dd_type is DdType.enterprise
    assert scope.classification.computed_dd_mix <= 30
    assert all(r.deck == "enterprise" for r in scope.rows)


def test_g2_injects_the_erp_cost_note() -> None:
    """C1 — ERP is roughly 80% of integration cost."""
    scope = scope_for(**G2)
    erp_note = next((n for n in scope.notes if n["code"] == "ERP-COST"), None)
    assert erp_note is not None
    assert "80%" in erp_note["text"]


def test_g2_opens_vendors_and_contracts_at_depth() -> None:
    """M7 — contract transfer is implied, and licences are the carve-out risk."""
    scope = scope_for(**G2)
    contracts = row(scope, "EN-09")
    assert contracts is not None
    assert contracts.tier >= 2


# ----------------------------------------------------------------------------- G3

G3 = dict(
    deal_name="Project Vitals",
    company_name="Corvus Health",
    line_of_business="Operates a patient-scheduling and records platform used by private clinics.",
    dd_type_preference="Blended",
    tech_is_product="Partly, software is a major differentiator",
    digital_maturity="Digitally enabled",
    data_sensitivity=["Health data (PHI)", "Personal data (PII)"],
    compliance_regimes=["HIPAA", "SOC 2"],
    investment_type="strategic",
    post_close_intent="Integrate into existing platform",
    timeline_weeks=10,
)


def test_g3_healthtech_integration_is_blended_across_both_decks() -> None:
    scope = scope_for(**G3)
    assert scope.classification.dd_type is DdType.blended
    decks = {r.deck for r in scope.rows}
    assert decks == {"product", "enterprise"}


def test_g3_regulated_data_forces_security_and_compliance_depth() -> None:
    """M2/M3 — PHI and named regimes make these mandatory at Tier 2+."""
    scope = scope_for(**G3)
    security = row(scope, "PD-04")
    assert security is not None and security.tier >= 2
    regulatory = row(scope, "PD-05")
    assert regulatory is not None and regulatory.tier >= 2


def test_g3_strategic_integrator_floors_every_domain(  # D8
) -> None:
    scope = scope_for(**G3)
    in_scope = [r for r in scope.rows if r.tier > 0]
    assert all(r.tier >= 2 for r in in_scope), "D8 requires Tier 2+ on every domain"


# ----------------------------------------------------------------------------- G4

G4 = dict(
    **{k: v for k, v in G1.items() if k not in {"timeline_weeks", "access_level"}},
    timeline_weeks=2,
    access_level="Data room only",
    deal_stage="Exploratory",
)


def test_g4_compressed_early_stage_is_a_red_flag_review() -> None:
    """Same shape as G1 but 2 weeks and early stage -> breadth, one deep dive.

    Deviation: the spec's `code_access = none` clause is gone with the field, so this
    case tests D4 (timeline) and D5 (stage) rather than D1.
    """
    scope = scope_for(**G4)
    deep = [r for r in scope.rows if r.tier >= 2]
    assert len(deep) == 1, "D4 permits exactly one area to keep depth"


def test_g4_names_the_timeline_constraint_as_a_diligence_risk() -> None:
    scope = scope_for(**G4)
    assert any("timeline" in risk or "breadth" in risk for risk in scope.diligence_risks)


def test_g4_still_covers_every_row_at_screen_depth() -> None:
    """G3 — the core is never dropped to make room for tailoring."""
    scope = scope_for(**G4)
    assert all(r.tier >= 1 for r in scope.rows)


# ----------------------------------------------------------------------------- G5


def test_g5_sparse_intake_yields_low_confidence_without_crashing() -> None:
    """Most optional fields empty -> confidence low, unknowns recorded, no error."""
    scope = scope_for(dd_type_preference="Let the platform decide")
    assert scope.classification.confidence == "low"
    assert scope.classification.unknown_count > 0
    assert scope.classification.confidence_reasons
    # Still a publishable document.
    assert scope.rows
    assert scope.exclusions


def test_g5_unknown_inputs_are_stated_in_the_exclusions() -> None:
    scope = scope_for(dd_type_preference="Let the platform decide")
    assert any("not captured" in e.subject for e in scope.exclusions)


# ----------------------------------------------------------------------------- G6


def test_g6_declared_archetype_overrides_the_computed_one() -> None:
    """DD_master G6 — the human overrides the engine, and the disagreement is visible."""
    scope = scope_for(**{**G1, "dd_type_preference": "Enterprise IT DD"})
    assert scope.classification.dd_type is DdType.enterprise
    assert scope.classification.computed_dd_type is DdType.product
    assert scope.classification.override_applied is True
    assert scope.classification.disagrees is True
    # The declaration decides which deck ships.
    assert all(r.deck == "enterprise" for r in scope.rows)


# ------------------------------------------------------------- invariants (G1-G6)

ALL_CASES = {
    "G1": G1,
    "G2": G2,
    "G3": G3,
    "G4": G4,
    "G5": dict(dd_type_preference="Let the platform decide"),
    "G6": {**G1, "dd_type_preference": "Enterprise IT DD"},
}


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_every_case_states_its_exclusions(name: str) -> None:
    """DD_master G4 — a scope that does not say what it excludes is not a scope."""
    assert scope_for(**ALL_CASES[name]).exclusions


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_every_case_shows_its_provenance(name: str) -> None:
    """DD_master G5 — a scope a reviewer cannot audit is one they cannot defend."""
    scope = scope_for(**ALL_CASES[name])
    assert scope.provenance
    assert all(p.code for p in scope.provenance)


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_every_case_uses_order_of_magnitude_cost_language(name: str) -> None:
    """DD_master §8.3 — ranges with an assumptions register, never point estimates."""
    plan = scope_for(**ALL_CASES[name]).cost_plan
    assert "order-of-magnitude" in plan.approach
    assert "never as point estimates" in plan.approach
    assert plan.assumptions_register


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_every_case_is_publishable_without_an_llm(name: str) -> None:
    """The rules generator alone must produce a complete scope."""
    scope = scope_for(**ALL_CASES[name])
    assert scope.is_placeholder is False
    assert scope.generator == "rules"
    assert scope.engagement_summary
    assert scope.objectives
    assert scope.rows
    assert scope.sequencing
    assert scope.team_shape.core_team


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_every_row_keeps_its_kpmg_wording_and_audit_trail(name: str) -> None:
    scope = scope_for(**ALL_CASES[name])
    for r in scope.rows:
        assert r.title.strip()
        assert r.lines and all(line.text.strip() for line in r.lines)
        assert r.tier_reason
        assert r.evidence_requests
        assert r.dd_master_ref


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_generation_is_deterministic(name: str) -> None:
    first = scope_for(**ALL_CASES[name]).model_dump(mode="json")
    second = scope_for(**ALL_CASES[name]).model_dump(mode="json")
    assert first == second


# ------------------------------------------------------------------- calibration

# The settled confidence distribution. This is the snapshot that makes the weights in
# scope_rules.yaml safe to tune: change one, and the case that no longer holds tells
# you what you broke.
EXPECTED_CONFIDENCE = {
    "G1": "high",    # digital-native SaaS, 4 signals
    "G2": "medium",  # ERP-heavy manufacturer, 3 signals
    "G3": "low",     # genuinely mixed, 1 signal
    "G4": "high",    # same shape as G1
    "G5": "low",     # sparse intake, 0 signals
    "G6": "high",    # same shape as G1, archetype overridden
}


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_confidence_matches_the_settled_calibration(name: str) -> None:
    scope = scope_for(**ALL_CASES[name])
    assert scope.classification.confidence == EXPECTED_CONFIDENCE[name]


@pytest.mark.parametrize("name", sorted(ALL_CASES))
def test_uncaptured_inputs_are_always_disclosed(name: str) -> None:
    """Structural unknowns no longer move the rating, so they must still be stated."""
    scope = scope_for(**ALL_CASES[name])
    assert any("not captured" in r for r in scope.classification.confidence_reasons)


def test_confidence_is_not_uniform_across_cases() -> None:
    """A rating identical on every engagement carries no information."""
    ratings = {scope_for(**case).classification.confidence for case in ALL_CASES.values()}
    assert len(ratings) >= 2
