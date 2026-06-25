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
from app.schemas.admin_dashboard import (
    AdminClosingRead,
    AdminDashboardRead,
    AdminDashboardBundleRead,
    AdminDepartmentDashboardRead,
    AdminEventRowRead,
    AdminPaymentRequestRowRead,
)
from app.services.event_calculator import calculate_event_summary_values, q, q0

from app.schemas.event import EventRead
from app.schemas.event_item import EventItemRead
from app.schemas.manager_dashboard import ManagerEventFullPayload
from app.api.routes.manager_dashboard import build_event_summary_read_for_bundle
from app.api.routes.payment_requests import enrich_payment_request_read_fast
from app.services.auth import require_roles


router = APIRouter(tags=["admin_dashboard"])
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


def expense_default_split_amounts(db: Session, expense: MonthlyExpense) -> tuple[Decimal, Decimal]:
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == expense.month)).scalar_one_or_none()
    sanzhar_percent = money(plan.sanzhar_share_percent) if plan is not None else Decimal("66.67")
    sanzhar = q(money(expense.amount) * sanzhar_percent / Decimal("100"))
    return sanzhar, q(money(expense.amount) - sanzhar)


def get_department_expenses(db: Session, department_name: str, year: int, month: int) -> Decimal:
    # Backward-compatible helper for old call sites. The admin dashboard uses
    # preloaded monthly expenses via build_department_expenses_by_name() below
    # to avoid repeating the same SQL work for every department.
    expenses = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == year,
            extract("month", MonthlyExpense.month) == month,
        )
    ).scalars().all()
    plan = db.execute(
        select(MonthlyPlan).where(
            extract("year", MonthlyPlan.month) == year,
            extract("month", MonthlyPlan.month) == month,
        )
    ).scalar_one_or_none()
    return build_department_expenses_by_name(expenses, plan).get(department_name, Decimal("0.00"))


def build_department_expenses_by_name(
    expenses: list[MonthlyExpense],
    plan: MonthlyPlan | None,
) -> dict[str, Decimal]:
    sanzhar_percent = money(plan.sanzhar_share_percent) if plan is not None else Decimal("66.67")
    totals = {"Санжар": Decimal("0.00"), "Рауфаль": Decimal("0.00")}

    for expense in expenses:
        if expense.allocation_type == "default_split":
            sanzhar_amount = q(money(expense.amount) * sanzhar_percent / Decimal("100"))
            raufal_amount = q(money(expense.amount) - sanzhar_amount)
        else:
            sanzhar_amount = money(expense.sanzhar_amount)
            raufal_amount = money(expense.raufal_amount)

        totals["Санжар"] += sanzhar_amount
        totals["Рауфаль"] += raufal_amount

    return {name: q(amount) for name, amount in totals.items()}


def build_closing(closing: MonthlyClosing | None) -> AdminClosingRead:
    if closing is None:
        return AdminClosingRead(is_closed=False)

    return AdminClosingRead(
        is_closed=closing.status == "closed",
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


def event_share_allocations(event: Event, user_by_id: dict[int, User]) -> list[tuple[User | None, Decimal]]:
    """
    Возвращает доли мероприятия для админки.

    Если соавторства нет:
    - 100% у владельца мероприятия.

    Если есть event_shares:
    - используем доли из event_shares;
    - так админка считает мероприятие так же, как кабинеты менеджеров.
    """
    shares = list(event.shares or [])

    if not shares:
        return [(user_by_id.get(event.manager_id), Decimal("100.00"))]

    allocations: list[tuple[User | None, Decimal]] = []
    for share in shares:
        allocations.append((user_by_id.get(share.user_id), money(share.share_percent)))

    return allocations


def allocated_amount(value: Decimal, share_percent: Decimal) -> Decimal:
    return q(money(value) * money(share_percent) / Decimal("100"))





def empty_monthly_tax_totals() -> dict[str, Decimal]:
    return {
        "turnover": Decimal("0.00"),
        "client_vat": Decimal("0.00"),
        "contractor_vat_credit": Decimal("0.00"),
        "ip_contrast_tax": Decimal("0.00"),
        "tax_deductions": Decimal("0.00"),
    }


def add_event_to_monthly_tax_totals(
    totals: dict[str, Decimal],
    event: Event,
    summary: dict,
) -> None:
    """
    Добавляет мероприятие в верхний блок админки, не пересчитывая смету второй раз.

    v0.40.79 пыталась считать эти показатели отдельным вторым проходом по мероприятиям.
    Если на одном старом/импортном мероприятии расчёт падал, ломался весь admin-dashboard-bundle
    и админка оставалась пустой. Теперь используем summary, который уже успешно посчитан
    для основной таблицы мероприятий, и не даём верхнему информеру уронить все вкладки.
    """
    totals["turnover"] += money(summary.get("turnover_with_vat") or summary.get("external_total"))
    totals["client_vat"] += money(summary.get("client_vat_amount"))
    totals["contractor_vat_credit"] += money(summary.get("contractor_vat_credit"))
    totals["tax_deductions"] += money(summary.get("deductions_total"))

    if event.client_calc_type == "ip_contrast_event":
        totals["ip_contrast_tax"] += money(summary.get("internal_tax_amount"))


def finalize_monthly_tax_totals(totals: dict[str, Decimal]) -> dict[str, Decimal]:
    vat_to_pay = q0(money(totals.get("client_vat")) - money(totals.get("contractor_vat_credit")))
    if vat_to_pay < 0:
        vat_to_pay = Decimal("0.00")

    tax_to_pay = q0(money(totals.get("ip_contrast_tax")) - money(totals.get("tax_deductions")))
    if tax_to_pay < 0:
        tax_to_pay = Decimal("0.00")

    return {
        "turnover": q0(money(totals.get("turnover"))),
        "vat_to_pay": q0(vat_to_pay),
        "tax_to_pay": q0(tax_to_pay),
    }


@router.get("/admin-dashboard", response_model=AdminDashboardRead)
def get_admin_dashboard(
    month: str,
    include_drafts: bool = True,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    perf_total_started = perf_counter()
    perf_marks: dict[str, float] = {}

    def mark_perf(name: str) -> None:
        perf_marks[name] = perf_counter()

    month_date = parse_month(month)
    mark_perf("parse")

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    # Админка не должна падать, если на выбранный месяц ещё не задан план.
    # В этом случае показываем месяц с нулевым планом и пустыми/фактическими данными.
    if plan is None:
        plan = MonthlyPlan(
            month=month_date,
            company_plan_amount=Decimal("0.00"),
            sanzhar_share_percent=Decimal("66.67"),
            raufal_share_percent=Decimal("33.33"),
            manager_personal_plan_percent=Decimal("12.50"),
            created_at=None,
            updated_at=None,
        )

    departments = db.execute(
        select(Department).where(Department.is_active == True).order_by(Department.id)  # noqa: E712
    ).scalars().all()

    # Для расчёта факта отделов нужны и уже отключённые менеджеры:
    # их кабинет блокируется, но мероприятия текущего месяца должны остаться в базе и в планах.
    all_users = db.execute(select(User)).scalars().all()
    active_users = [user for user in all_users if user.is_active]
    user_by_id = {user.id: user for user in all_users}
    dept_by_id = {department.id: department for department in departments}
    monthly_expenses = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == month_date.year,
            extract("month", MonthlyExpense.month) == month_date.month,
        )
    ).scalars().all()
    department_expenses_by_name = build_department_expenses_by_name(monthly_expenses, plan)
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

    events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().all()
    mark_perf("events_sql")

    event_rows = []
    department_fact_by_id = {department.id: Decimal("0.00") for department in departments}
    department_event_ids_by_id = {department.id: set() for department in departments}
    department_draft_event_ids_by_id = {department.id: set() for department in departments}
    monthly_tax_raw_totals = empty_monthly_tax_totals()

    for event in events:
        items = sorted(
            [item for item in (event.items or []) if item.is_deleted is False],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )

        summary = calculate_event_summary_values(event, items)
        add_event_to_monthly_tax_totals(monthly_tax_raw_totals, event, summary)
        full_final_income = money(summary["final_company_income"])
        full_manager_salary = money(summary["manager_salary"])

        event_payment_requests = list(event.payment_requests or [])

        requests_count = len(event_payment_requests)
        active_requests_count = len([
            request for request in event_payment_requests
            if request.status not in INACTIVE_PAYMENT_STATUSES
        ])

        allocations = event_share_allocations(event, user_by_id)

        for allocated_manager, share_percent in allocations:
            allocated_department = dept_by_id.get(allocated_manager.department_id) if allocated_manager and allocated_manager.department_id else None
            allocated_department_id = allocated_department.id if allocated_department else event.department_id
            allocated_department_name = allocated_department.name if allocated_department else (dept_by_id.get(event.department_id).name if dept_by_id.get(event.department_id) else None)

            allocated_final_income = allocated_amount(full_final_income, share_percent)
            allocated_manager_salary = allocated_amount(full_manager_salary, share_percent)

            department_fact_by_id[allocated_department_id] = department_fact_by_id.get(allocated_department_id, Decimal("0.00")) + allocated_final_income
            department_event_ids_by_id.setdefault(allocated_department_id, set()).add(event.id)
            if event.status == "draft":
                department_draft_event_ids_by_id.setdefault(allocated_department_id, set()).add(event.id)

            event_rows.append(
                AdminEventRowRead(
                    id=event.id,
                    client_name=event.client_name,
                    title=event.title,
                    event_date=event.event_date,
                    status=event.status,
                    money_status=getattr(event, "money_status", "waiting_money"),
                    client_calc_type=event.client_calc_type,
                    department_id=allocated_department_id,
                    department_name=allocated_department_name,
                    manager_id=allocated_manager.id if allocated_manager else event.manager_id,
                    manager_name=allocated_manager.name if allocated_manager else None,
                    final_company_income=q(allocated_final_income),
                    external_total=q(money(summary["external_total"])),
                    paid_total=q(money(summary["paid_total"])),
                    manager_salary=q(allocated_manager_salary),
                    payment_requests_count=requests_count,
                    active_payment_requests_count=active_requests_count,
                    items_count=len(items),
                )
            )

    mark_perf("events_calc")

    department_rows = []
    company_fact = Decimal("0.00")
    company_expenses = Decimal("0.00")

    for department in departments:
        dept_fact = department_fact_by_id.get(department.id, Decimal("0.00"))
        dept_plan = department_plan_amount(plan, department.name)
        dept_expenses = department_expenses_by_name.get(department.name, Decimal("0.00"))
        drafts_count = len(department_draft_event_ids_by_id.get(department.id, set()))
        managers_count = len([user for user in active_users if user.department_id == department.id])
        dept_events_count = len(department_event_ids_by_id.get(department.id, set()))

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
                events_count=dept_events_count,
                drafts_count=drafts_count,
                managers_count=managers_count,
            )
        )

    mark_perf("departments_calc")

    if events:
        payment_query = (
            select(PaymentRequest)
            .where(PaymentRequest.event_id.in_([event.id for event in events]))
            .order_by(PaymentRequest.id.desc())
        )
        payment_requests = db.execute(payment_query).scalars().all()
    else:
        payment_requests = []

    mark_perf("payments_sql")

    event_by_id = {event.id: event for event in events}

    payment_rows = [
        AdminPaymentRequestRowRead(
            id=request.id,
            created_at=request.created_at,
            event_id=request.event_id,
            event_title=event_by_id.get(request.event_id).title if event_by_id.get(request.event_id) else None,
            event_date=event_by_id.get(request.event_id).event_date if event_by_id.get(request.event_id) else None,
            client_name=event_by_id.get(request.event_id).client_name if event_by_id.get(request.event_id) else None,
            position=request.item_name_snapshot,
            amount_requested=request.amount_requested,
            payment_method=payment_method_label(request.payment_method),
            status=request.status,
            money_status=getattr(request, "money_status", "waiting_money"),
            tax_status=tax_status_label(request.tax_status_snapshot),
            card_number=request.card_number,
            contractor_name_snapshot=request.contractor_name_snapshot,
            warning_over_remaining=request.warning_over_remaining,
        )
        for request in payment_requests
    ]
    mark_perf("payments_rows")

    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()
    mark_perf("closing_sql")

    items_count = sum(len([item for item in (event.items or []) if item.is_deleted is False]) for event in events)
    requests_count = sum(len(event.payment_requests or []) for event in events)
    shares_count = sum(len(event.shares or []) for event in events)

    monthly_tax_totals = finalize_monthly_tax_totals(monthly_tax_raw_totals)

    dashboard = AdminDashboardRead(
        month=month_date,
        include_drafts=include_drafts,
        company_plan_amount=q(plan.company_plan_amount),
        company_fact_income_amount=q(company_fact),
        company_completion_percent=completion_percent(company_fact, money(plan.company_plan_amount)),
        company_expenses_amount=q(company_expenses),
        company_turnover_amount=monthly_tax_totals["turnover"],
        company_vat_to_pay_amount=monthly_tax_totals["vat_to_pay"],
        company_tax_to_pay_amount=monthly_tax_totals["tax_to_pay"],
        manager_personal_plan_amount=manager_personal_plan_amount(plan),
        departments=department_rows,
        events=event_rows,
        payment_requests=payment_rows,
        closing=build_closing(closing),
    )
    mark_perf("response_model")

    def delta(start_name: str, end_name: str) -> float:
        return perf_marks[end_name] - perf_marks[start_name]

    logger.warning(
        "PERF admin-dashboard month=%s include_drafts=%s events=%s items=%s requests=%s shares=%s expenses=%s "
        "base_sql=%.3fs events_sql=%.3fs events_calc=%.3fs departments_calc=%.3fs "
        "payments_sql=%.3fs payments_rows=%.3fs closing_sql=%.3fs response_model=%.3fs total=%.3fs",
        month,
        include_drafts,
        len(events),
        items_count,
        requests_count,
        shares_count,
        len(monthly_expenses),
        delta("parse", "base_sql"),
        delta("base_sql", "events_sql"),
        delta("events_sql", "events_calc"),
        delta("events_calc", "departments_calc"),
        delta("departments_calc", "payments_sql"),
        delta("payments_sql", "payments_rows"),
        delta("payments_rows", "closing_sql"),
        delta("closing_sql", "response_model"),
        perf_marks["response_model"] - perf_total_started,
    )

    return dashboard


@router.get("/admin-dashboard-bundle", response_model=AdminDashboardBundleRead)
def get_admin_dashboard_bundle(
    month: str,
    include_drafts: bool = True,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """Optimized admin payload: dashboard + full event modal payloads in one response."""
    perf_total_started = perf_counter()
    perf_marks: dict[str, float] = {}

    def mark_perf(name: str) -> None:
        perf_marks[name] = perf_counter()

    def delta(start_name: str, end_name: str) -> float:
        return perf_marks[end_name] - perf_marks[start_name]

    month_date = parse_month(month)
    mark_perf("parse")

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        plan = MonthlyPlan(
            month=month_date,
            company_plan_amount=Decimal("0.00"),
            sanzhar_share_percent=Decimal("66.67"),
            raufal_share_percent=Decimal("33.33"),
            manager_personal_plan_percent=Decimal("12.50"),
            created_at=None,
            updated_at=None,
        )

    departments = db.execute(
        select(Department).where(Department.is_active == True).order_by(Department.id)  # noqa: E712
    ).scalars().all()
    all_users = db.execute(select(User)).scalars().all()
    active_users = [user for user in all_users if user.is_active]
    user_by_id = {user.id: user for user in all_users}
    dept_by_id = {department.id: department for department in departments}
    monthly_expenses = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == month_date.year,
            extract("month", MonthlyExpense.month) == month_date.month,
        )
    ).scalars().all()
    department_expenses_by_name = build_department_expenses_by_name(monthly_expenses, plan)
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

    events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().unique().all()
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

    event_rows = []
    department_fact_by_id = {department.id: Decimal("0.00") for department in departments}
    department_event_ids_by_id = {department.id: set() for department in departments}
    department_draft_event_ids_by_id = {department.id: set() for department in departments}
    monthly_tax_raw_totals = empty_monthly_tax_totals()
    event_payloads: dict[int, ManagerEventFullPayload] = {}
    payment_requests_by_id: dict[int, PaymentRequest] = {}

    for event in events:
        items = sorted(
            [item for item in (event.items or []) if item.is_deleted is False],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )
        summary = calculate_event_summary_values(event, items)
        add_event_to_monthly_tax_totals(monthly_tax_raw_totals, event, summary)
        full_final_income = money(summary["final_company_income"])
        full_manager_salary = money(summary["manager_salary"])
        event_payment_requests = sorted(list(event.payment_requests or []), key=lambda request: request.id or 0, reverse=True)
        for request in event_payment_requests:
            payment_requests_by_id[int(request.id)] = request

        requests_count = len(event_payment_requests)
        active_requests_count = len([
            request for request in event_payment_requests
            if request.status not in INACTIVE_PAYMENT_STATUSES
        ])
        allocations = event_share_allocations(event, user_by_id)

        for allocated_manager, share_percent in allocations:
            allocated_department = dept_by_id.get(allocated_manager.department_id) if allocated_manager and allocated_manager.department_id else None
            allocated_department_id = allocated_department.id if allocated_department else event.department_id
            allocated_department_name = allocated_department.name if allocated_department else (dept_by_id.get(event.department_id).name if dept_by_id.get(event.department_id) else None)
            allocated_final_income = allocated_amount(full_final_income, share_percent)
            allocated_manager_salary = allocated_amount(full_manager_salary, share_percent)

            department_fact_by_id[allocated_department_id] = department_fact_by_id.get(allocated_department_id, Decimal("0.00")) + allocated_final_income
            department_event_ids_by_id.setdefault(allocated_department_id, set()).add(event.id)
            if event.status == "draft":
                department_draft_event_ids_by_id.setdefault(allocated_department_id, set()).add(event.id)

            event_rows.append(
                AdminEventRowRead(
                    id=event.id,
                    client_name=event.client_name,
                    title=event.title,
                    event_date=event.event_date,
                    status=event.status,
                    money_status=getattr(event, "money_status", "waiting_money"),
                    client_calc_type=event.client_calc_type,
                    department_id=allocated_department_id,
                    department_name=allocated_department_name,
                    manager_id=allocated_manager.id if allocated_manager else event.manager_id,
                    manager_name=allocated_manager.name if allocated_manager else None,
                    final_company_income=q(allocated_final_income),
                    external_total=q(money(summary["external_total"])),
                    paid_total=q(money(summary["paid_total"])),
                    manager_salary=q(allocated_manager_salary),
                    payment_requests_count=requests_count,
                    active_payment_requests_count=active_requests_count,
                    items_count=len(items),
                )
            )

        manager_name = user_by_id.get(event.manager_id).name if event.manager_id in user_by_id else None
        event_payloads[int(event.id)] = ManagerEventFullPayload(
            event=EventRead.model_validate(event),
            items=[EventItemRead.model_validate(item) for item in items],
            summary=build_event_summary_read_for_bundle(event, items),
            requests=[
                enrich_payment_request_read_fast(request, event.client_name, event.title, event.event_date, manager_name)
                for request in event_payment_requests
            ],
        )
    mark_perf("payloads")

    department_rows = []
    company_fact = Decimal("0.00")
    company_expenses = Decimal("0.00")
    for department in departments:
        dept_fact = department_fact_by_id.get(department.id, Decimal("0.00"))
        dept_plan = department_plan_amount(plan, department.name)
        dept_expenses = department_expenses_by_name.get(department.name, Decimal("0.00"))
        drafts_count = len(department_draft_event_ids_by_id.get(department.id, set()))
        managers_count = len([user for user in active_users if user.department_id == department.id])
        dept_events_count = len(department_event_ids_by_id.get(department.id, set()))
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
                events_count=dept_events_count,
                drafts_count=drafts_count,
                managers_count=managers_count,
            )
        )
    mark_perf("departments_calc")

    event_by_id = {event.id: event for event in events}
    payment_rows = [
        AdminPaymentRequestRowRead(
            id=request.id,
            created_at=request.created_at,
            event_id=request.event_id,
            event_title=event_by_id.get(request.event_id).title if event_by_id.get(request.event_id) else None,
            event_date=event_by_id.get(request.event_id).event_date if event_by_id.get(request.event_id) else None,
            client_name=event_by_id.get(request.event_id).client_name if event_by_id.get(request.event_id) else None,
            position=request.item_name_snapshot,
            amount_requested=request.amount_requested,
            payment_method=payment_method_label(request.payment_method),
            status=request.status,
            money_status=getattr(request, "money_status", "waiting_money"),
            tax_status=tax_status_label(request.tax_status_snapshot),
            card_number=request.card_number,
            contractor_name_snapshot=request.contractor_name_snapshot,
            warning_over_remaining=request.warning_over_remaining,
        )
        for request in sorted(payment_requests_by_id.values(), key=lambda item: item.id or 0, reverse=True)
    ]
    mark_perf("payments_rows")

    monthly_tax_totals = finalize_monthly_tax_totals(monthly_tax_raw_totals)

    dashboard = AdminDashboardRead(
        month=month_date,
        include_drafts=include_drafts,
        company_plan_amount=q(plan.company_plan_amount),
        company_fact_income_amount=q(company_fact),
        company_completion_percent=completion_percent(company_fact, money(plan.company_plan_amount)),
        company_expenses_amount=q(company_expenses),
        company_turnover_amount=monthly_tax_totals["turnover"],
        company_vat_to_pay_amount=monthly_tax_totals["vat_to_pay"],
        company_tax_to_pay_amount=monthly_tax_totals["tax_to_pay"],
        manager_personal_plan_amount=manager_personal_plan_amount(plan),
        departments=department_rows,
        events=event_rows,
        payment_requests=payment_rows,
        closing=build_closing(closing),
    )
    response = AdminDashboardBundleRead(dashboard=dashboard, event_payloads=event_payloads)
    mark_perf("response_model")

    items_count = len(active_items)
    requests_count = sum(len(event.payment_requests or []) for event in events)
    shares_count = sum(len(event.shares or []) for event in events)
    logger.warning(
        "PERF admin-dashboard-bundle month=%s include_drafts=%s events=%s items=%s requests=%s shares=%s users=%s expenses=%s "
        "base_sql=%.3fs events_sql=%.3fs paid_sync=%.3fs payloads=%.3fs departments_calc=%.3fs payments_rows=%.3fs response_model=%.3fs total=%.3fs",
        month,
        include_drafts,
        len(events),
        items_count,
        requests_count,
        shares_count,
        len(all_users),
        len(monthly_expenses),
        delta("parse", "base_sql"),
        delta("base_sql", "events_sql"),
        delta("events_sql", "paid_sync"),
        delta("paid_sync", "payloads"),
        delta("payloads", "departments_calc"),
        delta("departments_calc", "payments_rows"),
        delta("payments_rows", "response_model"),
        perf_marks["response_model"] - perf_total_started,
    )

    return response
