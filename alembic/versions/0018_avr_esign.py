"""add two-party SIGEX/eGov signing for R-1 acts

Revision ID: 0018_avr_esign
Revises: 0017_accounting_avr
Create Date: 2026-08-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0018_avr_esign"
down_revision: Union[str, None] = "0017_accounting_avr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("self_employed_accounting", sa.Column("contractor_phone", sa.String(length=32), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_sigex_document_id", sa.String(length=64), nullable=True))
    op.add_column("self_employed_accounting", sa.Column("act_sigex_registered_at", sa.DateTime(), nullable=True))
    op.create_index(
        "ix_self_employed_accounting_act_sigex_document_id",
        "self_employed_accounting",
        ["act_sigex_document_id"],
        unique=True,
    )

    op.create_table(
        "self_employed_act_signatures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accounting_id", sa.Integer(), nullable=False),
        sa.Column("signer_role", sa.String(length=16), nullable=False),
        sa.Column("expected_iin", sa.String(length=20), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("token", sa.String(length=96), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("session_started_at", sa.DateTime(), nullable=True),
        sa.Column("session_expires_at", sa.DateTime(), nullable=True),
        sa.Column("sigex_data_url", sa.Text(), nullable=True),
        sa.Column("sigex_sign_url", sa.Text(), nullable=True),
        sa.Column("egov_mobile_url", sa.Text(), nullable=True),
        sa.Column("egov_business_url", sa.Text(), nullable=True),
        sa.Column("qr_code", sa.Text(), nullable=True),
        sa.Column("signature_data", sa.LargeBinary(), nullable=True),
        sa.Column("signature_sha256", sa.String(length=64), nullable=True),
        sa.Column("sigex_sign_id", sa.Integer(), nullable=True),
        sa.Column("signer_iin", sa.String(length=20), nullable=True),
        sa.Column("signer_name", sa.String(length=255), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["accounting_id"],
            ["self_employed_accounting.id"],
            name="fk_act_signature_accounting_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("accounting_id", "signer_role", name="uq_act_signature_accounting_role"),
    )
    op.create_index("ix_self_employed_act_signatures_id", "self_employed_act_signatures", ["id"])
    op.create_index("ix_self_employed_act_signatures_accounting_id", "self_employed_act_signatures", ["accounting_id"])
    op.create_index("ix_self_employed_act_signatures_signer_role", "self_employed_act_signatures", ["signer_role"])
    op.create_index("ix_self_employed_act_signatures_status", "self_employed_act_signatures", ["status"])
    op.create_index("ix_self_employed_act_signatures_token", "self_employed_act_signatures", ["token"], unique=True)


def downgrade() -> None:
    op.drop_table("self_employed_act_signatures")
    op.drop_index("ix_self_employed_accounting_act_sigex_document_id", table_name="self_employed_accounting")
    op.drop_column("self_employed_accounting", "act_sigex_registered_at")
    op.drop_column("self_employed_accounting", "act_sigex_document_id")
    op.drop_column("self_employed_accounting", "contractor_phone")
