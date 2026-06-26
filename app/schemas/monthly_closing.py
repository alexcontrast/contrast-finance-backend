from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MonthlyClosingHeadPercentUpdate(BaseModel):
    department: str
    percent: Decimal | None = None


class MonthlyClosingCalculateRead(BaseModel):
    month: date
    company_plan_amount: Decimal

    sanzhar_plan_amount: Decimal
    sanzhar_income_amount: Decimal
    sanzhar_expense_amount: Decimal
    sanzhar_completion_percent: Decimal
    sanzhar_head_percent: Decimal
    sanzhar_head_percent_override: Decimal | None = None
    sanzhar_head_salary: Decimal
    sanzhar_remaining_after_head: Decimal

    raufal_plan_amount: Decimal
    raufal_income_amount: Decimal
    raufal_expense_amount: Decimal
    raufal_completion_percent: Decimal
    raufal_head_percent: Decimal
    raufal_head_percent_override: Decimal | None = None
    raufal_head_salary: Decimal
    raufal_remaining_after_head: Decimal

    founders_total_amount: Decimal
    founder_one_amount: Decimal
    founder_two_amount: Decimal
    founder_three_amount: Decimal

    status: str


class MonthlyClosingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: date
    company_plan_amount: Decimal

    sanzhar_plan_amount: Decimal
    sanzhar_income_amount: Decimal
    sanzhar_expense_amount: Decimal
    sanzhar_completion_percent: Decimal
    sanzhar_head_percent: Decimal
    sanzhar_head_percent_override: Decimal | None = None
    sanzhar_head_salary: Decimal
    sanzhar_remaining_after_head: Decimal

    raufal_plan_amount: Decimal
    raufal_income_amount: Decimal
    raufal_expense_amount: Decimal
    raufal_completion_percent: Decimal
    raufal_head_percent: Decimal
    raufal_head_percent_override: Decimal | None = None
    raufal_head_salary: Decimal
    raufal_remaining_after_head: Decimal

    founders_total_amount: Decimal
    founder_one_amount: Decimal
    founder_two_amount: Decimal
    founder_three_amount: Decimal

    status: str
    closed_by_user_id: int | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
