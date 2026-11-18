"""Add the estate assessment: inventories, answers, scores, gap edits and the IT budget.

docs/phases/PHASE6_PLAN.md §3. Five tables, all children of `engagements`:

* `inventory_item` — applications, data domains and platforms the target reported;
* `estate_answer` — the analyst's answers about each, and about the estate;
* `estate_assessment` — versioned scoring runs, one series per domain;
* `estate_gap_note` — consultant edits overlaid on generated gaps;
* `it_budget` — budget vs actual inputs and the budgeting-process answers.

Revision ID: 0008_add_estate_assessment
Revises: 0007_add_scan_findings
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_add_estate_assessment"
down_revision = "0007_add_scan_findings"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def _engagement_fk(unique: bool = False) -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(
        "engagement_id",
        sa.String(36),
        sa.ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        unique=unique,
    )


def upgrade() -> None:
    op.create_table(
        "inventory_item",
        sa.Column("id", sa.String(36), primary_key=True),
        _engagement_fk(),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("ref", sa.String(16), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("engagement_id", "kind", "ref", name="uq_inventory_item_ref"),
    )
    op.create_index("ix_inventory_item_engagement", "inventory_item", ["engagement_id", "kind"])

    op.create_table(
        "estate_answer",
        sa.Column("id", sa.String(36), primary_key=True),
        _engagement_fk(),
        sa.Column("domain", sa.String(20), nullable=False),
        sa.Column("subject_id", sa.String(36), nullable=False),
        sa.Column("question_id", sa.String(64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
        *_timestamps(),
        sa.UniqueConstraint("engagement_id", "domain", "subject_id", "question_id", name="uq_estate_answer"),
    )

    op.create_table(
        "estate_assessment",
        sa.Column("id", sa.String(36), primary_key=True),
        _engagement_fk(),
        sa.Column("domain", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generator", sa.String(40), nullable=False),
        sa.Column("index_value", sa.Float(), nullable=True),
        sa.Column("band", sa.String(20), nullable=True),
        sa.Column("gap_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_estate_assessment_engagement", "estate_assessment", ["engagement_id", "domain"])

    op.create_table(
        "estate_gap_note",
        sa.Column("id", sa.String(36), primary_key=True),
        _engagement_fk(),
        sa.Column("domain", sa.String(20), nullable=False),
        sa.Column("gap_key", sa.String(120), nullable=False),
        sa.Column("severity", sa.String(10), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("engagement_id", "domain", "gap_key", name="uq_estate_gap_note"),
    )

    op.create_table(
        "it_budget",
        sa.Column("id", sa.String(36), primary_key=True),
        _engagement_fk(unique=True),
        sa.Column("inputs_json", sa.JSON(), nullable=False),
        *_timestamps(),
    )


def downgrade() -> None:
    op.drop_table("it_budget")
    op.drop_table("estate_gap_note")
    op.drop_index("ix_estate_assessment_engagement", table_name="estate_assessment")
    op.drop_table("estate_assessment")
    op.drop_table("estate_answer")
    op.drop_index("ix_inventory_item_engagement", table_name="inventory_item")
    op.drop_table("inventory_item")
