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
    JudgementSection,
    StrategyProjectsConfig,
    TeamGovernanceConfig,
    ThemeDef,
)
from app.schemas.it_budget import ItBudgetConfig
from app.services.estate import judgement

# The themes each module's code raises observations against, beside those its questions
# name. Kept here so a renamed theme in YAML fails the boot, not a scoring request.
APPLICATION_RULE_THEMES = (
    "end_of_support",
    "fragmentation",
    "customisation",
    "integration",
    "outside_systems",
    "capability_unused",
    "analytics",
    "ai_adoption",
)
DATA_TECH_RULE_THEMES = (
    "privacy",
    "data_ownership",
    "data_quality",
    "infra_support",
    "asset_lifecycle",
    "recovery",
    "capacity",
)
TEAM_RULE_THEMES = (
    "key_person",
    "outsourcing",
    "parent_dependency",
    "leadership",
    "attrition",
    "contract_expiry",
    "change_of_control",
)
PROJECT_RULE_THEMES = (
    "project_delivery",
    "spend_ahead",
    "strategy_unfunded",
    "portfolio_governance",
    "portfolio_alignment",
    "delivery_vendor",
)
BUDGET_RULE_THEMES = ("budget_variance", "budget_movement")

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


def _check(problems: list[str]) -> None:
    if problems:
        raise EstateLibraryError("; ".join(problems))


def _themes_used(where: str, themes: list[ThemeDef], used: set[str]) -> list[str]:
    known = {t.id for t in themes}
    return [f"{where}: unknown theme {t!r}" for t in sorted(used - known)]


@lru_cache(maxsize=1)
def get_applications_config() -> ApplicationsConfig:
    try:
        config = ApplicationsConfig.model_validate(_read("applications.yaml"))
    except Exception as exc:
        raise EstateLibraryError(f"applications.yaml: {exc}") from exc

    _unique([q.id for q in config.questions], "applications.yaml")
    groups = [q.group for q in config.questions]
    for required in ("criticality", "automation", "ai"):
        if groups.count(required) != 1:
            raise EstateLibraryError(f"applications.yaml: exactly one question in group {required!r}")
    for question in config.questions:
        low, high = question.scale
        if set(question.levels) != set(range(low, high + 1)):
            raise EstateLibraryError(f"applications.yaml {question.id}: levels must cover {low}..{high} exactly")
    _check(
        judgement.validate("applications.yaml", config.portfolio_sections, config.portfolio_questions, config.themes)
    )
    # Themes the rules raise in code must exist in the content.
    _check(_themes_used("applications.yaml", config.themes, set(APPLICATION_RULE_THEMES)))
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
    _unique([t.id for t in config.themes], "data_tech.yaml themes")
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
    check_ids = {c.id for s in config.check_sections for c in s.checks}
    for keyword, checks in config.tool_checks.items():
        for check in checks:
            if check not in check_ids:
                raise EstateLibraryError(f"data_tech.yaml tool_checks {keyword!r}: unknown check {check!r}")
    used = {c.theme for s in config.check_sections for c in s.checks} | set(DATA_TECH_RULE_THEMES)
    _check(_themes_used("data_tech.yaml", config.themes, used))
    return config


@lru_cache(maxsize=1)
def get_team_governance_config() -> TeamGovernanceConfig:
    try:
        config = TeamGovernanceConfig.model_validate(_read("team_governance.yaml"))
    except Exception as exc:
        raise EstateLibraryError(f"team_governance.yaml: {exc}") from exc
    _check(judgement.validate("team_governance.yaml", config.sections, config.questions, config.themes))
    _check(_themes_used("team_governance.yaml", config.themes, set(TEAM_RULE_THEMES)))
    return config


@lru_cache(maxsize=1)
def get_strategy_projects_config() -> StrategyProjectsConfig:
    try:
        config = StrategyProjectsConfig.model_validate(_read("strategy_projects.yaml"))
    except Exception as exc:
        raise EstateLibraryError(f"strategy_projects.yaml: {exc}") from exc
    _check(judgement.validate("strategy_projects.yaml", config.sections, config.questions, config.themes))
    project_section = [JudgementSection(key="projects", label="Projects")]
    _check(
        judgement.validate("strategy_projects.yaml projects", project_section, config.project_questions, config.themes)
    )
    _check(_themes_used("strategy_projects.yaml", config.themes, set(PROJECT_RULE_THEMES)))
    labels = {q.id: {o.label for o in q.options} for q in config.project_questions}
    rules = config.rules
    triage = labels.get("PJ1", set())
    if rules.stop_triage not in triage or not set(rules.priority_triage) <= triage:
        raise EstateLibraryError("strategy_projects.yaml: triage rules must name PJ1 options")
    if rules.off_track not in labels.get("PJ2", set()):
        raise EstateLibraryError("strategy_projects.yaml: off_track must be a PJ2 option")
    return config


def all_themes() -> dict[str, list[ThemeDef]]:
    """Every theme, by assessment — the report checks each names a known area."""
    return {
        "applications": get_applications_config().themes,
        "data_tech": get_data_tech_config().themes,
        "team_governance": get_team_governance_config().themes,
        "strategy_projects": get_strategy_projects_config().themes,
        "it_budget": get_it_budget_config().themes,
        "processes": _process_themes(),
    }


def _process_themes() -> list[ThemeDef]:
    from app.services.assess.findings import get_process_findings_config  # local: avoids a cycle

    return get_process_findings_config().themes


@lru_cache(maxsize=1)
def get_it_budget_config() -> ItBudgetConfig:
    try:
        config = ItBudgetConfig.model_validate(_read("it_budget.yaml"))
    except Exception as exc:
        raise EstateLibraryError(f"it_budget.yaml: {exc}") from exc
    _unique([q.id for q in config.process_questions], "it_budget.yaml")
    used = {q.theme for q in config.process_questions} | set(BUDGET_RULE_THEMES)
    _check(_themes_used("it_budget.yaml", config.themes, used))
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
    get_team_governance_config()
    get_strategy_projects_config()
    get_it_budget_config()
