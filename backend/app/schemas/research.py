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


class BriefSection(BaseModel):
    """One part of the business brief, with the sources behind it.

    Cited like a finding rather than written as free prose: a brief that cannot be traced
    back to a page is indistinguishable from the model's own general knowledge of the
    sector, which is exactly what the research prompt forbids.
    """

    model_config = {"extra": "ignore"}

    # 2-6 sentences. Empty where the sources did not support the section — the model is
    # told to omit rather than pad, and an absent section is a finding in itself.
    text: str = ""
    source_ids: list[str] = Field(default_factory=list)


class BusinessBrief(BaseModel):
    """A deal team's working understanding of the target's business.

    Added 2026-09-11 (Rishi): the original research returned a short summary and a flat
    list of findings, which answered "what is on the record" but not "what does this
    company actually do, for whom, in what market". A tech DD scope is a function of the
    business model — a distributor with 4,000 trade accounts and a SaaS vendor with 40
    enterprise customers need different diligence — so this is the section the scope and
    the IRL should be reading.

    Every section is optional. A thin public record produces a thin brief, and saying so
    is more useful than filling the gaps from general sector knowledge.
    """

    model_config = {"extra": "ignore"}

    # 2-3 paragraphs. The one section a partner would read on its own.
    executive_summary: BriefSection = Field(default_factory=BriefSection)
    # The operations: products, services, what physically or digitally happens.
    what_they_do: BriefSection = Field(default_factory=BriefSection)
    # The revenue model: how money is actually made, pricing, contract shape.
    how_they_make_money: BriefSection = Field(default_factory=BriefSection)
    # Segments, named customers, concentration, geography, channel.
    customers_and_markets: BriefSection = Field(default_factory=BriefSection)
    # The sector: size, growth, structure, cyclicality, regulation, disruption.
    sector_context: BriefSection = Field(default_factory=BriefSection)
    # Named competitors and where the target sits against them.
    competitive_position: BriefSection = Field(default_factory=BriefSection)
    # The bridge to the rest of the product: what this business model implies for the
    # technology diligence. The only section that is analysis rather than reportage, and
    # it is labelled as such in the UI.
    implications_for_diligence: BriefSection = Field(default_factory=BriefSection)

    @property
    def any_content(self) -> bool:
        return any(
            section.text.strip()
            for section in (
                self.executive_summary,
                self.what_they_do,
                self.how_they_make_money,
                self.customers_and_markets,
                self.sector_context,
                self.competitive_position,
                self.implications_for_diligence,
            )
        )


class ResearchPayload(BaseModel):
    """The stored research run."""

    schema_version: Literal[1] = 1
    generator: str
    prompt_version: str | None = None

    company_name: str | None = None
    summary: str
    # The deep business understanding. Optional so runs stored before 2026-09-11 still
    # load — an older payload simply has no brief, and the UI falls back to the summary.
    business_brief: BusinessBrief | None = None
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
