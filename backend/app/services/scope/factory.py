import logging

from app.core.config import Settings
from app.services.scope.base import ScopeGenerator
from app.services.scope.llm import LlmScopeGenerator
from app.services.scope.placeholder import PlaceholderScopeGenerator
from app.services.scope.rules_generator import RulesScopeGenerator

logger = logging.getLogger(__name__)

# Stateless generators, constructed once. An unrecognised SCOPE_GENERATOR degrades to
# the placeholder rather than raising, so a stale setting can never take the API down.
# "llm" is not here: it is built per call so it reads the current settings.
_GENERATORS: dict[str, ScopeGenerator] = {
    "placeholder": PlaceholderScopeGenerator(),
    "rules": RulesScopeGenerator(),
}


def get_scope_generator(settings: Settings) -> ScopeGenerator:
    requested = settings.scope_generator

    # The LLM generator is constructed per call so it picks up the current settings,
    # and it degrades to the rules output internally when no key is configured.
    if requested == "llm":
        return LlmScopeGenerator(settings)

    generator = _GENERATORS.get(requested)
    if generator is None:
        logger.warning(
            "SCOPE_GENERATOR=%r is not implemented yet; falling back to 'placeholder'.",
            requested,
        )
        return _GENERATORS["placeholder"]
    return generator


def resolve_generator_name(settings: Settings) -> str:
    """Fallback label for payloads that do not carry their own generator name (v1)."""
    return settings.scope_generator if settings.scope_generator in _GENERATORS else "placeholder"
