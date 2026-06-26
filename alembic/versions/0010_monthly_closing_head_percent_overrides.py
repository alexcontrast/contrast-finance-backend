"""add monthly closing head percent overrides

Revision ID: 0010_monthly_closing_head_percent_overrides
Revises: 0009_event_customer_paid_amount
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_monthly_closing_head_percent_overrides"
down_revision: Union[str, None] = "0009_event_customer_paid_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "monthly_closings",
        sa.Column("sanzhar_head_percent_override", sa.Numeric(5, 2), nullable=True),
    )
    op.add_column(
        "monthly_closings",
        sa.Column("raufal_head_percent_override", sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("monthly_closings", "raufal_head_percent_override")
    op.drop_column("monthly_closings", "sanzhar_head_percent_override")
