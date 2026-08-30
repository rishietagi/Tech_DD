"""MixScorer, banding, confidence and the user override."""

from app.schemas.classification import DdType
from app.services.scope.rules import get_scope_rules
from app.services.scope.scoring import assess_confidence, band_for, classify, score_mix
from app.services.scope.signals import extract_signals
from tests.factories import make_intake

PRODUCT_HEAVY = dict(
    digital_maturity="Digital native",
    build_vs_buy="Predominantly in-house build",
    engineering_share_pct=45,
    ai_ml_dependence="Embedded in the product",
)

ENTERPRISE_HEAVY = dict(
    digital_maturity="Traditional",
    build_vs_buy="Predominantly COTS/packaged (ERP, CRM, etc.)",
    core_systems=["SAP"],
    hosting_model="Predominantly on-premise",
)


def mix_of(**overrides) -> int:
    intake = make_intake(**overrides)
    return score_mix(extract_signals(intake))


def classification_of(**overrides):
    intake = make_intake(**overrides)
    return classify(intake, extract_signals(intake))


# ------------------------------------------------------------------------ scoring


def test_neutral_intake_scores_the_midpoint() -> None:
    assert mix_of() == 50


def test_product_signals_push_the_mix_up() -> None:
    assert mix_of(**PRODUCT_HEAVY) > 65


def test_enterprise_signals_push_the_mix_down() -> None:
    assert mix_of(**ENTERPRISE_HEAVY) < 35


def test_mix_is_clamped_to_the_configured_range() -> None:
    low, high = get_scope_rules().mix.clamp
    assert low <= mix_of(**PRODUCT_HEAVY) <= high
    assert low <= mix_of(**ENTERPRISE_HEAVY) <= high


def test_damping_keeps_realistic_engagements_off_the_extremes() -> None:
    """The calibration note in scope_rules.yaml: without damping everything pinned to 0/100."""
    enterprise = mix_of(**ENTERPRISE_HEAVY)
    assert enterprise > 0, "a normal ERP-heavy target should not pin to absolute zero"


def test_a_mixed_target_lands_in_the_blended_band() -> None:
    mix = mix_of(
        digital_maturity="Digitally enabled",
        build_vs_buy="Predominantly in-house build",
    )
    assert 35 <= mix <= 65


# ------------------------------------------------------------------------ banding


def test_band_boundaries() -> None:
    assert band_for(0) is DdType.enterprise
    assert band_for(34) is DdType.enterprise
    assert band_for(35) is DdType.blended
    assert band_for(65) is DdType.blended
    assert band_for(66) is DdType.product
    assert band_for(100) is DdType.product


# --------------------------------------------------------------------- confidence


def test_confidence_falls_when_few_signals_fire() -> None:
    confidence, reasons = assess_confidence(extract_signals(make_intake()))
    assert confidence == "low"
    assert any("signal" in r for r in reasons)


def test_confidence_notes_conflicting_signals() -> None:
    # Software is the product (+35) but the estate is COTS/ERP (-20): a real conflict.
    intake = make_intake(
        build_vs_buy="Predominantly COTS/packaged (ERP, CRM, etc.)",
        digital_maturity="Digital native",
    )
    _, reasons = assess_confidence(extract_signals(intake))
    assert any("both archetypes" in r for r in reasons)


def test_confidence_notes_uncaptured_inputs() -> None:
    _, reasons = assess_confidence(extract_signals(make_intake()))
    assert any("not captured" in r for r in reasons)


def test_structural_unknowns_are_reported_not_scored() -> None:
    """The same 10 rules are dormant on every engagement, so scoring them would shift
    the whole scale rather than discriminate. They are reported instead — settled
    against the golden cases in step 5."""
    strong = assess_confidence(extract_signals(make_intake(**PRODUCT_HEAVY)))
    assert strong[0] == "high", "a decisively-signalled intake must not be dragged down"
    # The caveat still reaches the reader.
    assert any("not captured" in r for r in strong[1])
    # An intake that genuinely says nothing is still low.
    assert assess_confidence(extract_signals(make_intake()))[0] == "low"


def test_confidence_discriminates_between_engagements() -> None:
    """The rating has to vary, or it carries no information."""
    decisive = assess_confidence(extract_signals(make_intake(**PRODUCT_HEAVY)))[0]
    clear = assess_confidence(extract_signals(make_intake(**ENTERPRISE_HEAVY)))[0]
    silent = assess_confidence(extract_signals(make_intake()))[0]
    assert decisive == "high"
    assert clear == "medium"
    assert silent == "low"


def test_confidence_reason_reports_both_count_and_weight() -> None:
    """When the signals fall short of "high", the reason names the count and weight."""
    sparse = make_intake(dd_type_preference="Product Tech DD")
    _, reasons = assess_confidence(extract_signals(sparse))
    assert any("combined weight" in r for r in reasons)


def test_unknown_signals_never_raise_and_are_counted() -> None:
    result = classification_of()
    assert result.unknown_count == 10  # the dormant rules
    assert result.dd_mix == 50


# ----------------------------------------------------------------------- override


def test_no_override_when_platform_decides() -> None:
    result = classification_of(dd_type_preference="Let the platform decide", **PRODUCT_HEAVY)
    assert result.override_applied is False
    assert result.dd_type is result.computed_dd_type


def test_user_declaration_wins_over_the_computed_band() -> None:
    """DD_master G6 — the human overrides the engine."""
    result = classification_of(dd_type_preference="Enterprise IT DD", **PRODUCT_HEAVY)
    assert result.dd_type is DdType.enterprise
    assert result.override_applied is True
    # The engine's own view survives so the disagreement stays visible.
    assert result.computed_dd_type is DdType.product
    assert result.disagrees is True


def test_override_that_agrees_is_not_flagged_as_disagreement() -> None:
    result = classification_of(dd_type_preference="Product Tech DD", **PRODUCT_HEAVY)
    assert result.override_applied is True
    assert result.disagrees is False


def test_declared_blend_recentres_a_polarised_mix() -> None:
    result = classification_of(dd_type_preference="Blended", **PRODUCT_HEAVY)
    assert result.dd_type is DdType.blended
    assert 35 <= result.dd_mix <= 65
    assert result.computed_dd_mix > 65  # the computation is untouched


def test_computed_values_are_always_populated() -> None:
    for preference in ("Let the platform decide", "Product Tech DD", "Enterprise IT DD", "Blended"):
        result = classification_of(dd_type_preference=preference)
        assert result.computed_dd_type is not None
        assert 0 <= result.computed_dd_mix <= 100
