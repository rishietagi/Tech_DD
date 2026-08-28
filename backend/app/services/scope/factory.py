from app.core.config import Settings
from app.services.scope.base import ScopeGenerator
from app.services.scope.placeholder import PlaceholderScopeGenerator

_GENERATORS: dict[str, ScopeGenerator] = {
    "placeholder": PlaceholderScopeGenerator(),
}


def get_scope_generator(settings: Settings) -> ScopeGenerator:
    return _GENERATORS[settings.scope_generator]
