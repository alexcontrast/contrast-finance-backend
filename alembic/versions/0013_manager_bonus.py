"""add protected monthly manager bonuses

Revision ID: 0013_manager_bonus
Revises: 0012_invoice_tax_repair
Create Date: 2026-08-04
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0013_manager_bonus"
down_revision: Union[str, None] = "0012_invoice_tax_repair"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE monthly_expenses
        ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) NOT NULL DEFAULT 'manual'
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_expenses
        ADD COLUMN IF NOT EXISTS manager_id INTEGER REFERENCES users(id)
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_expenses
        ADD COLUMN IF NOT EXISTS bonus_income_amount NUMERIC(14, 2)
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_expenses
        ADD COLUMN IF NOT EXISTS bonus_percent NUMERIC(5, 2)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_monthly_expenses_manager_id
        ON monthly_expenses (manager_id)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_monthly_expenses_manager_bonus
        ON monthly_expenses (manager_id, month)
        WHERE source_type = 'manager_bonus'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_monthly_expenses_manager_bonus")
    op.execute("DROP INDEX IF EXISTS ix_monthly_expenses_manager_id")
    op.execute("ALTER TABLE monthly_expenses DROP COLUMN IF EXISTS bonus_percent")
    op.execute("ALTER TABLE monthly_expenses DROP COLUMN IF EXISTS bonus_income_amount")
    op.execute("ALTER TABLE monthly_expenses DROP COLUMN IF EXISTS manager_id")
    op.execute("ALTER TABLE monthly_expenses DROP COLUMN IF EXISTS source_type")
