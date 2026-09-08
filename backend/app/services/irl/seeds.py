"""Seed requests, derived deterministically from the scope of work.

An Initial Request List asks for **two different things**, and until 2026-09-02 this
engine only produced one of them:

* **Document requests** — "provide the application architecture diagram". Every KPMG scope
  row carries an `evidence` list, which reaches the payload as `ScopedRow.evidence_requests`.
* **Questions** — "how does the company support system availability monitoring?".
  `DD_master.md` §6 gives every workstream *"areas of investigation (sourced questions
  where available)"* alongside its evidence requests. Those questions were being discarded.

Both are seeded here, and each seed carries its `kind` so the rest of the chain can treat
them differently: only a document can be "received", and only a question can be "answered".

**Why questions belong in the request list** rather than being saved for the interview —
the source is explicit, and the reasoning is about the target's patience, not convenience:

    "prioritise questions because time with management is limited; avoid repeating
     questions across sessions"                                    [DD_master p. 84-85]
    "do not go back repeatedly - the seller can become overwhelmed and even ultimately
     unresponsive"                                                    [DD_master p. 83]

A question left out of the list costs a follow-up round the source warns against spending.

Rows at tier 0 are out of scope and are skipped entirely. There is no point requesting
evidence, or asking questions, about an area the engine deliberately did not open.
"""

from dataclasses import dataclass
from typing import Literal

from app.schemas.scope import ScopeOfWorkPayloadV2
from app.services.irl.investigation import questions_for

SeedKind = Literal["document", "question"]


@dataclass(frozen=True)
class SeedRequest:
    """One request derived from one in-scope row, with its provenance attached."""

    id: str
    text: str
    row_id: str
    row_title: str
    tier: int
    # DD_master workstream codes for the row. Not shown to the client — they are the
    # internal audit layer — but they help the model group requests sensibly.
    workstreams: list[str]

    # What is being asked for. A document request wants an artefact; a question wants an
    # explanation. They are chased differently and answered differently, and only a
    # document can meaningfully be "received".
    kind: SeedKind = "document"
    # For questions: the page the wording came from, so a request traces to the source
    # exactly as a scope row's rule does. Empty for evidence-derived documents, whose
    # provenance is the scope row itself.
    citation: str = ""
    source_workstream: str = ""


def build_seeds(scope: ScopeOfWorkPayloadV2) -> list[SeedRequest]:
    """Flatten in-scope rows into document and question seeds.

    Deterministic and order-stable: the same scope always yields the same seeds in the
    same order, which is what makes the golden-case style tests meaningful.

    Documents come first within a row, then questions. That ordering is deliberate — the
    document request is usually the thing that answers the question, so a client reading
    down a scope area is asked for the artefact before being asked to explain it.
    """
    seeds: list[SeedRequest] = []
    # A question belongs to its workstream, and several scope rows can carry the same
    # workstream — three rows share W-APP on a typical enterprise deck. Asking its
    # questions once per row would put the same question to management three times, which
    # is precisely the failure DD_master p. 84-85 warns against ("avoid repeating
    # questions across sessions"). Each question is therefore asked once, on the first
    # in-scope row that carries its workstream: rows are already ordered by the deck's own
    # sequence, so the first is the most natural home for it.
    asked: set[str] = set()

    for row in scope.rows:
        if row.tier <= 0:
            continue

        for index, evidence in enumerate(row.evidence_requests, start=1):
            text = evidence.strip()
            if not text:
                continue
            seeds.append(
                SeedRequest(
                    # Stable within a version and derived from the row, so a request's id
                    # survives a regeneration when the underlying scope is unchanged.
                    id=f"{row.id}-E{index}",
                    text=text,
                    row_id=row.id,
                    row_title=row.title,
                    tier=row.tier,
                    workstreams=list(row.workstreams),
                    kind="document",
                )
            )

        # Questions the book attaches to this row's workstreams, skipping any already
        # asked on an earlier row.
        index = 0
        for code, question, citation in questions_for(list(row.workstreams)):
            key = question.strip().lower()
            if key in asked:
                continue
            asked.add(key)
            index += 1
            seeds.append(
                SeedRequest(
                    id=f"{row.id}-Q{index}",
                    text=question,
                    row_id=row.id,
                    row_title=row.title,
                    tier=row.tier,
                    workstreams=list(row.workstreams),
                    kind="question",
                    citation=citation,
                    source_workstream=code,
                )
            )

    return seeds
