"""store generated R-1 acts for self-employed accounting

Revision ID: 0017_accounting_avr
Revises: 0016_accounting_flow
Create Date: 2026-08-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0017_accounting_avr"
down_revision: Union[str, None] = "0016_accounting_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("self_employed_accounting", sa.Column("act_number", sa.String(length=64), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_date", sa.Date(), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_filename", sa.String(length=255), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_content_type", sa.String(length=120), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_size", sa.Integer(), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_sha256", sa.String(length=64), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_data", sa.LargeBinary(), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_generated_at", sa.DateTime(), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_generated_by_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_self_employed_accounting_act_generated_by_user_id",
        "self_employed_accounting",
        "users",
        ["act_generated_by_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_self_employed_accounting_act_sha256",
        "self_employed_accounting",
        ["act_sha256"],
    )


def downgrade() -> None:
    op.drop_index("ix_self_employed_accounting_act_sha256", table_name="self_employed_accounting")
    op.drop_constraint(
        "fk_self_employed_accounting_act_generated_by_user_id",
        "self_employed_accounting",
        type_="foreignkey",
    )
    op.drop_column("self_employed_accounting", "act_generated_by_user_id")
    op.drop_column("self_employed_accounting", "act_generated_at")
    op.drop_column("self_employed_accounting", "act_data")
    op.drop_column("self_employed_accounting", "act_sha256")
    op.drop_column("self_employed_accounting", "act_size")
    op.drop_column("self_employed_accounting", "act_content_type")
    op.drop_column("self_employed_accounting", "act_filename")
    op.drop_column("self_employed_accounting", "act_date")
    op.drop_column("self_employed_accounting", "act_number")
