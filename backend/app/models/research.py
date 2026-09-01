"""AI-generated company research, grounded in live web sources.

Takes the target described in the intake and searches the web for what is publicly known
about it — incidents, filings, funding, press — so the diligence team starts from
evidence rather than a blank page, and so the IRL can name business functions that
actually match the target's shape.

Versioned like `ScopeOfWork`: a run is stored, not re-fetched on every page view. That
matters because each run costs an API call against a small free-tier quota.

Every payload carries its own disclaimer text. The research is model-generated from
sources of varying quality, and a stored run that is later re-read or exported must carry
that warning with it rather than relying on the page that happened to render it.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.engagement import Engagement


class CompanyResearch(TimestampMixin, Base):
    __tablename__ = "company_research"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    generator: Mapped[str] = mapped_column(String(40), nullable=False)
    # Denormalised so the listing can show what was researched without opening the JSON.
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="research_runs")
