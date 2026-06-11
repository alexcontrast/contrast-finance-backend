from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class AdminDepartmentDashboardRead(BaseModel):
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


class AdminEventRowRead(BaseModel):
    id: int
    client_name: str
    title: str
    event_date: date
    status: str
    money_status: str = "waiting_money"
    client_calc_type: str | None = None
    department_id: int
    department_name: str | None
    manager_id: int
    manager_name: str | None
    final_company_income: Decimal
    external_total: Decimal
    paid_total: Decimal
    manager_salary: Decimal = Decimal("0.00")
    payment_requests_count: int = 0
    active_payment_requests_count: int = 0
    items_count: int


class AdminPaymentRequestRowRead(BaseModel):
    id: int
    created_at: datetime | None = None
    event_id: int
    event_title: str | None
    client_name: str | None = None
    position: str | None
    amount_requested: Decimal
    payment_method: str
    status: str
    money_status: str = "waiting_money"
    tax_status: str | None
    warning_over_remaining: bool


class AdminClosingRead(BaseModel):
    is_closed: bool
    status: str | None = None
    sanzhar_head_salary: Decimal | None = None
    raufal_head_salary: Decimal | None = None
    sanzhar_remaining_after_head: Decimal | None = None
    raufal_remaining_after_head: Decimal | None = None
    founders_total_amount: Decimal | None = None
    founder_one_amount: Decimal | None = None
    founder_two_amount: Decimal | None = None
    founder_three_amount: Decimal | None = None


class AdminDashboardRead(BaseModel):
    month: date
    include_drafts: bool
    company_plan_amount: Decimal
    company_fact_income_amount: Decimal
    company_completion_percent: Decimal
    company_expenses_amount: Decimal
    manager_personal_plan_amount: Decimal
    departments: list[AdminDepartmentDashboardRead]
    events: list[AdminEventRowRead]
    payment_requests: list[AdminPaymentRequestRowRead]
    closing: AdminClosingRead
