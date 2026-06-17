from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ManagerDashboardEventRead(BaseModel):
    id: int
    client_name: str
    title: str
    event_date: date
    status: str
    money_status: str = "waiting_money"

    external_total: Decimal
    fact_total: Decimal
    paid_total: Decimal
    final_company_income: Decimal
    manager_salary: Decimal

    payment_requests_count: int
    active_payment_requests_count: int

    share_percent: Decimal = Decimal("100.00")
    is_coauthored: bool = False
    coauthor_name: str | None = None
    coauthor_user_id: int | None = None
    owner_manager_id: int | None = None
    owner_manager_name: str | None = None


class ManagerDashboardRead(BaseModel):
    month: date
    manager_id: int
    manager_name: str
    department_id: int | None = None
    department_name: str | None = None
    include_drafts: bool

    personal_plan_amount: Decimal
    fact_income_amount: Decimal
    completion_percent: Decimal
    remaining_to_plan: Decimal

    events_count: int
    drafts_count: int
    payment_requests_count: int
    active_payment_requests_count: int

    events: list[ManagerDashboardEventRead]


from app.schemas.event import EventRead
from app.schemas.event_item import EventItemRead
from app.schemas.event_summary import EventSummaryRead
from app.schemas.payment_request import PaymentRequestRead


class ManagerEventFullPayload(BaseModel):
    event: EventRead
    items: list[EventItemRead]
    summary: EventSummaryRead
    requests: list[PaymentRequestRead]


class ManagerDashboardBundleRead(BaseModel):
    dashboard: ManagerDashboardRead
    payment_requests: list[PaymentRequestRead]
    event_payloads: dict[int, ManagerEventFullPayload]
