from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.monthly_closing import MonthlyClosing
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.models.user import User
from app.schemas.department_head_dashboard import (
    DepartmentHeadClosingRead,
    DepartmentHeadDashboardRead,
    DepartmentHeadEventRead,
    DepartmentHeadManagerRead,
)
from app.services.event_calculator import calculate_event_summary_values, q
from app.services.auth import require_roles


router = APIRouter(tags=["department_head_dashboard"])


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


def department_plan_amount(plan: MonthlyPlan, department_name: str) -> Decimal:
    if department_name == "Санжар":
        return q(money(plan.company_plan_amount) * money(plan.sanzhar_share_percent) / Decimal("100"))
    if department_name == "Рауфаль":
        return q(money(plan.company_plan_amount) * money(plan.raufal_share_percent) / Decimal("100"))
    return Decimal("0.00")


def department_expenses(db: Session, department_name: str, year: int, month: int) -> Decimal:
    expenses = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == year,
            extract("month", MonthlyExpense.month) == month,
        )
    ).scalars().all()

    total = Decimal("0.00")
    for expense in expenses:
        if department_name == "Санжар":
            total += money(expense.sanzhar_amount)
        elif department_name == "Рауфаль":
            total += money(expense.raufal_amount)

    return q(total)


def build_department_closing(closing: MonthlyClosing | None, department_name: str) -> DepartmentHeadClosingRead:
    if closing is None:
        return DepartmentHeadClosingRead(is_closed=False)

    if department_name == "Санжар":
        return DepartmentHeadClosingRead(
            is_closed=True,
            status=closing.status,
            plan_amount=closing.sanzhar_plan_amount,
            income_amount=closing.sanzhar_income_amount,
            expense_amount=closing.sanzhar_expense_amount,
            completion_percent=closing.sanzhar_completion_percent,
            head_percent=closing.sanzhar_head_percent,
            head_salary=closing.sanzhar_head_salary,
            remaining_after_head=closing.sanzhar_remaining_after_head,
        )

    if department_name == "Рауфаль":
        return DepartmentHeadClosingRead(
            is_closed=True,
            status=closing.status,
            plan_amount=closing.raufal_plan_amount,
            income_amount=closing.raufal_income_amount,
            expense_amount=closing.raufal_expense_amount,
            completion_percent=closing.raufal_completion_percent,
            head_percent=closing.raufal_head_percent,
            head_salary=closing.raufal_head_salary,
            remaining_after_head=closing.raufal_remaining_after_head,
        )

    return DepartmentHeadClosingRead(is_closed=True, status=closing.status)


@router.get("/department-head-dashboard", response_model=DepartmentHeadDashboardRead)
def get_department_head_dashboard(
    department_id: int,
    month: str,
    include_drafts: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "department_head")),
):
    month_date = parse_month(month)

    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    if current_user.role == "department_head" and current_user.department_id != department_id:
        raise HTTPException(status_code=403, detail="Department head can view only own department")

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Monthly plan not found")

    managers = db.execute(
        select(User)
        .where(User.department_id == department_id, User.is_active == True)  # noqa: E712
        .order_by(User.id)
    ).scalars().all()

    event_query = select(Event).where(
        Event.department_id == department_id,
        extract("year", Event.event_date) == month_date.year,
        extract("month", Event.event_date) == month_date.month,
        Event.status != "cancelled",
    )

    if not include_drafts:
        event_query = event_query.where(Event.status != "draft")

    events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().all()

    manager_name_by_id = {manager.id: manager.name for manager in managers}

    fact_income = Decimal("0.00")
    drafts_count = 0
    event_rows = []

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
        paid_total = money(summary["paid_total"])

        fact_income += final_income

        event_rows.append(
            DepartmentHeadEventRead(
                id=event.id,
                client_name=event.client_name,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                manager_id=event.manager_id,
                manager_name=manager_name_by_id.get(event.manager_id),
                final_company_income=q(final_income),
                items_count=len(items),
                paid_total=q(paid_total),
            )
        )

    dept_plan = department_plan_amount(plan, department.name)
    expenses = department_expenses(db, department.name, month_date.year, month_date.month)

    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()

    return DepartmentHeadDashboardRead(
        month=month_date,
        department_id=department.id,
        department_name=department.name,

        plan_amount=q(dept_plan),
        fact_income_amount=q(fact_income),
        completion_percent=completion_percent(fact_income, dept_plan),
        remaining_to_plan=q(dept_plan - fact_income),
        expenses_amount=q(expenses),

        events_count=len(events),
        drafts_count=drafts_count,
        managers_count=len(managers),
        include_drafts=include_drafts,

        managers=[
            DepartmentHeadManagerRead(
                id=manager.id,
                name=manager.name,
                role=manager.role,
                is_active=manager.is_active,
            )
            for manager in managers
        ],
        events=event_rows,
        closing=build_department_closing(closing, department.name),
    )
