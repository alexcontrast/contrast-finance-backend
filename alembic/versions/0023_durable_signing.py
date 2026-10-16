"""Durable signature queue and shared worker leases.
Revision ID: 0023_durable_signing
Revises: 0022_finance_hardening
"""
from alembic import op
import sqlalchemy as sa
revision = "0023_durable_signing"
down_revision = "0022_finance_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("background_states", sa.Column("key", sa.String(120), primary_key=True),
        sa.Column("owner", sa.String(64), nullable=True), sa.Column("lease_until", sa.DateTime(), nullable=False),
        sa.Column("watermark", sa.DateTime(), nullable=True))
    op.create_table("pending_act_signatures", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("accounting_id", sa.Integer(), sa.ForeignKey("self_employed_accounting.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_sha256", sa.String(64), nullable=True),
        sa.Column("signature_sha256", sa.String(64), nullable=False), sa.Column("signature_data", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("accounting_id", "signature_sha256", name="uq_pending_act_signature"))
    op.create_index("ix_pending_act_signatures_accounting_id", "pending_act_signatures", ["accounting_id"])
    op.create_index("ix_pending_act_signatures_status", "pending_act_signatures", ["status"])
    # Existing pending bytes remain in the old protected slot and are recovered
    # normally. No original document/signature/history is deleted or rewritten.


def downgrade():
    op.drop_table("pending_act_signatures")
    op.drop_table("background_states")
