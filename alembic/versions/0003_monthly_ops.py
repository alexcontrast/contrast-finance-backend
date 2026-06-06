"""create monthly ops tables

Revision ID: 0003_monthly_ops
Revises: 0002_payments_tax_audit
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_monthly_ops"
down_revision: Union[str, None] = "0002_payments_tax_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monthly_plans",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("month", sa.Date(), nullable=False, unique=True),
        sa.Column("company_plan_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("sanzhar_share_percent", sa.Numeric(5, 2), nullable=False, server_default="66.67"),
        sa.Column("raufal_share_percent", sa.Numeric(5, 2), nullable=False, server_default="33.33"),
        sa.Column("manager_personal_plan_percent", sa.Numeric(5, 2), nullable=False, server_default="12.50"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_monthly_plans_month", "monthly_plans", ["month"])

    op.create_table(
        "monthly_expenses",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("allocation_type", sa.String(length=50), nullable=False, server_default="default_split"),
        sa.Column("sanzhar_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("raufal_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_monthly_expenses_month", "monthly_expenses", ["month"])
    op.create_index("ix_monthly_expenses_created_by_user_id", "monthly_expenses", ["created_by_user_id"])

    op.create_table(
        "monthly_closings",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("month", sa.Date(), nullable=False, unique=True),
        sa.Column("company_plan_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),

        sa.Column("sanzhar_plan_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("sanzhar_income_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("sanzhar_expense_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("sanzhar_completion_percent", sa.Numeric(7, 2), nullable=False, server_default="0.00"),
        sa.Column("sanzhar_head_percent", sa.Numeric(5, 2), nullable=False, server_default="10.00"),
        sa.Column("sanzhar_head_salary", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("sanzhar_remaining_after_head", sa.Numeric(14, 2), nullable=False, server_default="0.00"),

        sa.Column("raufal_plan_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("raufal_income_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("raufal_expense_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("raufal_completion_percent", sa.Numeric(7, 2), nullable=False, server_default="0.00"),
        sa.Column("raufal_head_percent", sa.Numeric(5, 2), nullable=False, server_default="10.00"),
        sa.Column("raufal_head_salary", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("raufal_remaining_after_head", sa.Numeric(14, 2), nullable=False, server_default="0.00"),

        sa.Column("founders_total_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("founder_one_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("founder_two_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("founder_three_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),

        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("closed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_monthly_closings_month", "monthly_closings", ["month"])
    op.create_index("ix_monthly_closings_status", "monthly_closings", ["status"])
    op.create_index("ix_monthly_closings_closed_by_user_id", "monthly_closings", ["closed_by_user_id"])

    op.create_table(
        "exports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("export_type", sa.String(length=100), nullable=False),
        sa.Column("period_month", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("google_sheet_url", sa.Text(), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_exports_export_type", "exports", ["export_type"])
    op.create_index("ix_exports_period_month", "exports", ["period_month"])
    op.create_index("ix_exports_status", "exports", ["status"])
    op.create_index("ix_exports_created_by_user_id", "exports", ["created_by_user_id"])

    op.create_table(
        "telegram_messages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("payment_request_id", sa.Integer(), sa.ForeignKey("payment_requests.id"), nullable=True),
        sa.Column("chat_id", sa.String(length=100), nullable=False),
        sa.Column("message_id", sa.String(length=100), nullable=False),
        sa.Column("message_type", sa.String(length=100), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_telegram_messages_payment_request_id", "telegram_messages", ["payment_request_id"])
    op.create_index("ix_telegram_messages_chat_id", "telegram_messages", ["chat_id"])
    op.create_index("ix_telegram_messages_message_id", "telegram_messages", ["message_id"])
    op.create_index("ix_telegram_messages_message_type", "telegram_messages", ["message_type"])
    op.create_index("ix_telegram_messages_recipient_user_id", "telegram_messages", ["recipient_user_id"])
    op.create_index("ix_telegram_messages_status", "telegram_messages", ["status"])


def downgrade() -> None:
    op.drop_index("ix_telegram_messages_status", table_name="telegram_messages")
    op.drop_index("ix_telegram_messages_recipient_user_id", table_name="telegram_messages")
    op.drop_index("ix_telegram_messages_message_type", table_name="telegram_messages")
    op.drop_index("ix_telegram_messages_message_id", table_name="telegram_messages")
    op.drop_index("ix_telegram_messages_chat_id", table_name="telegram_messages")
    op.drop_index("ix_telegram_messages_payment_request_id", table_name="telegram_messages")
    op.drop_table("telegram_messages")

    op.drop_index("ix_exports_created_by_user_id", table_name="exports")
    op.drop_index("ix_exports_status", table_name="exports")
    op.drop_index("ix_exports_period_month", table_name="exports")
    op.drop_index("ix_exports_export_type", table_name="exports")
    op.drop_table("exports")

    op.drop_index("ix_monthly_closings_closed_by_user_id", table_name="monthly_closings")
    op.drop_index("ix_monthly_closings_status", table_name="monthly_closings")
    op.drop_index("ix_monthly_closings_month", table_name="monthly_closings")
    op.drop_table("monthly_closings")

    op.drop_index("ix_monthly_expenses_created_by_user_id", table_name="monthly_expenses")
    op.drop_index("ix_monthly_expenses_month", table_name="monthly_expenses")
    op.drop_table("monthly_expenses")

    op.drop_index("ix_monthly_plans_month", table_name="monthly_plans")
    op.drop_table("monthly_plans")
