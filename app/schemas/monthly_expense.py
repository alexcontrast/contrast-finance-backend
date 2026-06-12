from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MonthlyExpenseCreate(BaseModel):
    month: date
    title: str
    amount: Decimal

    # default_split / sanzhar_only / raufal_only / custom
    allocation_type: str = Field(default="default_split")

    # Used only for custom allocation.
    sanzhar_amount: Decimal | None = None
    raufal_amount: Decimal | None = None

    comment: str | None = None
    created_by_user_id: int | None = None


class MonthlyExpenseUpdate(BaseModel):
    amount: Decimal


class MonthlyExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: date
    title: str
    amount: Decimal
    allocation_type: str
    sanzhar_amount: Decimal
    raufal_amount: Decimal
    comment: str | None
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class MonthlyExpenseSummaryRead(BaseModel):
    month: date
    total_amount: Decimal
    sanzhar_amount: Decimal
    raufal_amount: Decimal
    expenses_count: int
