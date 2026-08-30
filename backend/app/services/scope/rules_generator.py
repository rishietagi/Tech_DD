"""RulesScopeGenerator — the deterministic engine, end to end.

Produces a complete, publishable scope with no LLM involvement. Slots in behind the
Phase 1 `ScopeGenerator` protocol, so swapping it in is a config change.
"""

from app.schemas.intake import IntakeFull
from app.schemas.scope import ScopeOfWorkPayloadV2
from app.services.scope.composer import compose_scope
from app.services.scope.depth import calibrate_depth
from app.services.scope.scoring import classify
from app.services.scope.selection import select_rows
from app.services.scope.signals import extract_signals


class RulesScopeGenerator:
    """Intake -> signals -> classification -> selection -> depth -> document."""

    name = "rules"

    def generate(self, intake: IntakeFull) -> ScopeOfWorkPayloadV2:
        signals = extract_signals(intake)
        classification = classify(intake, signals)
        rows = select_rows(intake, classification, signals)
        rows, exclusions, diligence_risks = calibrate_depth(rows, intake, classification, signals)

        return compose_scope(
            intake=intake,
            classification=classification,
            rows=rows,
            signals=signals,
            exclusions=exclusions,
            diligence_risks=diligence_risks,
            generator=self.name,
        )
