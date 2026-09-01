"""The Initial Request List and the responses collected against it.

An IRL is the document a buyer sends the target at the start of diligence, listing every
artefact the team needs to inspect. It derives from the scope of work: the areas the
scope opened decide what evidence is worth asking for.

Versioned like `ScopeOfWork` — regenerating never destroys a prior list.

**Responses are a separate table on purpose.** They are user data with a different
lifecycle from the generated document: regenerating an IRL must never clobber answers
someone has already typed. Keeping them out of `payload_json` also avoids the
shallow-copy/`flag_modified` trap recorded in docs/PROJECT_LOG.md.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.engagement import Engagement


class InformationRequestList(TimestampMixin, Base):
    __tablename__ = "information_request_list"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    generator: Mapped[str] = mapped_column(String(40), nullable=False)
    # The scope version this list was derived from, so a reader can tell whether the IRL
    # is still aligned with the current scope or was built against an older one.
    source_scope_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="irls")
    responses: Mapped[list["IrlResponse"]] = relationship(
        back_populates="irl", cascade="all, delete-orphan"
    )


class IrlResponse(TimestampMixin, Base):
    """One answer against one question. Written by the analyst or the client."""

    __tablename__ = "irl_response"
    __table_args__ = (UniqueConstraint("irl_id", "question_id", name="uq_irl_response_question"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    irl_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("information_request_list.id", ondelete="CASCADE"), nullable=False
    )
    # The question's id within the payload, not a foreign key — the questions live in
    # `payload_json` rather than their own table.
    question_id: Mapped[str] = mapped_column(String(64), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    irl: Mapped["InformationRequestList"] = relationship(back_populates="responses")
