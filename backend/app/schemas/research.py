"""Company research payloads.

AI-generated, grounded in live web search. The shape exists to keep three things
inseparable: a claim, the source it came from, and the warning that neither has been
verified by a human.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# Shown above the research everywhere it appears, and stored on every payload so a run
# that is re-read or exported later still carries it. Deliberately blunt: this content
# can reach a client deliverable, and the failure mode of AI research is confident,
# well-formatted, plausible wrongness.
RESEARCH_DISCLAIMER = (
    "AI-generated research — verify before relying on it. This summary was produced by "
    "an AI model from public web sources at the time shown. It may be incomplete, out of "
    "date, or wrong, and it may attribute claims to sources inaccurately. Nothing here "
    "is verified fact, financial advice, or a substitute for professional due diligence. "
    "Check every material point against the linked source before acting on it or "
    "including it in a client deliverable."
)


class ResearchSource(BaseModel):
    """One web source the model actually consulted, from the grounding metadata."""

    id: str
    title: str
    url: str
    publisher: str | None = None


class ResearchFinding(BaseModel):
    """One point about the target, tied to the sources that support it."""

    topic: str
    detail: str
    # Categorised so the UI can group, and so the IRL prompt can weight what matters.
    category: Literal[
        "overview",
        "financial",
        "technology",
        "incident",
        "regulatory",
        "market",
        "people",
        "other",
    ] = "other"
    source_ids: list[str] = Field(default_factory=list)


class ResearchPayload(BaseModel):
    """The stored research run."""

    schema_version: Literal[1] = 1
    generator: str
    prompt_version: str | None = None

    company_name: str | None = None
    summary: str
    findings: list[ResearchFinding] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)

    # Stored, not rendered from a constant at display time — see the module docstring.
    disclaimer: str = RESEARCH_DISCLAIMER
    researched_at: datetime


class ResearchRead(BaseModel):
    id: str
    engagement_id: str
    version: int
    generator: str
    company_name: str | None = None
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchVersionSummary(BaseModel):
    version: int
    generator: str
    created_at: datetime

    model_config = {"from_attributes": True}
