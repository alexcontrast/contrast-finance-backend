"""use one AVR signing link and keep reusable self-employed contacts

Revision ID: 0019_avr_shared_link
Revises: 0018_avr_esign
Create Date: 2026-08-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0019_avr_shared_link"
down_revision: Union[str, None] = "0018_avr_esign"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "self_employed_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("iin", sa.String(length=12), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("whatsapp_phone", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_self_employed_contacts_id", "self_employed_contacts", ["id"])
    op.create_index("ix_self_employed_contacts_iin", "self_employed_contacts", ["iin"], unique=True)

    for name, column in (
        ("act_signing_token", sa.String(length=96)),
        ("act_signing_token_expires_at", sa.DateTime()),
        ("act_session_status", sa.String(length=32)),
        ("act_session_started_at", sa.DateTime()),
        ("act_session_expires_at", sa.DateTime()),
        ("act_sigex_data_url", sa.Text()),
        ("act_sigex_sign_url", sa.Text()),
        ("act_egov_mobile_url", sa.Text()),
        ("act_egov_business_url", sa.Text()),
        ("act_qr_code", sa.Text()),
        ("act_signing_error", sa.Text()),
    ):
        op.add_column("self_employed_accounting", sa.Column(name, column, nullable=True))
    op.create_index(
        "ix_self_employed_accounting_act_signing_token",
        "self_employed_accounting",
        ["act_signing_token"],
        unique=True,
    )

    # Preserve every phone already entered in v0.5.91. DISTINCT ON selects the
    # most recently changed receipt for each IIN.
    op.execute(
        """
        INSERT INTO self_employed_contacts (iin, full_name, whatsapp_phone, created_at, updated_at)
        SELECT DISTINCT ON (regexp_replace(iin, '[^0-9]', '', 'g'))
               regexp_replace(iin, '[^0-9]', '', 'g'),
               contractor_full_name,
               contractor_phone,
               CURRENT_TIMESTAMP,
               CURRENT_TIMESTAMP
          FROM self_employed_accounting
         WHERE contractor_phone IS NOT NULL
           AND contractor_phone <> ''
           AND length(regexp_replace(iin, '[^0-9]', '', 'g')) = 12
         ORDER BY regexp_replace(iin, '[^0-9]', '', 'g'), updated_at DESC, id DESC
        """
    )


def downgrade() -> None:
    op.drop_index("ix_self_employed_accounting_act_signing_token", table_name="self_employed_accounting")
    for name in (
        "act_signing_error",
        "act_qr_code",
        "act_egov_business_url",
        "act_egov_mobile_url",
        "act_sigex_sign_url",
        "act_sigex_data_url",
        "act_session_expires_at",
        "act_session_started_at",
        "act_session_status",
        "act_signing_token_expires_at",
        "act_signing_token",
    ):
        op.drop_column("self_employed_accounting", name)
    op.drop_table("self_employed_contacts")
