"""The ScopeGenerator seam (CLAUDE.md §9).

`ScopeGenerator` is the only contract a generator has to honour, which is what let
Phase 2 swap the placeholder for a real engine without touching routes, schemas or UI.

Implementations:
  - PlaceholderScopeGenerator  Phase 1. Hard-coded v1 payload; retained so existing
                               scope rows still render.
  - RulesScopeGenerator        Phase 2. Deterministic KPMG deck, complete and
                               publishable with no LLM involved.
  - LlmScopeGenerator          Phase 2 step 8. Rewrites the prose inside a rules-built
                               document; never decides what the document contains.

Selected by the SCOPE_GENERATOR setting via `factory.get_scope_generator`.
"""

from typing import Protocol

from app.schemas.intake import IntakeFull
from app.schemas.scope import AnyScopePayload


class ScopeGenerator(Protocol):
    def generate(self, intake: IntakeFull) -> AnyScopePayload: ...
