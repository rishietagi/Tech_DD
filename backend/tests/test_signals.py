"""One test per DD_master §15 rule: it fires when it should, and not when it shouldn't.

These are the tests that make the weights in scope_rules.yaml safe to tune.
"""

from app.schemas.signals import SignalEffect
from app.services.scope.rules import get_scope_rules
from app.services.scope.signals import extract_signals
from tests.factories import make_intake


def codes(intake, effect: SignalEffect | None = None) -> set[str]:
    return {
        s.code
        for s in extract_signals(intake)
        if effect is None or s.effect is effect
    }


def fired(intake) -> set[str]:
    """Rule ids that actually fired (excludes dormant 'unknown' markers)."""
    return {s.code for s in extract_signals(intake) if not s.is_unknown}


def signal_for(intake, code: str):
    return next((s for s in extract_signals(intake) if s.code == code), None)


# ------------------------------------------------------------------ rules file itself


def test_rules_file_loads() -> None:
    rules = get_scope_rules()
    assert rules.rules_version == "1.0"
    assert rules.mix.start == 50
    assert len(rules.all_rules) == 37  # A1-A11, M1-M7, D1-D10, C1-C9


def test_disabled_rules_never_emit_a_signal() -> None:
    """D1 was deliberately dropped with code_access; it must be silent, not unknown."""
    assert "D1" not in codes(make_intake())


def test_dormant_rules_emit_unknown_signals_not_errors() -> None:
    unknowns = codes(make_intake(), SignalEffect.unknown)
    # Every §9.3-dependent rule plus A7 (investor_type) should be dormant.
    assert {"A7", "A8", "M4", "D3", "D9", "D10", "C2", "C3", "C4", "C7"} == unknowns


# ------------------------------------------------------------------ 15.1 archetype mix


def test_a1_fires_when_software_is_the_product() -> None:
    assert "A1" in fired(make_intake(tech_is_product="Yes, the software is the product"))
    assert "A1" not in fired(make_intake(tech_is_product="No, software supports the business"))


def test_a2_fires_for_digital_native() -> None:
    assert "A2" in fired(make_intake(digital_maturity="Digital native"))
    assert "A2" not in fired(make_intake(digital_maturity="Traditional"))


def test_a3_fires_for_traditional() -> None:
    assert "A3" in fired(make_intake(digital_maturity="Traditional"))
    assert "A3" not in fired(make_intake(digital_maturity="Digital native"))


def test_a4_fires_on_cots_or_on_erp_in_core_systems() -> None:
    assert "A4" in fired(make_intake(build_vs_buy="Predominantly COTS/packaged (ERP, CRM, etc.)"))
    # Also fires via the other_field clause even when build_vs_buy is in-house.
    assert "A4" in fired(make_intake(build_vs_buy="Predominantly in-house build", core_systems=["SAP"]))
    assert "A4" not in fired(make_intake(build_vs_buy="Predominantly in-house build"))


def test_a5_fires_for_in_house_build() -> None:
    assert "A5" in fired(make_intake(build_vs_buy="Predominantly in-house build"))
    assert "A5" not in fired(make_intake(build_vs_buy="Balanced build and buy"))


def test_a6_fires_at_the_engineering_share_threshold() -> None:
    assert "A6" in fired(make_intake(engineering_share_pct=30))
    assert "A6" in fired(make_intake(engineering_share_pct=55))
    assert "A6" not in fired(make_intake(engineering_share_pct=29))
    assert "A6" not in fired(make_intake())  # unset


def test_a9_requires_both_integration_and_a_strategic_buyer() -> None:
    both = make_intake(post_close_intent="Integrate into existing platform", investment_type="strategic")
    assert "A9" in fired(both)
    # Integration intent alone, with a financial buyer, must not fire A9.
    financial = make_intake(post_close_intent="Integrate into existing platform", investment_type="financial")
    assert "A9" not in fired(financial)


def test_a10_fires_for_on_premise() -> None:
    assert "A10" in fired(make_intake(hosting_model="Predominantly on-premise"))
    assert "A10" not in fired(make_intake(hosting_model="Public cloud"))


def test_a11_fires_when_ai_is_material() -> None:
    assert "A11" in fired(make_intake(ai_ml_dependence="Embedded in the product"))
    assert "A11" in fired(make_intake(ai_ml_dependence="Core to the value proposition"))
    assert "A11" not in fired(make_intake(ai_ml_dependence="Experimental"))
    assert "A11" not in fired(make_intake(ai_ml_dependence="None"))


# ------------------------------------------------------- 15.2 mandatory workstreams


def test_m1_always_fires_with_the_core_four() -> None:
    signal = signal_for(make_intake(), "M1")
    assert signal is not None
    assert signal.detail["workstreams"] == ["W-OPS", "W-APP", "W-INFRA", "W-SPEND"]


def test_m2_fires_only_when_sensitive_data_is_present() -> None:
    assert "M2" in fired(make_intake(data_sensitivity=["Personal data (PII)"]))
    # "None" alone must not count as sensitive data.
    assert "M2" not in fired(make_intake(data_sensitivity=["None"]))
    assert "M2" not in fired(make_intake(data_sensitivity=[]))


def test_m3_fires_only_when_a_real_regime_is_named() -> None:
    assert "M3" in fired(make_intake(compliance_regimes=["SOC 2"]))
    assert "M3" not in fired(make_intake(compliance_regimes=["None known"]))


def test_m5_fires_when_integration_is_intended() -> None:
    assert "M5" in fired(make_intake(post_close_intent="Integrate into existing platform"))
    assert "M5" not in fired(make_intake(post_close_intent="Standalone"))


def test_m6_fires_for_yes_and_partly() -> None:
    assert "M6" in fired(make_intake(tech_is_product="Yes, the software is the product"))
    assert "M6" in fired(make_intake(tech_is_product="Partly, software is a major differentiator"))
    assert "M6" not in fired(make_intake(tech_is_product="No, software supports the business"))


def test_m7_always_fires_and_carries_the_lead_time_note() -> None:
    signal = signal_for(make_intake(), "M7")
    assert signal is not None
    assert signal.detail["note_injection"] == "VEN-LEADTIME"


# -------------------------------------------------------- 15.3 depth and access gates


def test_d2_caps_everything_when_only_public_information_is_available() -> None:
    signal = signal_for(make_intake(access_level="Limited or public information"), "D2")
    assert signal is not None
    assert signal.detail["cap_all_tiers_at"] == 1
    assert "D2" not in fired(make_intake(access_level="Full (data room and management sessions)"))


def test_d4_fires_on_a_compressed_timeline() -> None:
    assert "D4" in fired(make_intake(timeline_weeks=3))
    assert "D4" in fired(make_intake(timeline_weeks=1))
    assert "D4" not in fired(make_intake(timeline_weeks=4))


def test_d5_and_d6_are_mutually_exclusive_postures() -> None:
    early = fired(make_intake(deal_stage="Exploratory"))
    assert "D5" in early and "D6" not in early

    late = fired(make_intake(deal_stage="Exclusivity"))
    assert "D6" in late and "D5" not in late

    bid = fired(make_intake(deal_stage="Bid situation"))
    assert "D5" in bid and "D6" not in bid


def test_d7_fires_for_a_financial_buyer() -> None:
    assert "D7" in fired(make_intake(investment_type="financial"))
    assert "D7" not in fired(make_intake(investment_type="strategic"))


def test_d8_requires_a_strategic_buyer_that_is_integrating() -> None:
    integrating = make_intake(investment_type="strategic", post_close_intent="Integrate into existing platform")
    signal = signal_for(integrating, "D8")
    assert signal is not None
    assert signal.detail["floor_all_tiers_at"] == 2

    # Strategic but standalone must not floor every tier.
    standalone = make_intake(investment_type="strategic", post_close_intent="Standalone")
    assert "D8" not in fired(standalone)


# ------------------------------------------------------------ 15.4 content injection


def test_c1_injects_the_erp_cost_note_when_an_erp_is_present() -> None:
    signal = signal_for(make_intake(core_systems=["SAP", "Salesforce"]), "C1")
    assert signal is not None
    assert signal.detail["inject"] == "ERP-COST"
    assert "80%" in signal.detail["text"]
    # Salesforce alone is CRM, not ERP, and must not trigger the ERP note.
    assert "C1" not in fired(make_intake(core_systems=["Salesforce"]))


def test_c5_c6_c9_always_inject() -> None:
    always_on = fired(make_intake())
    assert {"C5", "C6", "C9"} <= always_on


def test_c8_injects_ai_governance_when_ai_is_material() -> None:
    assert "C8" in fired(make_intake(ai_ml_dependence="Core to the value proposition"))
    assert "C8" not in fired(make_intake(ai_ml_dependence="None"))


# ------------------------------------------------------------------------ provenance


def test_every_signal_carries_provenance_and_a_readable_line() -> None:
    intake = make_intake(
        tech_is_product="Yes, the software is the product",
        digital_maturity="Digital native",
        core_systems=["SAP"],
    )
    for signal in extract_signals(intake):
        assert signal.provenance in ("sourced", "extended")
        assert signal.describe()
        # Extended content is never presented as sourced authority.
        if signal.provenance == "sourced" and not signal.is_unknown:
            assert signal.citation or signal.code.startswith(("M", "C"))


def test_extraction_is_deterministic() -> None:
    intake = make_intake(tech_is_product="Yes, the software is the product")
    first = [s.model_dump() for s in extract_signals(intake)]
    second = [s.model_dump() for s in extract_signals(intake)]
    assert first == second
