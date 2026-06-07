"""add user auth fields

Revision ID: 0006_add_user_auth_fields
Revises: 0003_monthly_ops
Create Date: 2026-06-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0006_add_user_auth_fields"
down_revision: Union[str, None] = "0003_monthly_ops"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [column["name"] for column in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if not _has_column("users", "phone"):
        op.add_column("users", sa.Column("phone", sa.String(length=64), nullable=True))

    if not _has_column("users", "legacy_user_id"):
        op.add_column("users", sa.Column("legacy_user_id", sa.String(length=64), nullable=True))

    if not _has_column("users", "legacy_pin_hash"):
        op.add_column("users", sa.Column("legacy_pin_hash", sa.String(length=128), nullable=True))

    if not _has_column("users", "auth_source"):
        op.add_column(
            "users",
            sa.Column("auth_source", sa.String(length=32), nullable=False, server_default="legacy_apps_script"),
        )

    if not _has_column("users", "pin_hash"):
        op.add_column("users", sa.Column("pin_hash", sa.String(length=128), nullable=True))

    try:
        op.create_index("ix_users_phone", "users", ["phone"], unique=False)
    except Exception:
        pass

    try:
        op.create_index("ix_users_legacy_user_id", "users", ["legacy_user_id"], unique=True)
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index("ix_users_legacy_user_id", table_name="users")
    except Exception:
        pass

    try:
        op.drop_index("ix_users_phone", table_name="users")
    except Exception:
        pass

    for column_name in ["pin_hash", "auth_source", "legacy_pin_hash", "legacy_user_id", "phone"]:
        if _has_column("users", column_name):
            op.drop_column("users", column_name)
