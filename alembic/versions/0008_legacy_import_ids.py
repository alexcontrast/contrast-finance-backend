"""add legacy import identifiers

Revision ID: 0008_legacy_import_ids
Revises: 0007_split_money_status
Create Date: 2026-06-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0008_legacy_import_ids"
down_revision: Union[str, None] = "0007_split_money_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in [column["name"] for column in _inspector().get_columns(table_name)]


def _has_index(table_name: str, index_name: str) -> bool:
    return index_name in [index["name"] for index in _inspector().get_indexes(table_name)]


def upgrade() -> None:
    if not _has_column("events", "legacy_event_id"):
        op.add_column("events", sa.Column("legacy_event_id", sa.String(length=80), nullable=True))
    if not _has_index("events", "ix_events_legacy_event_id"):
        op.create_index("ix_events_legacy_event_id", "events", ["legacy_event_id"], unique=True)

    if not _has_column("event_items", "legacy_item_key"):
        op.add_column("event_items", sa.Column("legacy_item_key", sa.String(length=160), nullable=True))
    if not _has_index("event_items", "ix_event_items_legacy_item_key"):
        op.create_index("ix_event_items_legacy_item_key", "event_items", ["legacy_item_key"], unique=True)

    if not _has_column("payment_requests", "legacy_payment_id"):
        op.add_column("payment_requests", sa.Column("legacy_payment_id", sa.String(length=80), nullable=True))
    if not _has_index("payment_requests", "ix_payment_requests_legacy_payment_id"):
        op.create_index("ix_payment_requests_legacy_payment_id", "payment_requests", ["legacy_payment_id"], unique=True)


def downgrade() -> None:
    if _has_index("payment_requests", "ix_payment_requests_legacy_payment_id"):
        op.drop_index("ix_payment_requests_legacy_payment_id", table_name="payment_requests")
    if _has_column("payment_requests", "legacy_payment_id"):
        op.drop_column("payment_requests", "legacy_payment_id")

    if _has_index("event_items", "ix_event_items_legacy_item_key"):
        op.drop_index("ix_event_items_legacy_item_key", table_name="event_items")
    if _has_column("event_items", "legacy_item_key"):
        op.drop_column("event_items", "legacy_item_key")

    if _has_index("events", "ix_events_legacy_event_id"):
        op.drop_index("ix_events_legacy_event_id", table_name="events")
    if _has_column("events", "legacy_event_id"):
        op.drop_column("events", "legacy_event_id")
