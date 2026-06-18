from datetime import date
from decimal import Decimal
import logging
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.department import Department
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.event_share import EventShare
from app.models.monthly_closing import MonthlyClosing
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.department_head_dashboard import (
    DepartmentHeadCalculationRead,
    DepartmentHeadDashboardRead,
    DepartmentHeadDashboardBundleRead,
    DepartmentHeadEventRead,
    DepartmentHeadExpenseRead,
    DepartmentHeadManagerRead,
    DepartmentHeadPaymentRequestRead,
)

from app.schemas.event import EventRead
from app.schemas.event_item import EventItemRead
from app.schemas.manager_dashboard import ManagerEventFullPayload
from app.api.routes.manager_dashboard import build_event_summary_read_for_bundle
from app.api.routes.payment_requests import enrich_payment_request_read_fast
from app.services.auth import require_roles
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["department_head_dashboard"])
logger = logging.getLogger("contrast.performance")

INACTIVE_PAYMENT_STATUSES = {"cancelled", "rejected"}


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


def payment_method_label(payment_method: str | None) -> str:
    labels = {
        "invoice": "По счету",
        "card": "На карту",
        "cash": "Налик",
        "self_employed": "Самозанятый",
    }
    return labels.get(payment_method, payment_method or "")


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


def allocated_amount(value: Decimal, share_percent: Decimal) -> Decimal:
    return q(money(value) * money(share_percent) / Decimal("100"))


def event_share_allocations(event: Event, user_by_id: dict[int, User]) -> list[tuple[User | None, Decimal]]:
    shares = list(event.shares or [])
    if not shares:
        return [(user_by_id.get(event.manager_id), Decimal("100.00"))]
    return [(user_by_id.get(share.user_id), money(share.share_percent)) for share in shares]


def department_share_percent(event: Event, department_id: int, user_by_id: dict[int, User]) -> Decimal:
    shares = list(event.shares or [])
    if not shares:
        manager = user_by_id.get(event.manager_id)
        owner_department_id = manager.department_id if manager and manager.department_id else event.department_id
        return Decimal("100.00") if owner_department_id == department_id else Decimal("0.00")

    percent = Decimal("0.00")
    for share in shares:
        manager = user_by_id.get(share.user_id)
        if manager and manager.department_id == department_id:
            percent += money(share.share_percent)
    return q(percent)


def event_visible_for_department(event: Event, department_id: int, user_by_id: dict[int, User]) -> bool:
    # Department-head cabinet follows the current manager/share ownership.
    # event.department_id can be stale after a manager moves to another department,
    # so it is only a last-resort fallback when the manager record is missing.
    if department_share_percent(event, department_id, user_by_id) > Decimal("0.00"):
        return True

    if event.shares:
        return False

    manager = user_by_id.get(event.manager_id)
    return manager is None and event.department_id == department_id


def expense_default_split_amounts(db: Session, expense: MonthlyExpense) -> tuple[Decimal, Decimal]:
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == expense.month)).scalar_one_or_none()
    sanzhar_percent = money(plan.sanzhar_share_percent) if plan is not None else Decimal("66.67")
    sanzhar = q(money(expense.amount) * sanzhar_percent / Decimal("100"))
    return sanzhar, q(money(expense.amount) - sanzhar)


def allocated_expense_amounts(db: Session, expense: MonthlyExpense) -> tuple[Decimal, Decimal]:
    if expense.allocation_type == "default_split":
        return expense_default_split_amounts(db, expense)
    return q(money(expense.sanzhar_amount)), q(money(expense.raufal_amount))


def expense_allocation_label(expense: MonthlyExpense) -> str:
    labels = {
        "default_split": "По плану месяца",
        "sanzhar_only": "100% Санжар",
        "raufal_only": "100% Рауфаль",
        "custom": "Вручную",
    }
    return labels.get(expense.allocation_type, expense.allocation_type or "")


def head_percent(income: Decimal, plan: Decimal) -> Decimal:
    return Decimal("15.00") if income >= plan and plan > 0 else Decimal("10.00")


def head_salary(income: Decimal, expenses: Decimal, percent: Decimal) -> Decimal:
    base = money(income) - money(expenses)
    if base <= 0:
        return Decimal("0.00")
    return q(base * percent / Decimal("100"))


def default_plan(month_date: date) -> MonthlyPlan:
    return MonthlyPlan(
        month=month_date,
        company_plan_amount=Decimal("0.00"),
        sanzhar_share_percent=Decimal("66.67"),
        raufal_share_percent=Decimal("33.33"),
        manager_personal_plan_percent=Decimal("12.50"),
        created_at=None,
        updated_at=None,
    )


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
        plan = default_plan(month_date)

    all_users = db.execute(select(User)).scalars().all()
    active_users = [user for user in all_users if user.is_active]
    user_by_id = {user.id: user for user in all_users}
    managers = [user for user in active_users if user.role == "manager" and user.department_id == department_id]
    manager_name_by_id = {user.id: user.name for user in all_users}

    event_query = (
        select(Event)
        .options(
            selectinload(Event.items),
            selectinload(Event.payment_requests),
            selectinload(Event.shares),
        )
        .where(
            extract("year", Event.event_date) == month_date.year,
            extract("month", Event.event_date) == month_date.month,
            Event.status != "cancelled",
        )
    )
    if not include_drafts:
        event_query = event_query.where(Event.status != "draft")

    all_month_events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().all()
    events = [event for event in all_month_events if event_visible_for_department(event, department_id, user_by_id)]

    dept_fact = Decimal("0.00")
    drafts_count = 0
    event_rows: list[DepartmentHeadEventRead] = []
    manager_fact_by_id = {manager.id: Decimal("0.00") for manager in managers}
    manager_event_ids_by_id = {manager.id: set() for manager in managers}

    for event in events:
        if event.status == "draft":
            drafts_count += 1

        items = sorted(
            [item for item in (event.items or []) if item.is_deleted is False],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )

        summary = calculate_event_summary_values(event, items)
        full_final_income = money(summary["final_company_income"])
        full_manager_salary = money(summary.get("manager_salary", Decimal("0.00")))
        paid_total = money(summary["paid_total"])
        external_total = money(summary.get("external_total", Decimal("0.00")))

        event_payment_requests = list(event.payment_requests or [])
        requests_count = len(event_payment_requests)
        active_requests_count = len([
            request for request in event_payment_requests
            if request.status not in INACTIVE_PAYMENT_STATUSES
        ])

        share_percent = department_share_percent(event, department_id, user_by_id)
        department_income = allocated_amount(full_final_income, share_percent)
        dept_fact += department_income

        # event_share_allocations() already returns the owner with 100% for non-shared events.
        # Do not add a second fallback block here: that doubles personal manager facts
        # in the department-head cabinet while the department total remains correct.
        for allocated_manager, allocation_percent in event_share_allocations(event, user_by_id):
            if allocated_manager and allocated_manager.department_id == department_id:
                manager_fact_by_id[allocated_manager.id] = manager_fact_by_id.get(allocated_manager.id, Decimal("0.00")) + allocated_amount(full_final_income, allocation_percent)
                manager_event_ids_by_id.setdefault(allocated_manager.id, set()).add(event.id)

        event_rows.append(
            DepartmentHeadEventRead(
                id=event.id,
                client_name=event.client_name,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                money_status=getattr(event, "money_status", "waiting_money"),
                client_calc_type=event.client_calc_type,
                department_id=event.department_id,
                department_name=department.name,
                manager_id=event.manager_id,
                manager_name=manager_name_by_id.get(event.manager_id),
                final_company_income=q(full_final_income),
                department_income=q(department_income),
                department_share_percent=q(share_percent),
                external_total=q(external_total),
                paid_total=q(paid_total),
                manager_salary=q(allocated_amount(full_manager_salary, share_percent)),
                payment_requests_count=requests_count,
                active_payment_requests_count=active_requests_count,
                items_count=len(items),
                is_shared=bool(event.shares),
            )
        )

    dept_plan = department_plan_amount(plan, department.name)

    expenses_all = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == month_date.year,
            extract("month", MonthlyExpense.month) == month_date.month,
        ).order_by(MonthlyExpense.id.desc())
    ).scalars().all()

    expense_rows: list[DepartmentHeadExpenseRead] = []
    dept_expenses = Decimal("0.00")
    for expense in expenses_all:
        sanzhar_amount, raufal_amount = allocated_expense_amounts(db, expense)
        department_amount = sanzhar_amount if department.name == "Санжар" else raufal_amount if department.name == "Рауфаль" else Decimal("0.00")
        if department_amount <= Decimal("0.00"):
            continue
        dept_expenses += department_amount
        expense_rows.append(
            DepartmentHeadExpenseRead(
                id=expense.id,
                month=expense.month,
                title=expense.title,
                total_amount=q(money(expense.amount)),
                department_amount=q(department_amount),
                allocation_type=expense.allocation_type,
                allocation_label=expense_allocation_label(expense),
                comment=expense.comment,
                created_at=expense.created_at,
            )
        )

    event_by_id = {event.id: event for event in events}
    visible_event_ids = list(event_by_id.keys())
    if visible_event_ids:
        requests = db.execute(
            select(PaymentRequest)
            .where(PaymentRequest.event_id.in_(visible_event_ids))
            .order_by(PaymentRequest.id.desc())
            .limit(200)
        ).scalars().all()
    else:
        requests = []

    payment_rows = []
    for request in requests:
        event = event_by_id.get(request.event_id)
        created_by = user_by_id.get(request.created_by_user_id)
        payment_rows.append(
            DepartmentHeadPaymentRequestRead(
                id=request.id,
                created_at=request.created_at,
                event_id=request.event_id,
                event_title=event.title if event else None,
                client_name=event.client_name if event else None,
                manager_name=created_by.name if created_by else manager_name_by_id.get(event.manager_id) if event else None,
                position=request.item_name_snapshot,
                amount_requested=request.amount_requested,
                payment_method=payment_method_label(request.payment_method),
                status=request.status,
                money_status=getattr(request, "money_status", "waiting_money"),
                tax_status=tax_status_label(request.tax_status_snapshot),
                warning_over_remaining=request.warning_over_remaining,
            )
        )

    personal_plan = manager_personal_plan_amount(plan)
    manager_rows = []
    for manager in managers:
        manager_fact = q(manager_fact_by_id.get(manager.id, Decimal("0.00")))
        manager_rows.append(
            DepartmentHeadManagerRead(
                id=manager.id,
                name=manager.name,
                role=manager.role,
                is_active=manager.is_active,
                plan_amount=q(personal_plan),
                fact_income_amount=q(manager_fact),
                completion_percent=completion_percent(manager_fact, personal_plan),
                events_count=len(manager_event_ids_by_id.get(manager.id, set())),
            )
        )

    dept_completion = completion_percent(dept_fact, dept_plan)
    dept_head_percent = head_percent(dept_fact, dept_plan)
    dept_head_salary = head_salary(dept_fact, dept_expenses, dept_head_percent)
    dept_remaining = q(dept_fact - dept_expenses - dept_head_salary)

    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()

    return DepartmentHeadDashboardRead(
        month=month_date,
        department_id=department.id,
        department_name=department.name,
        plan_amount=q(dept_plan),
        fact_income_amount=q(dept_fact),
        completion_percent=q(dept_completion),
        remaining_to_plan=q(dept_plan - dept_fact),
        expenses_amount=q(dept_expenses),
        events_count=len(events),
        drafts_count=drafts_count,
        managers_count=len(managers),
        include_drafts=include_drafts,
        managers=manager_rows,
        events=event_rows,
        payment_requests=payment_rows,
        expenses=expense_rows,
        calculation=DepartmentHeadCalculationRead(
            status=closing.status if closing else "current",
            plan_amount=q(dept_plan),
            income_amount=q(dept_fact),
            expense_amount=q(dept_expenses),
            completion_percent=q(dept_completion),
            head_percent=q(dept_head_percent),
            head_salary=q(dept_head_salary),
            remaining_after_head=q(dept_remaining),
        ),
    )


@router.get("/department-head-dashboard-bundle", response_model=DepartmentHeadDashboardBundleRead)
def get_department_head_dashboard_bundle(
    department_id: int,
    month: str,
    include_drafts: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "department_head")),
):
    """Optimized department-head payload: dashboard + full event payloads in one response."""
    perf_total_started = perf_counter()
    perf_marks: dict[str, float] = {}

    def mark_perf(name: str) -> None:
        perf_marks[name] = perf_counter()

    def delta(start_name: str, end_name: str) -> float:
        return perf_marks[end_name] - perf_marks[start_name]

    month_date = parse_month(month)
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    if current_user.role == "department_head" and current_user.department_id != department_id:
        raise HTTPException(status_code=403, detail="Department head can view only own department")
    mark_perf("parse")

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        plan = default_plan(month_date)
    all_users = db.execute(select(User)).scalars().all()
    active_users = [user for user in all_users if user.is_active]
    user_by_id = {user.id: user for user in all_users}
    managers = [user for user in active_users if user.role == "manager" and user.department_id == department_id]
    manager_name_by_id = {user.id: user.name for user in all_users}
    expenses_all = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == month_date.year,
            extract("month", MonthlyExpense.month) == month_date.month,
        ).order_by(MonthlyExpense.id.desc())
    ).scalars().all()
    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()
    mark_perf("base_sql")

    event_query = (
        select(Event)
        .options(
            selectinload(Event.items),
            selectinload(Event.payment_requests),
            selectinload(Event.shares),
        )
        .where(
            extract("year", Event.event_date) == month_date.year,
            extract("month", Event.event_date) == month_date.month,
            Event.status != "cancelled",
        )
    )
    if not include_drafts:
        event_query = event_query.where(Event.status != "draft")

    all_month_events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().unique().all()
    events = [event for event in all_month_events if event_visible_for_department(event, department_id, user_by_id)]
    mark_perf("events_sql")

    active_items: list[EventItem] = []
    for event in events:
        active_items.extend([item for item in (event.items or []) if item.is_deleted is False])
    if active_items:
        item_ids = [int(item.id) for item in active_items if item.id is not None]
        paid_totals = dict(
            db.execute(
                select(
                    PaymentRequest.event_item_id,
                    func.coalesce(func.sum(PaymentRequest.amount_requested), 0),
                )
                .where(
                    PaymentRequest.event_item_id.in_(item_ids),
                    PaymentRequest.status == "paid",
                )
                .group_by(PaymentRequest.event_item_id)
            ).all()
        )
        paid_changed = False
        for item in active_items:
            actual_paid = money(paid_totals.get(item.id, Decimal("0.00")))
            if money(item.paid_amount) != actual_paid:
                item.paid_amount = actual_paid
                db.add(item)
                paid_changed = True
        if paid_changed:
            db.flush()
    mark_perf("paid_sync")

    dept_fact = Decimal("0.00")
    drafts_count = 0
    event_rows: list[DepartmentHeadEventRead] = []
    manager_fact_by_id = {manager.id: Decimal("0.00") for manager in managers}
    manager_event_ids_by_id = {manager.id: set() for manager in managers}
    event_payloads: dict[int, ManagerEventFullPayload] = {}
    payment_requests_by_id: dict[int, PaymentRequest] = {}

    for event in events:
        if event.status == "draft":
            drafts_count += 1
        items = sorted(
            [item for item in (event.items or []) if item.is_deleted is False],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )
        summary = calculate_event_summary_values(event, items)
        full_final_income = money(summary["final_company_income"])
        full_manager_salary = money(summary.get("manager_salary", Decimal("0.00")))
        paid_total = money(summary["paid_total"])
        external_total = money(summary.get("external_total", Decimal("0.00")))
        event_payment_requests = sorted(list(event.payment_requests or []), key=lambda request: request.id or 0, reverse=True)
        for request in event_payment_requests:
            payment_requests_by_id[int(request.id)] = request
        requests_count = len(event_payment_requests)
        active_requests_count = len([
            request for request in event_payment_requests
            if request.status not in INACTIVE_PAYMENT_STATUSES
        ])
        share_percent = department_share_percent(event, department_id, user_by_id)
        department_income = allocated_amount(full_final_income, share_percent)
        dept_fact += department_income

        # event_share_allocations() already returns the owner with 100% for non-shared events.
        # Keep manager personal facts from a single allocation source to match admin totals.
        for allocated_manager, allocation_percent in event_share_allocations(event, user_by_id):
            if allocated_manager and allocated_manager.department_id == department_id:
                manager_fact_by_id[allocated_manager.id] = manager_fact_by_id.get(allocated_manager.id, Decimal("0.00")) + allocated_amount(full_final_income, allocation_percent)
                manager_event_ids_by_id.setdefault(allocated_manager.id, set()).add(event.id)

        event_rows.append(
            DepartmentHeadEventRead(
                id=event.id,
                client_name=event.client_name,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                money_status=getattr(event, "money_status", "waiting_money"),
                client_calc_type=event.client_calc_type,
                department_id=event.department_id,
                department_name=department.name,
                manager_id=event.manager_id,
                manager_name=manager_name_by_id.get(event.manager_id),
                final_company_income=q(full_final_income),
                department_income=q(department_income),
                department_share_percent=q(share_percent),
                external_total=q(external_total),
                paid_total=q(paid_total),
                manager_salary=q(allocated_amount(full_manager_salary, share_percent)),
                payment_requests_count=requests_count,
                active_payment_requests_count=active_requests_count,
                items_count=len(items),
                is_shared=bool(event.shares),
            )
        )
        manager_name = manager_name_by_id.get(event.manager_id)
        event_payloads[int(event.id)] = ManagerEventFullPayload(
            event=EventRead.model_validate(event),
            items=[EventItemRead.model_validate(item) for item in items],
            summary=build_event_summary_read_for_bundle(event, items),
            requests=[
                enrich_payment_request_read_fast(request, event.client_name, event.title, manager_name)
                for request in event_payment_requests
            ],
        )
    mark_perf("payloads")

    dept_plan = department_plan_amount(plan, department.name)
    expense_rows: list[DepartmentHeadExpenseRead] = []
    dept_expenses = Decimal("0.00")
    for expense in expenses_all:
        if expense.allocation_type == "default_split":
            sanzhar_percent = money(plan.sanzhar_share_percent) if plan is not None else Decimal("66.67")
            sanzhar_amount = q(money(expense.amount) * sanzhar_percent / Decimal("100"))
            raufal_amount = q(money(expense.amount) - sanzhar_amount)
        else:
            sanzhar_amount = q(money(expense.sanzhar_amount))
            raufal_amount = q(money(expense.raufal_amount))
        department_amount = sanzhar_amount if department.name == "Санжар" else raufal_amount if department.name == "Рауфаль" else Decimal("0.00")
        if department_amount <= Decimal("0.00"):
            continue
        dept_expenses += department_amount
        expense_rows.append(
            DepartmentHeadExpenseRead(
                id=expense.id,
                month=expense.month,
                title=expense.title,
                total_amount=q(money(expense.amount)),
                department_amount=q(department_amount),
                allocation_type=expense.allocation_type,
                allocation_label=expense_allocation_label(expense),
                comment=expense.comment,
                created_at=expense.created_at,
            )
        )
    mark_perf("expenses_calc")

    payment_rows = []
    event_by_id = {event.id: event for event in events}
    for request in sorted(payment_requests_by_id.values(), key=lambda item: item.id or 0, reverse=True):
        event = event_by_id.get(request.event_id)
        created_by = user_by_id.get(request.created_by_user_id)
        payment_rows.append(
            DepartmentHeadPaymentRequestRead(
                id=request.id,
                created_at=request.created_at,
                event_id=request.event_id,
                event_title=event.title if event else None,
                client_name=event.client_name if event else None,
                manager_name=created_by.name if created_by else manager_name_by_id.get(event.manager_id) if event else None,
                position=request.item_name_snapshot,
                amount_requested=request.amount_requested,
                payment_method=payment_method_label(request.payment_method),
                status=request.status,
                money_status=getattr(request, "money_status", "waiting_money"),
                tax_status=tax_status_label(request.tax_status_snapshot),
                warning_over_remaining=request.warning_over_remaining,
            )
        )

    personal_plan = manager_personal_plan_amount(plan)
    manager_rows = []
    for manager in managers:
        manager_fact = q(manager_fact_by_id.get(manager.id, Decimal("0.00")))
        manager_rows.append(
            DepartmentHeadManagerRead(
                id=manager.id,
                name=manager.name,
                role=manager.role,
                is_active=manager.is_active,
                plan_amount=q(personal_plan),
                fact_income_amount=q(manager_fact),
                completion_percent=completion_percent(manager_fact, personal_plan),
                events_count=len(manager_event_ids_by_id.get(manager.id, set())),
            )
        )
    mark_perf("rows_build")

    dept_completion = completion_percent(dept_fact, dept_plan)
    dept_head_percent = head_percent(dept_fact, dept_plan)
    dept_head_salary = head_salary(dept_fact, dept_expenses, dept_head_percent)
    dept_remaining = q(dept_fact - dept_expenses - dept_head_salary)

    dashboard = DepartmentHeadDashboardRead(
        month=month_date,
        department_id=department.id,
        department_name=department.name,
        plan_amount=q(dept_plan),
        fact_income_amount=q(dept_fact),
        completion_percent=q(dept_completion),
        remaining_to_plan=q(dept_plan - dept_fact),
        expenses_amount=q(dept_expenses),
        events_count=len(events),
        drafts_count=drafts_count,
        managers_count=len(managers),
        include_drafts=include_drafts,
        managers=manager_rows,
        events=event_rows,
        payment_requests=payment_rows,
        expenses=expense_rows,
        calculation=DepartmentHeadCalculationRead(
            status=closing.status if closing else "current",
            plan_amount=q(dept_plan),
            income_amount=q(dept_fact),
            expense_amount=q(dept_expenses),
            completion_percent=q(dept_completion),
            head_percent=q(dept_head_percent),
            head_salary=q(dept_head_salary),
            remaining_after_head=q(dept_remaining),
        ),
    )
    response = DepartmentHeadDashboardBundleRead(dashboard=dashboard, event_payloads=event_payloads)
    mark_perf("response_model")

    items_count = len(active_items)
    requests_count = sum(len(event.payment_requests or []) for event in events)
    shares_count = sum(len(event.shares or []) for event in events)
    logger.warning(
        "PERF department-head-dashboard-bundle month=%s department_id=%s include_drafts=%s events=%s items=%s requests=%s shares=%s users=%s expenses=%s "
        "base_sql=%.3fs events_sql=%.3fs paid_sync=%.3fs payloads=%.3fs expenses_calc=%.3fs rows_build=%.3fs response_model=%.3fs total=%.3fs",
        month,
        department_id,
        include_drafts,
        len(events),
        items_count,
        requests_count,
        shares_count,
        len(all_users),
        len(expenses_all),
        delta("parse", "base_sql"),
        delta("base_sql", "events_sql"),
        delta("events_sql", "paid_sync"),
        delta("paid_sync", "payloads"),
        delta("payloads", "expenses_calc"),
        delta("expenses_calc", "rows_build"),
        delta("rows_build", "response_model"),
        perf_marks["response_model"] - perf_total_started,
    )

    return response
