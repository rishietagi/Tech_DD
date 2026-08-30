"""ModuleSelector — decides which KPMG rows are in scope, at what base tier.

Selection order is fixed (PHASE2_SCOPE_ENGINE §6):
  1. Floor      — M1's core coverage is never dropped (G3)
  2. Mandatory  — M2-M7 force rows in at a minimum tier
  3. Affinity   — remaining rows open based on the archetype
  4. Objectives — the user's stated dd_objectives beat inferred priorities
Depth calibration (caps, floors, trade-offs) happens afterwards, in depth.py.
"""

from app.schemas.classification import Classification, DdType
from app.schemas.intake import IntakeFull
from app.schemas.kpmg_library import ScopeLibrary, ScopeRow
from app.schemas.selection import SelectedRow
from app.schemas.signals import Signal
from app.services.scope.library import get_scope_library

# Which decks a given archetype emits. A blended engagement gets both, per
# DD_master §3.4 — the archetypes are a weighting, never a menu.
_DECKS_FOR = {
    DdType.product: ["product"],
    DdType.enterprise: ["enterprise"],
    DdType.blended: ["product", "enterprise"],
}

# Maps a user's stated dd_objective onto the workstreams that answer it, so a stated
# priority can lift the rows that serve it (DD_master §8.1: explicit user priorities
# beat inferred ones).
_OBJECTIVE_WORKSTREAMS = {
    "Validate scalability": {"W-INFRA", "W-PROD", "W-APP"},
    "Quantify tech debt": {"W-APP", "W-PROD"},
    "Assess security & compliance": {"W-SEC", "W-PROC", "W-DATA"},
    "Size IT cost & run-rate": {"W-SPEND", "W-VEN"},
    "Assess team & key-person risk": {"W-OPS"},
    "Test product roadmap credibility": {"W-STRAT", "W-PROD"},
    "Assess integration or separation effort": {"W-INT", "W-SEP", "W-APP"},
    "Evaluate AI capability": {"W-APP", "W-PROD"},
    "Confirm IP ownership": {"W-VEN", "W-PROD"},
}


def _forced_workstream_tiers(signals: list[Signal]) -> dict[str, int]:
    """Minimum tier per workstream, from the mandatory rules that fired."""
    minimums: dict[str, int] = {}
    for signal in signals:
        if signal.is_unknown:
            continue
        detail = signal.detail
        min_tier = detail.get("min_tier")
        for workstream in detail.get("workstreams", []):
            if min_tier is not None:
                minimums[workstream] = max(minimums.get(workstream, 0), int(min_tier))
        forced = detail.get("force_workstream")
        if forced and forced.get("id"):
            tier = int(forced.get("min_tier", 1))
            minimums[forced["id"]] = max(minimums.get(forced["id"], 0), tier)
    return minimums


def _triggering_rules(row: ScopeRow, signals: list[Signal]) -> list[str]:
    """Which fired rules justify this row being in scope."""
    fired = {s.code for s in signals if not s.is_unknown}
    codes = [code for code in row.triggers if code in fired]

    # A row is also justified when a mandatory rule forced one of its workstreams.
    for signal in signals:
        if signal.is_unknown or signal.code in codes:
            continue
        forced = set(signal.detail.get("workstreams", []))
        forced_one = signal.detail.get("force_workstream") or {}
        if forced_one.get("id"):
            forced.add(forced_one["id"])
        if forced & set(row.workstreams):
            codes.append(signal.code)

    return sorted(set(codes))


def _objective_boost(row: ScopeRow, intake: IntakeFull) -> str | None:
    """+1 tier when the user explicitly asked for what this row primarily covers.

    The match is on the row's PRIMARY workstream (its first), not any workstream it
    touches. A broad objective like "Validate scalability" maps to W-INFRA/W-PROD/W-APP
    and would otherwise lift nearly every row in the deck, which makes the boost
    meaningless — everything deep is the same as nothing deep.
    """
    stated = intake.objectives.dd_objectives or []
    if not row.workstreams:
        return None
    primary = row.workstreams[0]
    for objective in stated:
        if primary in _OBJECTIVE_WORKSTREAMS.get(objective, set()):
            return objective
    return None


def select_rows(
    intake: IntakeFull,
    classification: Classification,
    signals: list[Signal],
    library: ScopeLibrary | None = None,
) -> list[SelectedRow]:
    """Every KPMG row in scope, with its base tier and audit trail."""
    library = library or get_scope_library()
    forced_tiers = _forced_workstream_tiers(signals)
    selected: list[SelectedRow] = []

    for deck_id in _DECKS_FOR[classification.dd_type]:
        deck = library.deck(deck_id)

        for row in deck.rows:
            triggered_by = _triggering_rules(row, signals)

            # 1. Floor + 2. Mandatory: always-in-scope rows, and any row whose
            #    workstream a mandatory rule forced open.
            mandated_tier = max(
                (forced_tiers.get(ws, 0) for ws in row.workstreams),
                default=0,
            )
            is_mandated = row.always_in_scope or mandated_tier > 0

            # 3. Affinity: a non-mandated row still opens if a rule triggered it.
            if not is_mandated and not triggered_by:
                continue

            tier = max(row.base_tier, mandated_tier)
            reasons: list[str] = []
            adjustments: list[str] = []

            if row.always_in_scope:
                reasons.append("core coverage")
            if mandated_tier > row.base_tier:
                adjustments.append(f"raised to Tier {mandated_tier} by a mandatory rule")
            if mandated_tier:
                reasons.append(f"mandatory at Tier {mandated_tier}")

            # 4. Objective boost — the user's stated priorities win over inferred ones.
            boosted_by = _objective_boost(row, intake)
            if boosted_by and tier < 3:
                tier += 1
                adjustments.append(f'+1 tier: you asked to "{boosted_by}"')

            selected.append(
                SelectedRow(
                    row=row,
                    deck=deck_id,
                    tier=tier,
                    tier_reason="; ".join(reasons) or "in scope for this archetype",
                    triggered_by=triggered_by,
                    adjustments=adjustments,
                )
            )

    return selected
