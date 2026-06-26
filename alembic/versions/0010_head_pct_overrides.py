"""add monthly closing head percent overrides

Revision ID: 0010_head_pct_overrides
Revises: 0009_event_customer_paid_amount
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_head_pct_overrides"
down_revision: Union[str, None] = "0009_event_customer_paid_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep this migration idempotent because an earlier build used a too-long
    # Alembic revision id and could fail after starting the upgrade.
    op.execute(
        """
        ALTER TABLE monthly_closings
        ADD COLUMN IF NOT EXISTS sanzhar_head_percent_override NUMERIC(5, 2)
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_closings
        ADD COLUMN IF NOT EXISTS raufal_head_percent_override NUMERIC(5, 2)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE monthly_closings
        DROP COLUMN IF EXISTS raufal_head_percent_override
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_closings
        DROP COLUMN IF EXISTS sanzhar_head_percent_override
        """
    )
