"""add event customer paid amount

Revision ID: 0009_event_customer_paid_amount
Revises: 0008_legacy_import_ids
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa


revision = "0009_event_customer_paid_amount"
down_revision = "0008_legacy_import_ids"
branch_labels = None
depends_on = None


def _has_column(bind, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "events", "customer_paid_amount"):
        op.add_column(
            "events",
            sa.Column(
                "customer_paid_amount",
                sa.Numeric(14, 2),
                nullable=False,
                server_default="0",
            ),
        )
        op.alter_column("events", "customer_paid_amount", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "events", "customer_paid_amount"):
        op.drop_column("events", "customer_paid_amount")
