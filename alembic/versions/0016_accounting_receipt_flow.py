"""receipt-first self-employed accounting flow

Revision ID: 0016_accounting_flow
Revises: 0015_self_employed_groups
Create Date: 2026-08-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016_accounting_flow"
down_revision: Union[str, None] = "0015_self_employed_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clean cut-over: everything that exists at migration time is historical and
    # must not suddenly flood the new Accounting workspace. New inserts default
    # to True after the migration completes.
    op.add_column(
        "payment_requests",
        sa.Column(
            "self_employed_accounting_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_payment_requests_self_employed_accounting_visible",
        "payment_requests",
        ["self_employed_accounting_visible"],
    )
    op.alter_column(
        "payment_requests",
        "self_employed_accounting_visible",
        server_default=sa.text("true"),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )

    # A receipt imported in bulk is allowed to exist before any payment request
    # is linked to it. Membership lives in self_employed_accounting_requests.
    op.alter_column(
        "self_employed_accounting",
        "payment_request_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    # Standalone imported receipts cannot be represented by the old schema.
    op.execute(
        sa.text(
            "DELETE FROM self_employed_accounting "
            "WHERE payment_request_id IS NULL"
        )
    )
    op.alter_column(
        "self_employed_accounting",
        "payment_request_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_index(
        "ix_payment_requests_self_employed_accounting_visible",
        table_name="payment_requests",
    )
    op.drop_column("payment_requests", "self_employed_accounting_visible")
