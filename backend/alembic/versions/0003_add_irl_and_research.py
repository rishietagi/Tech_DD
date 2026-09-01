"""add the IRL, its responses, and company research

Phase 3. Each new deliverable is its own versioned child table hanging off
`engagements`, exactly as `scope_of_work` already is — so adding a further module later
is one more table rather than a reshape of anything existing.

`irl_response` is separate from the IRL payload on purpose: responses are user data with
a different lifecycle from the generated document, and regenerating an IRL must never
clobber answers someone has already typed.

Revision ID: 0003_add_irl_and_research
Revises: 0002_drop_tech_is_product
Create Date: 2026-08-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_add_irl_and_research"
down_revision: Union[str, None] = "0002_drop_tech_is_product"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "information_request_list",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("engagement_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generator", sa.String(length=40), nullable=False),
        sa.Column("source_scope_version", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["engagements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_irl_engagement_version",
        "information_request_list",
        ["engagement_id", "version"],
    )

    op.create_table(
        "irl_response",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("irl_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["irl_id"], ["information_request_list.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("irl_id", "question_id", name="uq_irl_response_question"),
    )

    op.create_table(
        "company_research",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("engagement_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generator", sa.String(length=40), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["engagements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_engagement_version",
        "company_research",
        ["engagement_id", "version"],
    )


def downgrade() -> None:
    """Drops the three tables and everything in them. Irreversible by nature."""
    op.drop_index("ix_research_engagement_version", table_name="company_research")
    op.drop_table("company_research")
    op.drop_table("irl_response")
    op.drop_index("ix_irl_engagement_version", table_name="information_request_list")
    op.drop_table("information_request_list")
