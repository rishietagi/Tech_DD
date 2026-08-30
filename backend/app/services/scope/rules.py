"""Loads and validates scope_rules.yaml.

Same contract as the scope library: content lives in YAML so a practitioner can tune a
weight without touching Python, and a malformed file fails loudly at load rather than
producing a quietly wrong scope.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

RULES_FILE = Path(__file__).resolve().parents[2] / "reference" / "scope_rules.yaml"

RuleStatus = Literal["active", "disabled", "dormant"]


class MixBands(BaseModel):
    model_config = {"extra": "forbid"}

    enterprise: tuple[int, int]
    blended: tuple[int, int]
    product: tuple[int, int]


class MixConfig(BaseModel):
    model_config = {"extra": "forbid"}

    start: int
    clamp: tuple[int, int]
    bands: MixBands
    # Scales every mix_delta before it is applied. See the calibration note in
    # scope_rules.yaml: the sourced weights saturate, so realistic engagements would
    # otherwise all pin to 0 or 100 and the blended band would be unreachable.
    damping: float = Field(default=1.0, gt=0, le=1)


class ConfidenceConfig(BaseModel):
    model_config = {"extra": "forbid"}

    high_min_signals: int
    medium_min_signals: int
    conflict_penalty: int
    dormant_penalty_per_3: int


class Rule(BaseModel):
    """One rule from any of the four sections. Fields are a union across sections."""

    model_config = {"extra": "forbid"}

    id: str
    status: RuleStatus
    label: str | None = None
    citation: str | None = None
    provenance: Literal["sourced", "extended"] = "sourced"

    disabled_reason: str | None = None
    dormant_reason: str | None = None

    field: str | None = None
    when: dict[str, Any] | None = None
    requires: dict[str, Any] | None = None
    always: bool = False

    # effects
    mix_delta: int | None = None
    force_workstream: dict[str, Any] | None = None
    workstreams: list[str] = Field(default_factory=list)
    min_tier: int | None = None
    cap_all_tiers_at: int | None = None
    floor_all_tiers_at: int | None = None
    tier_bump: dict[str, Any] | None = None
    allow_single_deep_dive: bool = False
    strip_interview_evidence: bool = False
    flag_sma_required: bool = False
    sweep_then_target: bool = False
    prefer_breadth: bool = False
    require_cost_model: bool = False
    posture: str | None = None
    inject: str | None = None
    text: str | None = None
    note_injection: str | None = None


class ScopeRules(BaseModel):
    model_config = {"extra": "forbid"}

    rules_version: str
    source: str
    mix: MixConfig
    confidence: ConfidenceConfig
    archetype: list[Rule]
    mandatory: list[Rule]
    depth: list[Rule]
    content: list[Rule]

    @property
    def all_rules(self) -> list[Rule]:
        return [*self.archetype, *self.mandatory, *self.depth, *self.content]

    def active(self, section: list[Rule]) -> list[Rule]:
        return [r for r in section if r.status == "active"]

    def dormant(self) -> list[Rule]:
        return [r for r in self.all_rules if r.status == "dormant"]


class ScopeRulesError(RuntimeError):
    """Raised when scope_rules.yaml is missing or malformed."""


@lru_cache(maxsize=1)
def get_scope_rules() -> ScopeRules:
    if not RULES_FILE.exists():
        raise ScopeRulesError(f"scope rules file not found: {RULES_FILE}")
    try:
        with RULES_FILE.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ScopeRulesError(f"scope_rules.yaml is not valid YAML: {exc}") from exc

    try:
        rules = ScopeRules.model_validate(data)
    except Exception as exc:
        raise ScopeRulesError(f"scope_rules.yaml failed validation: {exc}") from exc

    ids = [r.id for r in rules.all_rules]
    if len(ids) != len(set(ids)):
        raise ScopeRulesError("scope_rules.yaml has duplicate rule ids")

    active = sum(1 for r in rules.all_rules if r.status == "active")
    dormant = sum(1 for r in rules.all_rules if r.status == "dormant")
    disabled = sum(1 for r in rules.all_rules if r.status == "disabled")
    logger.info(
        "Loaded scope rules v%s: %d active, %d dormant, %d disabled",
        rules.rules_version,
        active,
        dormant,
        disabled,
    )
    return rules


def reload_scope_rules() -> ScopeRules:
    get_scope_rules.cache_clear()
    return get_scope_rules()
