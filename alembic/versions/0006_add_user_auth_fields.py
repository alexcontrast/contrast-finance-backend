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


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table_name: str, column_name: str) -> bool:
    columns = [column["name"] for column in _inspector().get_columns(table_name)]
    return column_name in columns


def _has_index(table_name: str, index_name: str) -> bool:
    indexes = [index["name"] for index in _inspector().get_indexes(table_name)]
    return index_name in indexes


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

    if not _has_index("users", "ix_users_phone"):
        op.create_index("ix_users_phone", "users", ["phone"], unique=False)

    if not _has_index("users", "ix_users_legacy_user_id"):
        op.create_index("ix_users_legacy_user_id", "users", ["legacy_user_id"], unique=True)


def downgrade() -> None:
    if _has_index("users", "ix_users_legacy_user_id"):
        op.drop_index("ix_users_legacy_user_id", table_name="users")

    if _has_index("users", "ix_users_phone"):
        op.drop_index("ix_users_phone", table_name="users")

    for column_name in ["pin_hash", "auth_source", "legacy_pin_hash", "legacy_user_id", "phone"]:
        if _has_column("users", column_name):
            op.drop_column("users", column_name)
