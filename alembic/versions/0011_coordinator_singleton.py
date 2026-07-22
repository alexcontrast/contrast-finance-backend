"""deduplicate coordinator rows and enforce one active coordinator per event

Revision ID: 0011_coord_singleton
Revises: 0010_head_pct_overrides
Create Date: 2026-07-22
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0011_coord_singleton"
down_revision: Union[str, None] = "0010_head_pct_overrides"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No event-item writes may slip between cleanup and index creation.
    op.execute("LOCK TABLE event_items IN SHARE ROW EXCLUSIVE MODE")

    # Keep the most recently updated coordinator. If an old duplicate has
    # payment requests, preserve them by moving them to the retained row.
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                FIRST_VALUE(id) OVER (
                    PARTITION BY event_id
                    ORDER BY updated_at DESC NULLS LAST, id DESC
                ) AS keep_id,
                ROW_NUMBER() OVER (
                    PARTITION BY event_id
                    ORDER BY updated_at DESC NULLS LAST, id DESC
                ) AS row_number
            FROM event_items
            WHERE item_type = 'coordinator' AND is_deleted = FALSE
        )
        UPDATE payment_requests AS payment
        SET event_item_id = ranked.keep_id
        FROM ranked
        WHERE ranked.row_number > 1
          AND payment.event_item_id = ranked.id
        """
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY event_id
                    ORDER BY updated_at DESC NULLS LAST, id DESC
                ) AS row_number
            FROM event_items
            WHERE item_type = 'coordinator' AND is_deleted = FALSE
        )
        UPDATE event_items AS item
        SET is_deleted = TRUE,
            updated_at = CURRENT_TIMESTAMP
        FROM ranked
        WHERE ranked.row_number > 1
          AND item.id = ranked.id
        """
    )

    # Refresh the denormalized paid total after possible request reassignment.
    op.execute(
        """
        UPDATE event_items AS item
        SET paid_amount = COALESCE((
            SELECT SUM(payment.amount_requested)
            FROM payment_requests AS payment
            WHERE payment.event_item_id = item.id
              AND payment.status = 'paid'
        ), 0)
        WHERE item.item_type = 'coordinator'
          AND item.is_deleted = FALSE
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_event_items_one_active_coordinator
        ON event_items (event_id)
        WHERE item_type = 'coordinator' AND is_deleted = FALSE
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_event_items_one_active_coordinator")
