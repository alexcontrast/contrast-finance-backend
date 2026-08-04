from datetime import date
from decimal import Decimal
import logging
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.attributes import set_committed_value

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
    AdminEventPayloadsRead,
    AdminEventRowRead,
    AdminPaymentRequestRowRead,
)
from app.schemas.monthly_expense import ManagerBonusRead
from app.schemas.users_manage import UserRead as AdminUserRead
from app.services.event_calculator import calculate_event_summary_values, q, q0

from app.schemas.event import EventRead
from app.schemas.event_item import EventItemRead
from app.schemas.manager_dashboard import ManagerEventFullPayload
from app.api.routes.manager_dashboard import build_event_summary_read_for_bundle
from app.api.routes.monthly_closings import build_closing_calculation_from_totals
from app.api.routes.monthly_expenses import expense_to_read_with_plan
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


def next_month_start(month_date: date) -> date:
    if month_date.month == 12:
        return date(month_date.year + 1, 1, 1)
    return date(month_date.year, month_date.month + 1, 1)


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
    month_date = date(year, month, 1)
    expenses = db.execute(
        select(MonthlyExpense).where(MonthlyExpense.month == month_date)
    ).scalars().all()
    plan = db.execute(
        select(MonthlyPlan).where(MonthlyPlan.month == month_date)
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


def build_manager_bonus_reads(
    expenses: list[MonthlyExpense],
    user_by_id: dict[int, User],
    dept_by_id: dict[int, Department],
) -> list[ManagerBonusRead]:
    rows: list[ManagerBonusRead] = []
    for expense in expenses:
        if expense.source_type != "manager_bonus" or expense.manager_id is None:
            continue
        manager = user_by_id.get(expense.manager_id)
        if manager is None or manager.department_id is None:
            continue
        department = dept_by_id.get(manager.department_id)
        if department is None:
            continue
        rows.append(
            ManagerBonusRead(
                id=expense.id,
                month=expense.month,
                manager_id=manager.id,
                manager_name=manager.name,
                department_id=department.id,
                department_name=department.name,
                income_amount=q(expense.bonus_income_amount),
                bonus_percent=q(expense.bonus_percent or Decimal("5.00")),
                bonus_amount=q(expense.amount),
                paid_at=expense.created_at,
            )
        )
    return rows


def build_closing(closing: MonthlyClosing | None) -> AdminClosingRead:
    if closing is None:
        return AdminClosingRead(is_closed=False)

    return AdminClosingRead(
        is_closed=closing.status == "closed",
        status=closing.status,
        sanzhar_head_salary=closing.sanzhar_head_salary,
        sanzhar_head_percent_override=closing.sanzhar_head_percent_override,
        raufal_head_salary=closing.raufal_head_salary,
        raufal_head_percent_override=closing.raufal_head_percent_override,
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


def build_admin_user_reads(
    users: list[User],
    department_by_id: dict[int, Department],
) -> list[AdminUserRead]:
    return [
        AdminUserRead(
            id=user.id,
            name=user.name,
            phone=user.phone,
            department_id=user.department_id,
            department_name=(department_by_id.get(user.department_id).name if user.department_id in department_by_id else None),
            role=user.role,
            is_active=user.is_active,
            legacy_user_id=user.legacy_user_id,
            auth_source=user.auth_source or "legacy_apps_script",
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]


def active_items_for_events(events: list[Event]) -> list[EventItem]:
    return [
        item
        for event in events
        for item in (event.items or [])
        if item.is_deleted is False
    ]


def refresh_loaded_paid_amounts(db: Session, active_items: list[EventItem]) -> None:
    """Refresh paid_amount in memory with one aggregate query.

    The GET response needs current paid totals, but flushing these transient cache
    values caused UPDATE statements that were rolled back when the request session
    closed. Updating loaded objects in memory is sufficient for calculation and
    serialization and keeps the read path read-only.
    """
    item_ids = [int(item.id) for item in active_items if item.id is not None]
    if not item_ids:
        return

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
    for item in active_items:
        set_committed_value(item, "paid_amount", money(paid_totals.get(item.id, Decimal("0.00"))))





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
    stored_plan = plan
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
        select(MonthlyExpense).where(MonthlyExpense.month == month_date)
    ).scalars().all()
    department_expenses_by_name = build_department_expenses_by_name(monthly_expenses, plan)
    manager_bonuses = build_manager_bonus_reads(monthly_expenses, user_by_id, dept_by_id)
    mark_perf("base_sql")

    month_end = next_month_start(month_date)
    event_query = (
        select(Event)
        .options(
            selectinload(Event.items),
            selectinload(Event.payment_requests),
            selectinload(Event.shares),
        )
        .where(
            Event.event_date >= month_date,
            Event.event_date < month_end,
            Event.status != "cancelled",
        )
    )
    if not include_drafts:
        event_query = event_query.where(Event.status != "draft")

    events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().unique().all()
    mark_perf("events_sql")

    active_items = active_items_for_events(events)
    refresh_loaded_paid_amounts(db, active_items)
    mark_perf("paid_sync")

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

    payment_requests = sorted(
        [request for event in events for request in (event.payment_requests or [])],
        key=lambda request: request.id or 0,
        reverse=True,
    )

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
    department_by_name = {department.name: department for department in departments}
    sanzhar_department = department_by_name.get("Санжар")
    raufal_department = department_by_name.get("Рауфаль")
    closing_calculation = None
    if stored_plan is not None and sanzhar_department is not None and raufal_department is not None:
        closing_calculation = build_closing_calculation_from_totals(
            month_date=month_date,
            plan=stored_plan,
            sanzhar_income=department_fact_by_id.get(sanzhar_department.id, Decimal("0.00")),
            raufal_income=department_fact_by_id.get(raufal_department.id, Decimal("0.00")),
            sanzhar_expenses=department_expenses_by_name.get("Санжар", Decimal("0.00")),
            raufal_expenses=department_expenses_by_name.get("Рауфаль", Decimal("0.00")),
            closing_overrides=closing,
        )

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
        manager_bonuses=manager_bonuses,
        departments=department_rows,
        events=event_rows,
        payment_requests=payment_rows,
        closing=build_closing(closing),
        closing_calculation=closing_calculation,
    )
    mark_perf("response_model")

    def delta(start_name: str, end_name: str) -> float:
        return perf_marks[end_name] - perf_marks[start_name]

    # PERF admin-dashboard log removed in v0.5.6

    return dashboard


@router.get("/admin-dashboard-bundle", response_model=AdminDashboardBundleRead)
def get_admin_dashboard_bundle(
    month: str,
    include_drafts: bool = True,
    include_event_payloads: bool = True,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """Admin month payload.

    The initial admin screen requests the compact form and receives dashboard,
    users and closing data in one response. Full event modal payloads remain
    available for background prefetch and backward-compatible callers.
    """
    perf_total_started = perf_counter()
    perf_marks: dict[str, float] = {}

    def mark_perf(name: str) -> None:
        perf_marks[name] = perf_counter()

    def delta(start_name: str, end_name: str) -> float:
        return perf_marks[end_name] - perf_marks[start_name]

    month_date = parse_month(month)
    mark_perf("parse")

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    stored_plan = plan
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
        select(MonthlyExpense).where(MonthlyExpense.month == month_date)
    ).scalars().all()
    department_expenses_by_name = build_department_expenses_by_name(monthly_expenses, plan)
    manager_bonuses = build_manager_bonus_reads(monthly_expenses, user_by_id, dept_by_id)
    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()
    mark_perf("base_sql")

    month_end = next_month_start(month_date)
    event_query = (
        select(Event)
        .options(
            selectinload(Event.items),
            selectinload(Event.payment_requests),
            selectinload(Event.shares),
        )
        .where(
            Event.event_date >= month_date,
            Event.event_date < month_end,
            Event.status != "cancelled",
        )
    )
    if not include_drafts:
        event_query = event_query.where(Event.status != "draft")

    events = db.execute(event_query.order_by(Event.event_date, Event.id)).scalars().unique().all()
    mark_perf("events_sql")

    active_items = active_items_for_events(events)
    refresh_loaded_paid_amounts(db, active_items)
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

        if include_event_payloads:
            manager_name = user_by_id.get(event.manager_id).name if event.manager_id in user_by_id else None
            event_payloads[int(event.id)] = ManagerEventFullPayload(
                event=EventRead.model_validate(event),
                items=[EventItemRead.model_validate(item) for item in items],
                summary=build_event_summary_read_for_bundle(event, items, summary),
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

    department_by_name = {department.name: department for department in departments}
    sanzhar_department = department_by_name.get("Санжар")
    raufal_department = department_by_name.get("Рауфаль")
    closing_calculation = None
    if stored_plan is not None and sanzhar_department is not None and raufal_department is not None:
        closing_calculation = build_closing_calculation_from_totals(
            month_date=month_date,
            plan=stored_plan,
            sanzhar_income=department_fact_by_id.get(sanzhar_department.id, Decimal("0.00")),
            raufal_income=department_fact_by_id.get(raufal_department.id, Decimal("0.00")),
            sanzhar_expenses=department_expenses_by_name.get("Санжар", Decimal("0.00")),
            raufal_expenses=department_expenses_by_name.get("Рауфаль", Decimal("0.00")),
            closing_overrides=closing,
        )

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
        manager_bonuses=manager_bonuses,
        departments=department_rows,
        events=event_rows,
        payment_requests=payment_rows,
        closing=build_closing(closing),
        closing_calculation=closing_calculation,
    )
    response = AdminDashboardBundleRead(
        dashboard=dashboard,
        event_payloads=event_payloads,
        users=build_admin_user_reads(all_users, dept_by_id),
        monthly_expenses=[expense_to_read_with_plan(expense, stored_plan) for expense in monthly_expenses],
    )
    mark_perf("response_model")

    items_count = len(active_items)
    requests_count = sum(len(event.payment_requests or []) for event in events)
    shares_count = sum(len(event.shares or []) for event in events)
    # PERF admin-dashboard-bundle log removed in v0.5.6
    return response


def parse_event_ids_filter(raw_event_ids: str | None) -> list[int]:
    if not raw_event_ids:
        return []

    values: list[int] = []
    seen: set[int] = set()
    for raw_value in str(raw_event_ids).split(","):
        try:
            value = int(raw_value.strip())
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="event_ids must be comma-separated integers")
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


@router.get("/admin-event-payloads", response_model=AdminEventPayloadsRead)
def get_admin_event_payloads(
    month: str,
    event_ids: str | None = None,
    include_drafts: bool = True,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """Load full admin event cards separately from the first screen.

    The route is used for idle prefetch and for small live-sync refreshes. It
    deliberately avoids rebuilding plans, department totals, expenses and the
    payment-request table that the compact dashboard already supplied.
    """
    month_date = parse_month(month)
    selected_event_ids = parse_event_ids_filter(event_ids)

    month_end = next_month_start(month_date)
    query = (
        select(Event)
        .options(
            selectinload(Event.items),
            selectinload(Event.payment_requests),
        )
        .where(
            Event.event_date >= month_date,
            Event.event_date < month_end,
            Event.status != "cancelled",
        )
    )
    if not include_drafts:
        query = query.where(Event.status != "draft")
    if selected_event_ids:
        query = query.where(Event.id.in_(selected_event_ids))

    events = db.execute(query.order_by(Event.event_date, Event.id)).scalars().unique().all()
    manager_ids = {event.manager_id for event in events if event.manager_id is not None}
    managers = db.execute(select(User).where(User.id.in_(manager_ids))).scalars().all() if manager_ids else []
    manager_name_by_id = {manager.id: manager.name for manager in managers}

    active_items = active_items_for_events(events)
    refresh_loaded_paid_amounts(db, active_items)

    payloads: dict[int, ManagerEventFullPayload] = {}
    for event in events:
        items = sorted(
            [item for item in (event.items or []) if item.is_deleted is False],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )
        summary_values = calculate_event_summary_values(event, items)
        event_payment_requests = sorted(
            list(event.payment_requests or []),
            key=lambda request: request.id or 0,
            reverse=True,
        )
        payloads[int(event.id)] = ManagerEventFullPayload(
            event=EventRead.model_validate(event),
            items=[EventItemRead.model_validate(item) for item in items],
            summary=build_event_summary_read_for_bundle(event, items, summary_values),
            requests=[
                enrich_payment_request_read_fast(
                    request,
                    event.client_name,
                    event.title,
                    event.event_date,
                    manager_name_by_id.get(event.manager_id),
                )
                for request in event_payment_requests
            ],
        )

    return AdminEventPayloadsRead(month=month_date, event_payloads=payloads)
