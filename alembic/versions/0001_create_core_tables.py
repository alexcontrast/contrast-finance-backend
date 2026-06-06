"""create core tables

Revision ID: 0001_create_core_tables
Revises: 
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_create_core_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("telegram_id", sa.String(length=100), nullable=True),
        sa.Column("telegram_username", sa.String(length=150), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="manager"),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("pin_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("manager_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("client_calc_type", sa.String(length=50), nullable=False),
        sa.Column("manager_percent", sa.Numeric(5, 2), nullable=False, server_default="21.00"),
        sa.Column("agency_commission_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("agency_commission_spread_enabled", sa.String(length=10), nullable=False, server_default="false"),
        sa.Column("simplified_bank_tax_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_events_event_date", "events", ["event_date"])
    op.create_index("ix_events_department_id", "events", ["department_id"])
    op.create_index("ix_events_manager_id", "events", ["manager_id"])
    op.create_index("ix_events_status", "events", ["status"])

    op.create_table(
        "event_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("item_type", sa.String(length=50), nullable=False, server_default="regular"),

        sa.Column("external_name", sa.String(length=255), nullable=False),
        sa.Column("external_price", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("external_quantity", sa.Numeric(10, 2), nullable=False, server_default="1.00"),
        sa.Column("external_days", sa.Numeric(10, 2), nullable=False, server_default="1.00"),
        sa.Column("external_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("external_note", sa.Text(), nullable=True),

        sa.Column("amount_fact", sa.Numeric(14, 2), nullable=True),
        sa.Column("paid_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("payment_method", sa.String(length=50), nullable=True),

        sa.Column("iin_bin", sa.String(length=20), nullable=True),
        sa.Column("iin_bin_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tax_check_status", sa.String(length=50), nullable=True),

        sa.Column("vat_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("deduction_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),

        sa.Column("internal_note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_event_items_event_id", "event_items", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_event_items_event_id", table_name="event_items")
    op.drop_table("event_items")

    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_events_manager_id", table_name="events")
    op.drop_index("ix_events_department_id", table_name="events")
    op.drop_index("ix_events_event_date", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_index("ix_users_department_id", table_name="users")
    op.drop_table("users")

    op.drop_table("departments")
