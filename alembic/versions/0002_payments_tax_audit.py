"""create payments tax audit tables

Revision ID: 0002_payments_tax_audit
Revises: 0001_create_core_tables
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_payments_tax_audit"
down_revision: Union[str, None] = "0001_create_core_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contractors",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("iin_bin", sa.String(length=20), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("tax_status", sa.String(length=50), nullable=True),
        sa.Column("vat_status", sa.String(length=50), nullable=True),
        sa.Column("vat_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("deduction_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_contractors_iin_bin", "contractors", ["iin_bin"])
    op.create_index("ix_contractors_tax_status", "contractors", ["tax_status"])

    op.create_table(
        "taxpayer_checks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("contractor_id", sa.Integer(), sa.ForeignKey("contractors.id"), nullable=True),
        sa.Column("iin_bin", sa.String(length=20), nullable=False),
        sa.Column("name_result", sa.String(length=255), nullable=True),
        sa.Column("tax_status_result", sa.String(length=50), nullable=True),
        sa.Column("vat_status_result", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("raw_response_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("manual_set_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_taxpayer_checks_contractor_id", "taxpayer_checks", ["contractor_id"])
    op.create_index("ix_taxpayer_checks_iin_bin", "taxpayer_checks", ["iin_bin"])
    op.create_index("ix_taxpayer_checks_status", "taxpayer_checks", ["status"])

    op.create_table(
        "payment_requests",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("event_item_id", sa.Integer(), sa.ForeignKey("event_items.id"), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),

        sa.Column("amount_requested", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="new"),
        sa.Column("comment", sa.Text(), nullable=True),

        sa.Column("item_name_snapshot", sa.String(length=255), nullable=True),
        sa.Column("item_amount_plan_snapshot", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("item_amount_fact_snapshot", sa.Numeric(14, 2), nullable=True),
        sa.Column("item_paid_amount_snapshot", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("item_remaining_snapshot", sa.Numeric(14, 2), nullable=False, server_default="0.00"),

        sa.Column("contractor_id", sa.Integer(), sa.ForeignKey("contractors.id"), nullable=True),
        sa.Column("contractor_name_snapshot", sa.String(length=255), nullable=True),
        sa.Column("iin_bin_snapshot", sa.String(length=20), nullable=True),
        sa.Column("tax_status_snapshot", sa.String(length=50), nullable=True),
        sa.Column("vat_status_snapshot", sa.String(length=50), nullable=True),
        sa.Column("vat_amount_snapshot", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("deduction_amount_snapshot", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("tax_source_snapshot", sa.String(length=50), nullable=True),

        sa.Column("card_number", sa.String(length=30), nullable=True),

        sa.Column("manual_tax_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("manual_tax_set_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("manual_tax_set_at", sa.DateTime(), nullable=True),

        sa.Column("warning_over_remaining", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("cash_received_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_payment_requests_event_id", "payment_requests", ["event_id"])
    op.create_index("ix_payment_requests_event_item_id", "payment_requests", ["event_item_id"])
    op.create_index("ix_payment_requests_created_by_user_id", "payment_requests", ["created_by_user_id"])
    op.create_index("ix_payment_requests_status", "payment_requests", ["status"])
    op.create_index("ix_payment_requests_contractor_id", "payment_requests", ["contractor_id"])

    op.create_table(
        "event_shares",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("share_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_event_shares_event_id", "event_shares", ["event_id"])
    op.create_index("ix_event_shares_user_id", "event_shares", ["user_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_entity_type", "audit_log", ["entity_type"])
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_type", table_name="audit_log")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_event_shares_user_id", table_name="event_shares")
    op.drop_index("ix_event_shares_event_id", table_name="event_shares")
    op.drop_table("event_shares")

    op.drop_index("ix_payment_requests_contractor_id", table_name="payment_requests")
    op.drop_index("ix_payment_requests_status", table_name="payment_requests")
    op.drop_index("ix_payment_requests_created_by_user_id", table_name="payment_requests")
    op.drop_index("ix_payment_requests_event_item_id", table_name="payment_requests")
    op.drop_index("ix_payment_requests_event_id", table_name="payment_requests")
    op.drop_table("payment_requests")

    op.drop_index("ix_taxpayer_checks_status", table_name="taxpayer_checks")
    op.drop_index("ix_taxpayer_checks_iin_bin", table_name="taxpayer_checks")
    op.drop_index("ix_taxpayer_checks_contractor_id", table_name="taxpayer_checks")
    op.drop_table("taxpayer_checks")

    op.drop_index("ix_contractors_tax_status", table_name="contractors")
    op.drop_index("ix_contractors_iin_bin", table_name="contractors")
    op.drop_table("contractors")
