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
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
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
    document_statuses: Mapped[list["IrlDocumentStatus"]] = relationship(
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


class IrlDocumentStatus(TimestampMixin, Base):
    """Whether the document behind one request has actually arrived.

    Separate from `IrlResponse` on purpose. A response is *what the client wrote*; a
    status is *what the deal team observes about the documents*. They move
    independently, and the shared-drive scanner will write status without touching
    anything the client typed.

    Rows exist only once a status is set. Absence means `not_received`, so a freshly
    generated IRL needs no backfill and this table grows only as things arrive.
    """

    __tablename__ = "irl_document_status"
    __table_args__ = (
        UniqueConstraint("irl_id", "question_id", name="uq_irl_document_status_question"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    irl_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("information_request_list.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # not_received | received_partially | received_completely
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="not_received")
    # What kind of artefact arrived — "Policy", "Report", "Register", "Diagram". Free
    # text: the useful vocabulary differs by deal and should not be a fixed enum.
    document_type: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Filenames the scanner matched. Empty until the shared-drive walk is built; kept
    # so a wrong auto-match is visible rather than silent.
    matched_files: Mapped[list[str] | None] = mapped_column(SAJSON, nullable=True)
    # True when a human last set this, so a later scan does not overwrite a judgement
    # someone made deliberately.
    set_by_human: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    irl: Mapped["InformationRequestList"] = relationship(back_populates="document_statuses")
