"""split money status from work/payment status

Revision ID: 0007_split_money_status
Revises: 0006_add_user_auth_fields
Create Date: 2026-06-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0007_split_money_status"
down_revision: Union[str, None] = "0006_add_user_auth_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table_name: str, column_name: str) -> bool:
    columns = [column["name"] for column in _inspector().get_columns(table_name)]
    return column_name in columns


def _has_index(table_name: str, index_name: str) -> bool:
    indexes = [index["name"] for index in _inspector().get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    if not _has_column("events", "money_status"):
        op.add_column(
            "events",
            sa.Column("money_status", sa.String(length=50), nullable=False, server_default="waiting_money"),
        )

    if not _has_index("events", "ix_events_money_status"):
        op.create_index("ix_events_money_status", "events", ["money_status"], unique=False)

    if not _has_column("payment_requests", "money_status"):
        op.add_column(
            "payment_requests",
            sa.Column("money_status", sa.String(length=50), nullable=False, server_default="waiting_money"),
        )

    if not _has_index("payment_requests", "ix_payment_requests_money_status"):
        op.create_index("ix_payment_requests_money_status", "payment_requests", ["money_status"], unique=False)

    # Legacy conversion:
    # old events.status='cash_received' becomes event money_status='cash_received'
    # while work status returns to accepted.
    op.execute("""
        UPDATE events
        SET money_status = 'cash_received',
            status = 'accepted'
        WHERE status = 'cash_received'
    """)

    # old payment_requests.status='cash_received' becomes money_status='cash_received'.
    # If paid_at exists, it was already paid before cash received.
    # If paid_at is empty, the old bulk action likely overwrote a new/to_pay request,
    # so we return it to new instead of falsely marking contractor paid.
    op.execute("""
        UPDATE payment_requests
        SET money_status = 'cash_received',
            status = CASE
                WHEN paid_at IS NOT NULL THEN 'paid'
                ELSE 'new'
            END
        WHERE status = 'cash_received'
    """)


def downgrade() -> None:
    if _has_index("payment_requests", "ix_payment_requests_money_status"):
        op.drop_index("ix_payment_requests_money_status", table_name="payment_requests")

    if _has_column("payment_requests", "money_status"):
        op.drop_column("payment_requests", "money_status")

    if _has_index("events", "ix_events_money_status"):
        op.drop_index("ix_events_money_status", table_name="events")

    if _has_column("events", "money_status"):
        op.drop_column("events", "money_status")
