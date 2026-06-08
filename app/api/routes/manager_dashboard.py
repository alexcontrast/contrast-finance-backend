from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.monthly_plan import MonthlyPlan
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.manager_dashboard import ManagerDashboardEventRead, ManagerDashboardRead
from app.services.auth import get_current_user
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["manager_dashboard"])


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def parse_month(month: str) -> date:
    try:
        parts = [int(part) for part in month.split("-")]
        return date(parts[0], parts[1], 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM or YYYY-MM-DD") from exc


def completion_percent(fact: Decimal, plan: Decimal) -> Decimal:
    if plan <= 0:
        return Decimal("0.00")
    return q(fact * Decimal("100") / plan)


def manager_personal_plan_amount(plan: MonthlyPlan) -> Decimal:
    return q(money(plan.company_plan_amount) * money(plan.manager_personal_plan_percent) / Decimal("100"))


def resolve_manager(
    db: Session,
    current_user: User,
    manager_id: int | None,
) -> User:
    if current_user.role == "manager":
        return current_user

    if current_user.role == "admin":
        if manager_id is None:
            raise HTTPException(status_code=400, detail="admin must pass manager_id")
        manager = db.get(User, manager_id)
        if manager is None:
            raise HTTPException(status_code=404, detail="Manager not found")
        return manager

    if current_user.role == "department_head":
        if manager_id is None:
            raise HTTPException(status_code=400, detail="department_head must pass manager_id")

        manager = db.get(User, manager_id)
        if manager is None:
            raise HTTPException(status_code=404, detail="Manager not found")

        if manager.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Department head can view only own department managers")

        return manager

    raise HTTPException(status_code=403, detail="Not enough permissions")


@router.get("/manager-dashboard", response_model=ManagerDashboardRead)
def get_manager_dashboard(
    month: str,
    include_drafts: bool = True,
    manager_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    month_date = parse_month(month)
    manager = resolve_manager(db, current_user, manager_id)

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Monthly plan not found")

    department = db.get(Department, manager.department_id) if manager.department_id else None

    query = select(Event).where(
        Event.manager_id == manager.id,
        extract("year", Event.event_date) == month_date.year,
        extract("month", Event.event_date) == month_date.month,
        Event.status != "cancelled",
    )

    if not include_drafts:
        query = query.where(Event.status != "draft")

    events = db.execute(query.order_by(Event.event_date, Event.id)).scalars().all()

    event_rows: list[ManagerDashboardEventRead] = []
    fact_income = Decimal("0.00")
    drafts_count = 0
    payment_requests_total = 0
    active_payment_requests_total = 0

    for event in events:
        if event.status == "draft":
            drafts_count += 1

        items = db.execute(
            select(EventItem)
            .where(EventItem.event_id == event.id, EventItem.is_deleted == False)  # noqa: E712
            .order_by(EventItem.sort_order, EventItem.id)
        ).scalars().all()

        summary = calculate_event_summary_values(event, items)
        final_income = money(summary["final_company_income"])
        fact_income += final_income

        payment_requests = db.execute(
            select(PaymentRequest).where(PaymentRequest.event_id == event.id)
        ).scalars().all()

        requests_count = len(payment_requests)
        active_requests_count = len([
            request for request in payment_requests
            if request.status not in {"rejected"}
        ])

        payment_requests_total += requests_count
        active_payment_requests_total += active_requests_count

        event_rows.append(
            ManagerDashboardEventRead(
                id=event.id,
                client_name=event.client_name,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                external_total=q(money(summary["external_total"])),
                fact_total=q(money(summary["fact_total"])),
                paid_total=q(money(summary["paid_total"])),
                final_company_income=q(final_income),
                manager_salary=q(money(summary["manager_salary"])),
                payment_requests_count=requests_count,
                active_payment_requests_count=active_requests_count,
            )
        )

    personal_plan = manager_personal_plan_amount(plan)

    return ManagerDashboardRead(
        month=month_date,
        manager_id=manager.id,
        manager_name=manager.name,
        department_id=manager.department_id,
        department_name=department.name if department else None,
        include_drafts=include_drafts,

        personal_plan_amount=q(personal_plan),
        fact_income_amount=q(fact_income),
        completion_percent=completion_percent(fact_income, personal_plan),
        remaining_to_plan=q(personal_plan - fact_income),

        events_count=len(events),
        drafts_count=drafts_count,
        payment_requests_count=payment_requests_total,
        active_payment_requests_count=active_payment_requests_total,

        events=event_rows,
    )
