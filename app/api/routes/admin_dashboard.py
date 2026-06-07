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
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.admin_dashboard import (
    AdminClosingRead,
    AdminDashboardRead,
    AdminDepartmentDashboardRead,
    AdminEventRowRead,
    AdminPaymentRequestRowRead,
)
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["admin_dashboard"])


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


def manager_personal_plan_amount(plan: MonthlyPlan) -> Decimal:
    return q(money(plan.company_plan_amount) * money(plan.manager_personal_plan_percent) / Decimal("100"))


def tax_status_label(tax_status: str | None) -> str | None:
    labels = {
        "our_vat": "ОУР с НДС",
        "our_no_vat": "ОУР без НДС",
        "simplified": "Упрощенка",
        "snr": "СНР",
        "self_employed": "Самозанятый",
        "not_found": "Не проверен",
        None: None,
    }
    return labels.get(tax_status, tax_status)


def payment_method_label(payment_method: str | None) -> str:
    labels = {
        "invoice": "По счету",
        "card": "На карту",
        "cash": "Налик",
        "self_employed": "Самозанятый",
    }
    return labels.get(payment_method, payment_method or "")


def get_department_expenses(db: Session, department_name: str, year: int, month: int) -> Decimal:
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


def build_closing(closing: MonthlyClosing | None) -> AdminClosingRead:
    if closing is None:
        return AdminClosingRead(is_closed=False)

    return AdminClosingRead(
        is_closed=True,
        status=closing.status,
        sanzhar_head_salary=closing.sanzhar_head_salary,
        raufal_head_salary=closing.raufal_head_salary,
        sanzhar_remaining_after_head=closing.sanzhar_remaining_after_head,
        raufal_remaining_after_head=closing.raufal_remaining_after_head,
        founders_total_amount=closing.founders_total_amount,
        founder_one_amount=closing.founder_one_amount,
        founder_two_amount=closing.founder_two_amount,
        founder_three_amount=closing.founder_three_amount,
    )


@router.get("/admin-dashboard", response_model=AdminDashboardRead)
def get_admin_dashboard(
    month: str,
    include_drafts: bool = True,
    db: Session = Depends(get_db),
):
    month_date = parse_month(month)

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Monthly plan not found")

    departments = db.execute(
        select(Department).where(Department.is_active == True).order_by(Department.id)  # noqa: E712
    ).scalars().all()

    users = db.execute(select(User).where(User.is_active == True)).scalars().all()  # noqa: E712
    user_by_id = {user.id: user for user in users}
    dept_by_id = {department.id: department for department in departments}

    event_query = select(Event).where(
        extract("year", Event.event_date) == month_date.year,
        extract("month", Event.event_date) == month_date.month,
        Event.status != "cancelled",
    )
    if not include_drafts:
        event_query = event_query.where(Event.status != "draft")

    events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().all()

    events_by_department = {department.id: [] for department in departments}
    event_rows = []
    event_summary_by_id = {}

    for event in events:
        items = db.execute(
            select(EventItem)
            .where(EventItem.event_id == event.id, EventItem.is_deleted == False)  # noqa: E712
            .order_by(EventItem.sort_order, EventItem.id)
        ).scalars().all()

        summary = calculate_event_summary_values(event, items)
        event_summary_by_id[event.id] = summary
        events_by_department.setdefault(event.department_id, []).append(event)

        department = dept_by_id.get(event.department_id)
        manager = user_by_id.get(event.manager_id)

        event_rows.append(
            AdminEventRowRead(
                id=event.id,
                client_name=event.client_name,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                department_id=event.department_id,
                department_name=department.name if department else None,
                manager_id=event.manager_id,
                manager_name=manager.name if manager else None,
                final_company_income=q(money(summary["final_company_income"])),
                external_total=q(money(summary["external_total"])),
                paid_total=q(money(summary["paid_total"])),
                items_count=len(items),
            )
        )

    department_rows = []
    company_fact = Decimal("0.00")
    company_expenses = Decimal("0.00")

    for department in departments:
        dept_events = events_by_department.get(department.id, [])
        dept_fact = sum(
            (money(event_summary_by_id[event.id]["final_company_income"]) for event in dept_events),
            Decimal("0.00"),
        )
        dept_plan = department_plan_amount(plan, department.name)
        dept_expenses = get_department_expenses(db, department.name, month_date.year, month_date.month)
        drafts_count = len([event for event in dept_events if event.status == "draft"])
        managers_count = len([user for user in users if user.department_id == department.id])

        company_fact += dept_fact
        company_expenses += dept_expenses

        department_rows.append(
            AdminDepartmentDashboardRead(
                department_id=department.id,
                department_name=department.name,
                plan_amount=q(dept_plan),
                fact_income_amount=q(dept_fact),
                completion_percent=completion_percent(dept_fact, dept_plan),
                remaining_to_plan=q(dept_plan - dept_fact),
                expenses_amount=q(dept_expenses),
                events_count=len(dept_events),
                drafts_count=drafts_count,
                managers_count=managers_count,
            )
        )

    if events:
        payment_query = (
            select(PaymentRequest)
            .where(PaymentRequest.event_id.in_([event.id for event in events]))
            .order_by(PaymentRequest.id.desc())
            .limit(50)
        )
        payment_requests = db.execute(payment_query).scalars().all()
    else:
        payment_requests = []

    event_title_by_id = {event.id: event.title for event in events}

    payment_rows = [
        AdminPaymentRequestRowRead(
            id=request.id,
            event_id=request.event_id,
            event_title=event_title_by_id.get(request.event_id),
            position=request.item_name_snapshot,
            amount_requested=request.amount_requested,
            payment_method=payment_method_label(request.payment_method),
            status=request.status,
            tax_status=tax_status_label(request.tax_status_snapshot),
            warning_over_remaining=request.warning_over_remaining,
        )
        for request in payment_requests
    ]

    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()

    return AdminDashboardRead(
        month=month_date,
        include_drafts=include_drafts,
        company_plan_amount=q(plan.company_plan_amount),
        company_fact_income_amount=q(company_fact),
        company_completion_percent=completion_percent(company_fact, money(plan.company_plan_amount)),
        company_expenses_amount=q(company_expenses),
        manager_personal_plan_amount=manager_personal_plan_amount(plan),
        departments=department_rows,
        events=event_rows,
        payment_requests=payment_rows,
        closing=build_closing(closing),
    )
