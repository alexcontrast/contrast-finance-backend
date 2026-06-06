from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MonthlyPlanCreate(BaseModel):
    month: date
    company_plan_amount: Decimal
    sanzhar_share_percent: Decimal = Decimal("66.67")
    raufal_share_percent: Decimal = Decimal("33.33")
    manager_personal_plan_percent: Decimal = Decimal("12.50")


class MonthlyPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: date
    company_plan_amount: Decimal
    sanzhar_share_percent: Decimal
    raufal_share_percent: Decimal
    manager_personal_plan_percent: Decimal
    created_at: datetime
    updated_at: datetime


class DepartmentDashboardRead(BaseModel):
    month: date
    department_id: int | None
    department_name: str

    plan_amount: Decimal
    fact_income_amount: Decimal
    completion_percent: Decimal
    remaining_to_plan: Decimal

    events_count: int
    drafts_count: int
    expenses_amount: Decimal

    include_drafts: bool


class CompanyDashboardRead(BaseModel):
    month: date
    company_plan_amount: Decimal
    company_fact_income_amount: Decimal
    company_completion_percent: Decimal

    manager_personal_plan_amount: Decimal

    departments: list[DepartmentDashboardRead]
