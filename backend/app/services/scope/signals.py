"""SignalExtractor — pure IntakeFull -> list[Signal].

No I/O beyond the cached rules load, no randomness: the same intake always yields the
same signals. That is what makes the golden-case tests meaningful and the audit trail
trustworthy.

Dormant rules (their input field is not on this intake) emit an `unknown` signal rather
than being skipped silently. Those lower confidence but never block generation —
DD_master §13's rule that a missing value is an unknown, not an error.
"""

from typing import Any

from app.schemas.intake import IntakeFull
from app.schemas.signals import Signal, SignalEffect
from app.services.scope.rules import Rule, ScopeRules, get_scope_rules


def _resolve(intake: IntakeFull, dotted: str) -> Any:
    """Read `section.field` off the intake. Missing section or field -> None."""
    section_name, _, field_name = dotted.partition(".")
    section = getattr(intake, section_name, None)
    if section is None:
        return None
    return getattr(section, field_name, None)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, list | tuple | set) else [value]


def _matches(condition: dict[str, Any], value: Any, intake: IntakeFull) -> bool:
    """Evaluate one `when:` clause against a value."""
    if "any_of" in condition:
        return any(_matches(sub, value, intake) for sub in condition["any_of"])
    if "all_of" in condition:
        return all(_matches(sub, value, intake) for sub in condition["all_of"])

    # A clause may redirect to a different field (A4 checks core_systems as well).
    if "other_field" in condition:
        value = _resolve(intake, condition["other_field"])

    if "equals" in condition:
        return bool(value == condition["equals"])
    if "in" in condition:
        return value is not None and value in condition["in"]
    if "intersects" in condition:
        return bool(set(_as_list(value)) & set(condition["intersects"]))
    if "non_empty_excluding" in condition:
        excluded = set(condition["non_empty_excluding"])
        return bool([v for v in _as_list(value) if v not in excluded])
    if "gte" in condition:
        return value is not None and value >= condition["gte"]
    if "lte" in condition:
        return value is not None and value <= condition["lte"]
    return False


def _requires_met(rule: Rule, intake: IntakeFull) -> bool:
    if not rule.requires:
        return True
    required_field = rule.requires.get("field")
    if not required_field:
        return True
    value = _resolve(intake, required_field)
    return _matches({k: v for k, v in rule.requires.items() if k != "field"}, value, intake)


def _fires(rule: Rule, intake: IntakeFull) -> bool:
    if rule.always:
        return True
    if not rule.field or not rule.when:
        return False
    if not _requires_met(rule, intake):
        return False
    return _matches(rule.when, _resolve(intake, rule.field), intake)


def _effect_for(rule: Rule) -> SignalEffect:
    if rule.mix_delta is not None:
        return SignalEffect.mix_delta
    if rule.workstreams or rule.force_workstream:
        return SignalEffect.force_module
    if rule.cap_all_tiers_at is not None:
        return SignalEffect.cap_tier
    if rule.floor_all_tiers_at is not None:
        return SignalEffect.floor_tier
    if rule.tier_bump is not None:
        return SignalEffect.tier_bump
    if rule.inject is not None:
        return SignalEffect.inject_content
    if rule.posture is not None:
        return SignalEffect.posture
    return SignalEffect.posture


def _detail_for(rule: Rule) -> dict[str, Any]:
    detail: dict[str, Any] = {}
    if rule.mix_delta is not None:
        detail["mix_delta"] = rule.mix_delta
    if rule.workstreams:
        detail["workstreams"] = rule.workstreams
    if rule.min_tier is not None:
        detail["min_tier"] = rule.min_tier
    if rule.force_workstream:
        detail["force_workstream"] = rule.force_workstream
    if rule.cap_all_tiers_at is not None:
        detail["cap_all_tiers_at"] = rule.cap_all_tiers_at
    if rule.floor_all_tiers_at is not None:
        detail["floor_all_tiers_at"] = rule.floor_all_tiers_at
    if rule.tier_bump:
        detail["tier_bump"] = rule.tier_bump
    if rule.inject:
        detail["inject"] = rule.inject
    if rule.text:
        detail["text"] = rule.text
    if rule.posture:
        detail["posture"] = rule.posture
    for flag in (
        "allow_single_deep_dive",
        "strip_interview_evidence",
        "flag_sma_required",
        "sweep_then_target",
        "prefer_breadth",
        "require_cost_model",
    ):
        if getattr(rule, flag):
            detail[flag] = True
    if rule.note_injection:
        detail["note_injection"] = rule.note_injection
    return detail


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list | tuple | set):
        return ", ".join(str(v) for v in value) or None
    return str(value)


def extract_signals(intake: IntakeFull, rules: ScopeRules | None = None) -> list[Signal]:
    """Every rule that fired, plus an `unknown` signal per dormant rule."""
    rules = rules or get_scope_rules()
    signals: list[Signal] = []

    for rule in rules.all_rules:
        if rule.status == "disabled":
            continue

        if rule.status == "dormant":
            signals.append(
                Signal(
                    code=rule.id,
                    label=rule.label or rule.id,
                    effect=SignalEffect.unknown,
                    source_field=rule.field,
                    source_value=None,
                    detail={"reason": rule.dormant_reason} if rule.dormant_reason else {},
                    citation=rule.citation,
                    provenance=rule.provenance,
                )
            )
            continue

        if not _fires(rule, intake):
            continue

        signals.append(
            Signal(
                code=rule.id,
                label=rule.label or rule.id,
                effect=_effect_for(rule),
                source_field=rule.field,
                source_value=_stringify(_resolve(intake, rule.field)) if rule.field else None,
                detail=_detail_for(rule),
                citation=rule.citation,
                provenance=rule.provenance,
            )
        )

    return signals
