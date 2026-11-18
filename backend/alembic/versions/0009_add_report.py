"""Add the final report: versions, the edit overlay, uploaded diagrams.

docs/phases/PHASE7_PLAN.md Part D.

Revision ID: 0009_add_report
Revises: 0008_add_estate_assessment
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_add_report"
down_revision = "0008_add_estate_assessment"
branch_labels = None
depends_on = None


def _common() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "engagement_id",
            sa.String(36),
            sa.ForeignKey("engagements.id", ondelete="CASCADE"),
            nullable=False,
        ),
    ]


def _timestamps() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "report",
        *_common(),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generator", sa.String(40), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_report_engagement", "report", ["engagement_id"])
    op.create_table(
        "report_edit",
        *_common(),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("engagement_id", "key", name="uq_report_edit_key"),
    )
    op.create_table(
        "report_asset",
        *_common(),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False, server_default=""),
        sa.Column("mime", sa.String(60), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        *_timestamps(),
    )


def downgrade() -> None:
    op.drop_table("report_asset")
    op.drop_table("report_edit")
    op.drop_index("ix_report_engagement", table_name="report")
    op.drop_table("report")
