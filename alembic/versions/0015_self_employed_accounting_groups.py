"""allow one self-employed receipt to cover several payment requests

Revision ID: 0015_self_employed_groups
Revises: 0014_self_employed_accounting
Create Date: 2026-08-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic creates alembic_version.version_num as VARCHAR(32) by default.
# Keep revision identifiers within that limit so PostgreSQL can record the
# completed migration after the transactional DDL has run.
revision: str = "0015_self_employed_groups"
down_revision: Union[str, None] = "0014_self_employed_accounting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "self_employed_accounting_requests",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "accounting_id",
            sa.Integer(),
            sa.ForeignKey("self_employed_accounting.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payment_request_id",
            sa.Integer(),
            sa.ForeignKey("payment_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint(
            "payment_request_id",
            name="uq_self_employed_accounting_requests_payment_request_id",
        ),
    )
    op.create_index(
        "ix_self_employed_accounting_requests_accounting_id",
        "self_employed_accounting_requests",
        ["accounting_id"],
    )
    op.create_index(
        "ix_self_employed_accounting_requests_payment_request_id",
        "self_employed_accounting_requests",
        ["payment_request_id"],
        unique=True,
    )

    # Every pre-0015 accounting row represented exactly one request. Seed that
    # relation into the new membership table without touching receipts/data.
    op.execute(
        sa.text(
            """
            INSERT INTO self_employed_accounting_requests (accounting_id, payment_request_id, created_at)
            SELECT id, payment_request_id, COALESCE(created_at, CURRENT_TIMESTAMP)
            FROM self_employed_accounting
            """
        )
    )


def downgrade() -> None:
    op.drop_table("self_employed_accounting_requests")
