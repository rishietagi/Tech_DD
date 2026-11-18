"""Loads and validates the estate content from `reference/estate/*.yaml`.

Same contract as the scope library and the process questionnaires: content a practitioner
edits without a developer, failing loudly at load rather than producing a quietly wrong
score or a form with a missing field.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.schemas.estate import (
    INVENTORY_KINDS,
    ApplicationsConfig,
    DataTechConfig,
    InventoryDefinition,
)
from app.schemas.it_budget import ItBudgetConfig

ESTATE_DIR = Path(__file__).resolve().parents[2] / "reference" / "estate"


class EstateLibraryError(RuntimeError):
    """Raised when the estate content on disk is missing or malformed."""


def _read(name: str) -> dict[str, Any]:
    path = ESTATE_DIR / name
    if not path.exists():
        raise EstateLibraryError(f"estate content file not found: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise EstateLibraryError(f"{name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise EstateLibraryError(f"{name} must contain a mapping at the top level")
    return data


def _unique(ids: list[str], where: str) -> None:
    seen: set[str] = set()
    for candidate in ids:
        if candidate in seen:
            raise EstateLibraryError(f"{where}: duplicate id {candidate!r}")
        seen.add(candidate)


@lru_cache(maxsize=1)
def get_inventory_definition() -> InventoryDefinition:
    try:
        definition = InventoryDefinition.model_validate(_read("inventory.yaml"))
    except EstateLibraryError:
        raise
    except Exception as exc:
        raise EstateLibraryError(f"inventory.yaml: {exc}") from exc

    prefixes: set[str] = set()
    for kind, kdef in definition.kinds.items():
        keys = [f.key for f in kdef.fields]
        _unique(keys, f"inventory.yaml {kind}")
        if "name" not in keys:
            raise EstateLibraryError(f"inventory.yaml {kind}: every kind needs a `name` field")
        for field in kdef.fields:
            if field.type in ("select", "multi_select") and not field.options:
                raise EstateLibraryError(f"inventory.yaml {kind}.{field.key}: a {field.type} needs options")
        if kdef.ref_prefix in prefixes:
            raise EstateLibraryError(f"inventory.yaml: ref prefix {kdef.ref_prefix!r} reused")
        prefixes.add(kdef.ref_prefix)
    missing = set(INVENTORY_KINDS) - set(definition.kinds)
    if missing:
        raise EstateLibraryError(f"inventory.yaml: kinds missing: {sorted(missing)}")
    return definition


@lru_cache(maxsize=1)
def get_applications_config() -> ApplicationsConfig:
    try:
        config = ApplicationsConfig.model_validate(_read("applications.yaml"))
    except Exception as exc:
        raise EstateLibraryError(f"applications.yaml: {exc}") from exc

    _unique([q.id for q in config.questions], "applications.yaml")
    groups = {q.group for q in config.questions}
    for required in ("criticality", "business_fit", "technical_fit", "automation", "ai"):
        if required not in groups:
            raise EstateLibraryError(f"applications.yaml: no question in group {required!r}")
    for question in config.questions:
        low, high = question.scale
        if set(question.levels) != set(range(low, high + 1)):
            raise EstateLibraryError(f"applications.yaml {question.id}: levels must cover {low}..{high} exactly")
    for key in ("high_high", "high_low", "low_high", "low_low"):
        if key not in config.disposition.matrix:
            raise EstateLibraryError(f"applications.yaml: disposition matrix lacks {key!r}")
    return config


@lru_cache(maxsize=1)
def get_data_tech_config() -> DataTechConfig:
    try:
        config = DataTechConfig.model_validate(_read("data_tech.yaml"))
    except Exception as exc:
        raise EstateLibraryError(f"data_tech.yaml: {exc}") from exc

    ids = [q.id for q in config.domain_questions] + [q.id for q in config.platform_questions]
    ids += [c.id for s in config.check_sections for c in s.checks]
    _unique(ids, "data_tech.yaml")
    total = sum(q.weight for q in config.domain_questions)
    if abs(total - 100) > 1e-9:
        raise EstateLibraryError(f"data_tech.yaml: domain question weights sum to {total}, not 100")
    for question in [*config.domain_questions, *config.platform_questions]:
        if not question.options:
            raise EstateLibraryError(f"data_tech.yaml {question.id}: no options")
        for option in question.options:
            if option.value is not None and not 0 <= option.value <= 1:
                raise EstateLibraryError(f"data_tech.yaml {question.id}: option value {option.value} outside 0..1")
    sections = {"data", "platforms", *[s.key for s in config.check_sections]}
    if set(config.section_weights) != sections:
        raise EstateLibraryError(f"data_tech.yaml: section_weights must name exactly {sorted(sections)}")
    if abs(sum(config.section_weights.values()) - 100) > 1e-9:
        raise EstateLibraryError("data_tech.yaml: section weights must sum to 100")
    if set(config.check_statuses) != {"pass", "partial", "fail", "unknown"}:
        raise EstateLibraryError("data_tech.yaml: check_statuses must be pass/partial/fail/unknown")
    return config


@lru_cache(maxsize=1)
def get_it_budget_config() -> ItBudgetConfig:
    try:
        config = ItBudgetConfig.model_validate(_read("it_budget.yaml"))
    except Exception as exc:
        raise EstateLibraryError(f"it_budget.yaml: {exc}") from exc
    _unique([q.id for q in config.process_questions], "it_budget.yaml")
    for question in config.process_questions:
        for option in question.options:
            if option.finding and option.severity is None:
                raise EstateLibraryError(f"it_budget.yaml {question.id}: an option with a finding needs a severity")
    if not 1 <= config.default_period_years <= 10:
        raise EstateLibraryError("it_budget.yaml: default_period_years must be 1..10")
    return config


def validate_all() -> None:
    """Load every estate file once — called at startup so a bad edit fails the boot."""
    get_inventory_definition()
    get_applications_config()
    get_data_tech_config()
    get_it_budget_config()
