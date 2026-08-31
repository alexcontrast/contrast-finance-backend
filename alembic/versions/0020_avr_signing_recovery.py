"""persist incoming AVR signatures before SIGEX finalization

Revision ID: 0020_avr_signing_recovery
Revises: 0019_avr_shared_link
Create Date: 2026-08-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0020_avr_signing_recovery"
down_revision: Union[str, None] = "0019_avr_shared_link"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_pending_signature_data", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_pending_signature_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_pending_signature_received_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("self_employed_accounting", "act_pending_signature_received_at")
    op.drop_column("self_employed_accounting", "act_pending_signature_sha256")
    op.drop_column("self_employed_accounting", "act_pending_signature_data")
