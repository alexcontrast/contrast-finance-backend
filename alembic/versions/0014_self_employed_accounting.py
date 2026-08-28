"""add self-employed accounting receipt workspace

Revision ID: 0014_self_employed_accounting
Revises: 0013_manager_bonus
Create Date: 2026-08-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014_self_employed_accounting"
down_revision: Union[str, None] = "0013_manager_bonus"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "self_employed_accounting",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "payment_request_id",
            sa.Integer(),
            sa.ForeignKey("payment_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("receipt_filename", sa.String(length=255), nullable=True),
        sa.Column("receipt_content_type", sa.String(length=120), nullable=True),
        sa.Column("receipt_size", sa.Integer(), nullable=True),
        sa.Column("receipt_sha256", sa.String(length=64), nullable=True),
        sa.Column("receipt_data", sa.LargeBinary(), nullable=True),
        sa.Column("receipt_uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("receipt_uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("contractor_full_name", sa.String(length=255), nullable=True),
        sa.Column("iin", sa.String(length=20), nullable=True),
        sa.Column("receipt_number", sa.String(length=80), nullable=True),
        sa.Column("receipt_datetime", sa.DateTime(), nullable=True),
        sa.Column("service_name", sa.Text(), nullable=True),
        sa.Column("receipt_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("qr_payload", sa.Text(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("parse_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("parse_status", sa.String(length=32), nullable=False, server_default="empty"),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("act_status", sa.String(length=32), nullable=False, server_default="not_created"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("payment_request_id", name="uq_self_employed_accounting_payment_request_id"),
    )
    op.create_index(
        "ix_self_employed_accounting_payment_request_id",
        "self_employed_accounting",
        ["payment_request_id"],
        unique=True,
    )
    op.create_index("ix_self_employed_accounting_iin", "self_employed_accounting", ["iin"])
    op.create_index(
        "ix_self_employed_accounting_receipt_sha256",
        "self_employed_accounting",
        ["receipt_sha256"],
    )
    op.create_index(
        "ix_self_employed_accounting_parse_status",
        "self_employed_accounting",
        ["parse_status"],
    )
    op.create_index(
        "ix_self_employed_accounting_act_status",
        "self_employed_accounting",
        ["act_status"],
    )


def downgrade() -> None:
    op.drop_table("self_employed_accounting")
