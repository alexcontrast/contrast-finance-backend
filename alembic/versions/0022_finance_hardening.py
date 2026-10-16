"""Credential revocation, shared login limits and idempotent payment requests.

Revision ID: 0022_finance_hardening
Revises: 0021_avr_signed_ddc
"""
from alembic import op, context
import sqlalchemy as sa

revision = "0022_finance_hardening"
down_revision = "0021_avr_signed_ddc"
branch_labels = None
depends_on = None


def upgrade():
    duplicates = None if context.is_offline_mode() else op.get_bind().execute(sa.text("SELECT event_id, user_id FROM event_shares GROUP BY event_id,user_id HAVING COUNT(*) > 1 LIMIT 1")).first()
    if duplicates:
        raise RuntimeError(f"Preflight: duplicate event shares for event_id={duplicates[0]}, user_id={duplicates[1]}; review the existing financial allocation before upgrading")
    op.create_index("uq_event_shares_event_user", "event_shares", ["event_id", "user_id"], unique=True)
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.create_table("auth_attempts",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(), nullable=False))
    op.add_column("payment_requests", sa.Column("operation_key", sa.String(140), nullable=True))
    op.add_column("payment_requests", sa.Column("operation_hash", sa.String(64), nullable=True))
    op.create_index("uq_payment_operation_key", "payment_requests", ["operation_key"], unique=True)


def downgrade():
    op.drop_index("uq_event_shares_event_user", table_name="event_shares")
    op.drop_index("uq_payment_operation_key", table_name="payment_requests")
    op.drop_column("payment_requests", "operation_hash")
    op.drop_column("payment_requests", "operation_key")
    op.drop_table("auth_attempts")
    op.drop_column("users", "token_version")
