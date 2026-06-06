from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DepartmentHeadManagerRead(BaseModel):
    id: int
    name: str
    role: str
    is_active: bool


class DepartmentHeadEventRead(BaseModel):
    id: int
    client_name: str
    title: str
    event_date: date
    status: str
    manager_id: int
    manager_name: str | None
    final_company_income: Decimal
    items_count: int
    paid_total: Decimal


class DepartmentHeadClosingRead(BaseModel):
    is_closed: bool
    status: str | None = None

    plan_amount: Decimal | None = None
    income_amount: Decimal | None = None
    expense_amount: Decimal | None = None
    completion_percent: Decimal | None = None
    head_percent: Decimal | None = None
    head_salary: Decimal | None = None
    remaining_after_head: Decimal | None = None


class DepartmentHeadDashboardRead(BaseModel):
    month: date
    department_id: int
    department_name: str

    plan_amount: Decimal
    fact_income_amount: Decimal
    completion_percent: Decimal
    remaining_to_plan: Decimal
    expenses_amount: Decimal

    events_count: int
    drafts_count: int
    managers_count: int
    include_drafts: bool

    managers: list[DepartmentHeadManagerRead]
    events: list[DepartmentHeadEventRead]
    closing: DepartmentHeadClosingRead | None
