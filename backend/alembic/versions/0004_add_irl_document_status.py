"""add per-request document status for the IRL checklist

Phase 4. Tracks whether the document behind each IRL request has actually arrived.

Separate from `irl_response`: a response is what the client wrote, a status is what the
deal team observes about the documents. The shared-drive scanner (built at deployment)
will write status without touching anything the client typed.

Rows exist only once a status is set — absence means `not_received` — so no backfill is
needed for the IRLs that already exist.

Revision ID: 0004_add_irl_document_status
Revises: 0003_add_irl_and_research
Create Date: 2026-08-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_add_irl_document_status"
down_revision: Union[str, None] = "0003_add_irl_and_research"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "irl_document_status",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("irl_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("document_type", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("matched_files", sa.JSON(), nullable=True),
        sa.Column("set_by_human", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["irl_id"], ["information_request_list.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("irl_id", "question_id", name="uq_irl_document_status_question"),
    )


def downgrade() -> None:
    """Drops the table and every status in it. Irreversible by nature."""
    op.drop_table("irl_document_status")
