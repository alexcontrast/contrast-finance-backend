from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class DepartmentHeadManagerRead(BaseModel):
    id: int
    name: str
    role: str
    is_active: bool
    plan_amount: Decimal = Decimal("0.00")
    fact_income_amount: Decimal = Decimal("0.00")
    completion_percent: Decimal = Decimal("0.00")
    events_count: int = 0


class DepartmentHeadEventRead(BaseModel):
    id: int
    client_name: str
    title: str
    event_date: date
    status: str
    money_status: str = "waiting_money"
    client_calc_type: str | None = None
    department_id: int
    department_name: str | None = None
    manager_id: int
    manager_name: str | None
    final_company_income: Decimal
    department_income: Decimal = Decimal("0.00")
    department_share_percent: Decimal = Decimal("100.00")
    external_total: Decimal = Decimal("0.00")
    paid_total: Decimal
    manager_salary: Decimal = Decimal("0.00")
    payment_requests_count: int = 0
    active_payment_requests_count: int = 0
    items_count: int
    is_shared: bool = False


class DepartmentHeadPaymentRequestRead(BaseModel):
    id: int
    created_at: datetime | None = None
    event_id: int
    event_title: str | None
    client_name: str | None = None
    manager_name: str | None = None
    position: str | None
    amount_requested: Decimal
    payment_method: str
    status: str
    money_status: str = "waiting_money"
    tax_status: str | None
    card_number: str | None = None
    contractor_name_snapshot: str | None = None
    warning_over_remaining: bool


class DepartmentHeadExpenseRead(BaseModel):
    id: int
    month: date
    title: str
    total_amount: Decimal
    department_amount: Decimal
    allocation_type: str
    allocation_label: str
    comment: str | None = None
    created_at: datetime | None = None


class DepartmentHeadCalculationRead(BaseModel):
    status: str | None = "current"
    plan_amount: Decimal
    income_amount: Decimal
    expense_amount: Decimal
    completion_percent: Decimal
    head_percent: Decimal
    head_salary: Decimal
    remaining_after_head: Decimal


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
    payment_requests: list[DepartmentHeadPaymentRequestRead] = []
    expenses: list[DepartmentHeadExpenseRead] = []
    calculation: DepartmentHeadCalculationRead


from app.schemas.manager_dashboard import ManagerEventFullPayload


class DepartmentHeadDashboardBundleRead(BaseModel):
    dashboard: DepartmentHeadDashboardRead
    event_payloads: dict[int, ManagerEventFullPayload]
