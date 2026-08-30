import logging

from app.core.config import Settings
from app.services.scope.base import ScopeGenerator
from app.services.scope.placeholder import PlaceholderScopeGenerator

logger = logging.getLogger(__name__)

# Registered generators. Phase 2 adds "rules" and "llm" here as they land; until then
# an unbuilt selection degrades to the placeholder rather than raising, so a stale
# SCOPE_GENERATOR value can never take the API down.
_GENERATORS: dict[str, ScopeGenerator] = {
    "placeholder": PlaceholderScopeGenerator(),
}


def get_scope_generator(settings: Settings) -> ScopeGenerator:
    requested = settings.scope_generator
    generator = _GENERATORS.get(requested)
    if generator is None:
        logger.warning(
            "SCOPE_GENERATOR=%r is not implemented yet; falling back to 'placeholder'.",
            requested,
        )
        return _GENERATORS["placeholder"]
    return generator


def resolve_generator_name(settings: Settings) -> str:
    """The name actually used, for persisting onto the scope row."""
    return settings.scope_generator if settings.scope_generator in _GENERATORS else "placeholder"
