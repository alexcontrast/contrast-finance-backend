"""store the permanent SIGEX DDC for fully signed AVR documents

Revision ID: 0021_avr_signed_ddc
Revises: 0020_avr_signing_recovery
Create Date: 2026-08-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0021_avr_signed_ddc"
down_revision: Union[str, None] = "0020_avr_signing_recovery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_filename", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_size", sa.Integer(), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_data", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_generated_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_last_attempt_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "self_employed_accounting",
        sa.Column("act_ddc_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_self_employed_accounting_act_ddc_status",
        "self_employed_accounting",
        ["act_ddc_status"],
    )
    op.create_index(
        "ix_self_employed_accounting_act_ddc_sha256",
        "self_employed_accounting",
        ["act_ddc_sha256"],
    )


def downgrade() -> None:
    op.drop_index("ix_self_employed_accounting_act_ddc_sha256", table_name="self_employed_accounting")
    op.drop_index("ix_self_employed_accounting_act_ddc_status", table_name="self_employed_accounting")
    op.drop_column("self_employed_accounting", "act_ddc_error")
    op.drop_column("self_employed_accounting", "act_ddc_last_attempt_at")
    op.drop_column("self_employed_accounting", "act_ddc_generated_at")
    op.drop_column("self_employed_accounting", "act_ddc_data")
    op.drop_column("self_employed_accounting", "act_ddc_sha256")
    op.drop_column("self_employed_accounting", "act_ddc_size")
    op.drop_column("self_employed_accounting", "act_ddc_filename")
    op.drop_column("self_employed_accounting", "act_ddc_status")
