"""Seed requests, derived deterministically from the scope of work.

Every KPMG scope row carries an `evidence` list — "Architecture diagrams and system
documentation", "Known technical debt register" — which reaches the stored payload as
`ScopedRow.evidence_requests`. Those lists are exactly what an IRL asks for, so they are
the deterministic seed: **every seeded question traces back to a scope area that a rule
opened**, and the IRL still produces something usable with the LLM switched off.

Rows at tier 0 are out of scope and are skipped. There is no point requesting evidence
for an area the engine deliberately did not open.
"""

from dataclasses import dataclass

from app.schemas.scope import ScopeOfWorkPayloadV2


@dataclass(frozen=True)
class SeedRequest:
    """One evidence line from one in-scope row, with its provenance attached."""

    id: str
    text: str
    row_id: str
    row_title: str
    tier: int
    # DD_master workstream codes for the row. Not shown to the client — they are the
    # internal audit layer — but they help the model group questions sensibly.
    workstreams: list[str]


def build_seeds(scope: ScopeOfWorkPayloadV2) -> list[SeedRequest]:
    """Flatten the in-scope rows' evidence lists into seed requests.

    Deterministic and order-stable: the same scope always yields the same seeds in the
    same order, which is what makes the golden-case style tests meaningful.
    """
    seeds: list[SeedRequest] = []

    for row in scope.rows:
        if row.tier <= 0:
            continue
        for index, evidence in enumerate(row.evidence_requests, start=1):
            text = evidence.strip()
            if not text:
                continue
            seeds.append(
                SeedRequest(
                    # Stable within a version and derived from the row, so a question's
                    # id survives a regeneration when the underlying scope is unchanged.
                    id=f"{row.id}-E{index}",
                    text=text,
                    row_id=row.id,
                    row_title=row.title,
                    tier=row.tier,
                    workstreams=list(row.workstreams),
                )
            )

    return seeds
