"""MixScorer and ArchetypeResolver.

Turns signals into a mix score, a band, and a confidence rating — then lets the user's
declared preference override the band while keeping the computed value visible.
"""

from app.reference.enums import DdTypePreference
from app.schemas.classification import Classification, Confidence, DdType
from app.schemas.intake import IntakeFull
from app.schemas.signals import Signal
from app.services.scope.rules import ScopeRules, get_scope_rules

# The user's declaration maps onto an archetype. "Let the platform decide" is absent
# deliberately: it means no override, so the computed band stands.
_PREFERENCE_TO_TYPE = {
    DdTypePreference.product.value: DdType.product,
    DdTypePreference.enterprise.value: DdType.enterprise,
    DdTypePreference.blended.value: DdType.blended,
    # "AI-heavy Tech DD" is absent on purpose, alongside "Let the platform decide":
    # there is no AI-heavy deck yet, so declaring it applies no override and the
    # engagement classifies from the computed mix. The lookup below uses .get(), so an
    # unmapped declaration degrades to "no override" rather than raising.
}

# A mix rule counts as "strong" when it moves the needle by this much or more. Used to
# detect genuine conflict (both directions pulling hard) rather than mild noise.
_STRONG_DELTA = 15


def score_mix(signals: list[Signal], rules: ScopeRules | None = None) -> int:
    """Apply every mix_delta from the start point, damped and clamped."""
    rules = rules or get_scope_rules()
    raw = sum(int(s.detail.get("mix_delta", 0)) for s in signals if not s.is_unknown)
    damped = round(raw * rules.mix.damping)
    low, high = rules.mix.clamp
    return max(low, min(high, rules.mix.start + damped))


def band_for(mix: int, rules: ScopeRules | None = None) -> DdType:
    rules = rules or get_scope_rules()
    bands = rules.mix.bands
    if mix <= bands.enterprise[1]:
        return DdType.enterprise
    if mix >= bands.product[0]:
        return DdType.product
    return DdType.blended


def assess_confidence(
    signals: list[Signal], rules: ScopeRules | None = None
) -> tuple[Confidence, list[str]]:
    """How much the computed mix should be trusted, and why.

    Falls when few rules fired, when strong rules pull both ways, or when dormant
    inputs mean we are reasoning on partial information (DD_master §5, §13).
    """
    rules = rules or get_scope_rules()
    cfg = rules.confidence

    mix_signals = [s for s in signals if not s.is_unknown and s.detail.get("mix_delta")]
    unknowns = [s for s in signals if s.is_unknown]
    reasons: list[str] = []

    # How much the signals actually say, not merely how many fired. A single strong
    # rule ("software is the product", +35) is more informative than three weak ones,
    # and the resulting mix is what confidence is really about — so a decisive score
    # counts for as much as a broad one.
    count = len(mix_signals)
    conviction = sum(abs(int(s.detail.get("mix_delta", 0))) for s in mix_signals)
    effective = max(count, conviction // 20)

    if effective >= cfg.high_min_signals:
        level = 2  # high
    elif effective >= cfg.medium_min_signals:
        level = 1  # medium
    else:
        level = 0  # low
    if effective < cfg.high_min_signals:
        reasons.append(
            f"{count} archetype signal{'s' if count != 1 else ''} fired"
            f" (combined weight {conviction})"
        )

    # Strong disagreement between the two directions.
    pulls_product = any(s.detail.get("mix_delta", 0) >= _STRONG_DELTA for s in mix_signals)
    pulls_enterprise = any(s.detail.get("mix_delta", 0) <= -_STRONG_DELTA for s in mix_signals)
    if pulls_product and pulls_enterprise:
        level -= cfg.conflict_penalty
        reasons.append("Strong signals pull toward both archetypes")

    # Reasoning on partial information. The dormant rules are STRUCTURAL: the same ten
    # are absent on every engagement, because those fields are not on the intake. A
    # penalty that applies identically to every scope shifts the whole scale rather
    # than discriminating between engagements, which is how a decisively-signalled
    # target (traditional, COTS-heavy, on-premise) ended up rated "low".
    #
    # So it is reported, not scored: the reason always appears, and the caveat reaches
    # the reader through the exclusions section, but the rating stays free to reflect
    # what this particular intake actually said. Settled against the six golden cases
    # (PHASE2_SPEC §10), which is what the calibration note asked for.
    if unknowns:
        reasons.append(
            f"{len(unknowns)} scoping inputs are not captured by this intake "
            "(deal type, integration model, relative size, IT complexity, management access)"
        )

    level = max(0, min(2, level))
    confidence: Confidence = ("low", "medium", "high")[level]
    return confidence, reasons


def classify(
    intake: IntakeFull, signals: list[Signal], rules: ScopeRules | None = None
) -> Classification:
    """Full archetype verdict: computed value, user override, confidence."""
    rules = rules or get_scope_rules()

    computed_mix = score_mix(signals, rules)
    computed_type = band_for(computed_mix, rules)
    confidence, reasons = assess_confidence(signals, rules)

    preference = intake.objectives.dd_type_preference
    override_type = _PREFERENCE_TO_TYPE.get(preference) if preference else None

    if override_type is not None:
        # The declaration decides which deck ships; the computed mix is retained so the
        # disagreement stays visible. A declared blend re-centres the mix only when the
        # computation did not already land there.
        final_type = override_type
        final_mix = computed_mix
        if override_type is DdType.blended and band_for(computed_mix, rules) is not DdType.blended:
            final_mix = 50
        return Classification(
            dd_type=final_type,
            dd_mix=final_mix,
            confidence=confidence,
            computed_dd_type=computed_type,
            computed_dd_mix=computed_mix,
            override_applied=True,
            override_source=preference,
            signals=signals,
            unknown_count=sum(1 for s in signals if s.is_unknown),
            confidence_reasons=reasons,
        )

    return Classification(
        dd_type=computed_type,
        dd_mix=computed_mix,
        confidence=confidence,
        computed_dd_type=computed_type,
        computed_dd_mix=computed_mix,
        override_applied=False,
        override_source=None,
        signals=signals,
        unknown_count=sum(1 for s in signals if s.is_unknown),
        confidence_reasons=reasons,
    )
