"""The Phase-2 seam (CLAUDE.md §9, initial_plan.md §10).

`ScopeGenerator` is the only contract Phase 2 needs to honor. Phase 1 ships exactly
one implementation — `PlaceholderScopeGenerator` — selected via the
`SCOPE_GENERATOR` setting. Phase 2 adds `RulesScopeGenerator` and
`LlmScopeGenerator` beside it and flips the setting; no route, schema or UI changes.

TODO(phase-2): implement signal extraction, Enterprise/Product mix scoring, and
workstream selection from a versioned module library behind this same protocol.
Do not add that logic here or anywhere in Phase 1.
"""

from typing import Protocol

from app.schemas.intake import IntakeFull
from app.schemas.scope import ScopeOfWorkPayload


class ScopeGenerator(Protocol):
    def generate(self, intake: IntakeFull) -> ScopeOfWorkPayload: ...
