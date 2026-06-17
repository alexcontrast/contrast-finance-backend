from datetime import date
from decimal import Decimal
import logging
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.department import Department
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.event_share import EventShare
from app.models.monthly_plan import MonthlyPlan
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.manager_dashboard import ManagerDashboardBundleRead, ManagerDashboardEventRead, ManagerDashboardRead, ManagerEventFullPayload

from app.schemas.event import EventRead
from app.schemas.event_item import EventItemRead
from app.schemas.event_summary import EventSummaryRead
from app.schemas.payment_request import PaymentRequestRead
from app.services.payment_totals import sync_event_paid_amounts_from_requests
from app.api.routes.payment_requests import enrich_payment_request_read_fast
from app.services.auth import get_current_user
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["manager_dashboard"])
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


def event_share_percent_for_manager(event: Event, manager: User) -> Decimal:
    shares = list(event.shares or [])
    if not shares:
        return Decimal("100.00") if event.manager_id == manager.id else Decimal("0.00")

    for share in shares:
        if share.user_id == manager.id:
            return money(share.share_percent)

    return Decimal("0.00")


def coauthor_info(event: Event, manager: User, user_by_id: dict[int, User]) -> tuple[bool, str | None, int | None, int | None, str | None]:
    shares = list(event.shares or [])
    if not shares:
        owner = user_by_id.get(event.manager_id)
        return False, None, None, event.manager_id, owner.name if owner else None

    share_user_ids = [share.user_id for share in shares]
    other_ids = [user_id for user_id in share_user_ids if user_id != manager.id]
    other_id = other_ids[0] if other_ids else None
    other_user = user_by_id.get(other_id) if other_id else None
    owner = user_by_id.get(event.manager_id)
    return True, other_user.name if other_user else None, other_id, event.manager_id, owner.name if owner else None


@router.get("/manager-dashboard", response_model=ManagerDashboardRead)
def get_manager_dashboard(
    month: str,
    include_drafts: bool = True,
    manager_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perf_total_started = perf_counter()
    perf_marks: dict[str, float] = {"start": perf_total_started}

    def mark_perf(name: str) -> None:
        perf_marks[name] = perf_counter()

    month_date = parse_month(month)
    manager = resolve_manager(db, current_user, manager_id)
    mark_perf("parse")

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    # Кабинет менеджера не должен падать, если на выбранный месяц ещё не задан план.
    # В этом случае показываем пустой/нулевой план и всё равно отдаём список мероприятий.
    if plan is None:
        plan = MonthlyPlan(
            month=month_date,
            company_plan_amount=Decimal("0.00"),
            sanjar_department_plan_amount=Decimal("0.00"),
            raufal_department_plan_amount=Decimal("0.00"),
            created_at=None,
            updated_at=None,
        )

    department = db.get(Department, manager.department_id) if manager.department_id else None
    mark_perf("base_sql")

    shared_event_ids = select(EventShare.event_id).where(EventShare.user_id == manager.id)
    query = (
        select(Event)
        .options(
            selectinload(Event.items),
            selectinload(Event.payment_requests),
            selectinload(Event.shares),
        )
        .where(
            or_(Event.manager_id == manager.id, Event.id.in_(shared_event_ids)),
            extract("year", Event.event_date) == month_date.year,
            extract("month", Event.event_date) == month_date.month,
            Event.status != "cancelled",
        )
    )

    if not include_drafts:
        query = query.where(Event.status != "draft")

    events = db.execute(query.order_by(Event.event_date, Event.id)).scalars().unique().all()
    mark_perf("events_sql")

    needed_user_ids = {manager.id}
    for event in events:
        if event.manager_id:
            needed_user_ids.add(event.manager_id)
        for share in (event.shares or []):
            if share.user_id:
                needed_user_ids.add(share.user_id)

    if needed_user_ids:
        users = db.execute(select(User).where(User.id.in_(needed_user_ids))).scalars().all()
    else:
        users = []
    user_by_id = {user.id: user for user in users}
    mark_perf("users_sql")

    event_rows: list[ManagerDashboardEventRead] = []
    fact_income = Decimal("0.00")
    drafts_count = 0
    payment_requests_total = 0
    active_payment_requests_total = 0

    for event in events:
        if event.status == "draft":
            drafts_count += 1

        items = sorted(
            [item for item in (event.items or []) if item.is_deleted is False],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )

        summary = calculate_event_summary_values(event, items)
        full_final_income = money(summary["final_company_income"])
        share_percent = event_share_percent_for_manager(event, manager)
        manager_final_income = q(full_final_income * share_percent / Decimal("100"))

        fact_income += manager_final_income

        payment_requests = list(event.payment_requests or [])

        requests_count = len(payment_requests)
        active_requests_count = len([
            request for request in payment_requests
            if request.status not in INACTIVE_PAYMENT_STATUSES
        ])

        payment_requests_total += requests_count
        active_payment_requests_total += active_requests_count

        is_coauthored, coauthor_name, coauthor_user_id, owner_manager_id, owner_manager_name = coauthor_info(event, manager, user_by_id)

        event_rows.append(
            ManagerDashboardEventRead(
                id=event.id,
                client_name=event.client_name,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                money_status=getattr(event, "money_status", "waiting_money"),
                external_total=q(money(summary["external_total"])),
                fact_total=q(money(summary["fact_total"])),
                paid_total=q(money(summary["paid_total"])),
                final_company_income=q(manager_final_income),
                manager_salary=q(money(summary["manager_salary"]) * share_percent / Decimal("100")),
                payment_requests_count=requests_count,
                active_payment_requests_count=active_requests_count,
                share_percent=q(share_percent),
                is_coauthored=is_coauthored,
                coauthor_name=coauthor_name,
                coauthor_user_id=coauthor_user_id,
                owner_manager_id=owner_manager_id,
                owner_manager_name=owner_manager_name,
            )
        )

    mark_perf("events_calc")
    personal_plan = manager_personal_plan_amount(plan)

    dashboard = ManagerDashboardRead(
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
    mark_perf("response_model")

    def delta(start_name: str, end_name: str) -> float:
        return perf_marks[end_name] - perf_marks[start_name]

    items_count = sum(len([item for item in (event.items or []) if item.is_deleted is False]) for event in events)
    requests_count = sum(len(event.payment_requests or []) for event in events)
    shares_count = sum(len(event.shares or []) for event in events)

    logger.warning(
        "PERF manager-dashboard month=%s include_drafts=%s manager_id=%s events=%s items=%s requests=%s shares=%s users=%s "
        "base_sql=%.3fs events_sql=%.3fs users_sql=%.3fs events_calc=%.3fs response_model=%.3fs total=%.3fs",
        month,
        include_drafts,
        manager.id,
        len(events),
        items_count,
        requests_count,
        shares_count,
        len(users),
        delta("parse", "base_sql"),
        delta("base_sql", "events_sql"),
        delta("events_sql", "users_sql"),
        delta("users_sql", "events_calc"),
        delta("events_calc", "response_model"),
        perf_marks["response_model"] - perf_total_started,
    )

    return dashboard


def build_event_summary_read_for_bundle(event: Event, items: list[EventItem]) -> EventSummaryRead:
    values = calculate_event_summary_values(event, items)
    customer_paid = getattr(event, "customer_paid_amount", Decimal("0.00")) or Decimal("0.00")

    return EventSummaryRead(
        event_id=event.id,
        client_name=event.client_name,
        title=event.title,
        status=event.status,
        client_calc_type=event.client_calc_type,

        external_total=q(values["external_total"]),
        fact_total=q(values["fact_total"]),
        paid_total=q(values["paid_total"]),
        customer_paid_amount=q(customer_paid),
        customer_remaining_amount=q(max(Decimal("0.00"), values["turnover_with_vat"] - customer_paid)),

        regular_external_total=q(values["regular_external_total"]),
        regular_fact_total=q(values["regular_fact_total"]),

        coordinator_external_total=q(values["coordinator_external_total"]),
        coordinator_fact_amount=q(values["coordinator_fact_amount"]),
        coordinator_company_share=q(values["coordinator_company_share"]),

        vat_total=q(values["vat_total"]),
        deductions_total=q(values["deductions_total"]),

        internal_tax_amount=q(values["internal_tax_amount"]),
        simplified_bank_tax_amount=q(values["simplified_bank_tax_amount"]),

        manager_salary_base=q(values["manager_salary_base"]),
        manager_percent=q(values["manager_percent"]),
        manager_salary=q(values["manager_salary"]),
        manager_salary_paid=q(values["manager_salary_paid"]),

        company_income_before_manager_salary=q(values["company_income_before_manager_salary"]),
        company_income_after_manager_salary=q(values["company_income_after_manager_salary"]),
        final_company_income=q(values["final_company_income"]),

        turnover_with_vat=q(values["turnover_with_vat"]),
        client_vat_amount=q(values["client_vat_amount"]),
        contractor_vat_credit=q(values["contractor_vat_credit"]),
        vat_to_pay=q(values["vat_to_pay"]),
        tax_rate_percent=q(values["tax_rate_percent"]),
        tax_base_amount=q(values["tax_base_amount"]),
        taxes_total=q(values["taxes_total"]),
    )


@router.get("/manager-dashboard-bundle", response_model=ManagerDashboardBundleRead)
def get_manager_dashboard_bundle(
    month: str,
    include_drafts: bool = True,
    manager_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Optimized manager cabinet payload.

    Returns the month dashboard, month payment requests and full event payloads
    in one response, but avoids the old double work pattern where the regular
    manager dashboard was built first and then all events were loaded again.
    """
    perf_total_started = perf_counter()
    perf_marks: dict[str, float] = {"start": perf_total_started}

    def mark_perf(name: str) -> None:
        perf_marks[name] = perf_counter()

    def delta(start_name: str, end_name: str) -> float:
        return perf_marks[end_name] - perf_marks[start_name]

    month_date = parse_month(month)
    manager = resolve_manager(db, current_user, manager_id)
    mark_perf("parse")

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        plan = MonthlyPlan(
            month=month_date,
            company_plan_amount=Decimal("0.00"),
            sanjar_department_plan_amount=Decimal("0.00"),
            raufal_department_plan_amount=Decimal("0.00"),
            created_at=None,
            updated_at=None,
        )
    department = db.get(Department, manager.department_id) if manager.department_id else None
    mark_perf("base_sql")

    shared_event_ids = select(EventShare.event_id).where(EventShare.user_id == manager.id)
    query = (
        select(Event)
        .options(
            selectinload(Event.items),
            selectinload(Event.payment_requests),
            selectinload(Event.shares),
        )
        .where(
            or_(Event.manager_id == manager.id, Event.id.in_(shared_event_ids)),
            extract("year", Event.event_date) == month_date.year,
            extract("month", Event.event_date) == month_date.month,
            Event.status != "cancelled",
        )
    )
    if not include_drafts:
        query = query.where(Event.status != "draft")

    events = db.execute(query.order_by(Event.event_date, Event.id)).scalars().unique().all()
    mark_perf("events_sql")

    # Refresh denormalized paid_amount values for all loaded items in one batch.
    # Source of truth remains payment_requests.status == paid, but the UI uses
    # EventItem.paid_amount in summaries and estimates.
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

    needed_user_ids = {manager.id}
    for event in events:
        if event.manager_id:
            needed_user_ids.add(event.manager_id)
        for share in (event.shares or []):
            if share.user_id:
                needed_user_ids.add(share.user_id)

    users = db.execute(select(User).where(User.id.in_(needed_user_ids))).scalars().all() if needed_user_ids else []
    user_by_id = {user.id: user for user in users}
    mark_perf("users_sql")

    event_rows: list[ManagerDashboardEventRead] = []
    fact_income = Decimal("0.00")
    drafts_count = 0
    payment_requests_total = 0
    active_payment_requests_total = 0
    event_payloads: dict[int, ManagerEventFullPayload] = {}
    payment_requests_by_id: dict[int, PaymentRequestRead] = {}

    for event in events:
        if event.status == "draft":
            drafts_count += 1

        items = sorted(
            [item for item in (event.items or []) if item.is_deleted is False],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )
        summary_values = calculate_event_summary_values(event, items)
        full_final_income = money(summary_values["final_company_income"])
        share_percent = event_share_percent_for_manager(event, manager)
        manager_final_income = q(full_final_income * share_percent / Decimal("100"))
        fact_income += manager_final_income

        payment_requests = sorted(list(event.payment_requests or []), key=lambda request: request.id or 0, reverse=True)
        requests_count = len(payment_requests)
        active_requests_count = len([
            request for request in payment_requests
            if request.status not in INACTIVE_PAYMENT_STATUSES
        ])
        payment_requests_total += requests_count
        active_payment_requests_total += active_requests_count

        is_coauthored, coauthor_name, coauthor_user_id, owner_manager_id, owner_manager_name = coauthor_info(event, manager, user_by_id)
        event_rows.append(
            ManagerDashboardEventRead(
                id=event.id,
                client_name=event.client_name,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                money_status=getattr(event, "money_status", "waiting_money"),
                external_total=q(money(summary_values["external_total"])),
                fact_total=q(money(summary_values["fact_total"])),
                paid_total=q(money(summary_values["paid_total"])),
                final_company_income=q(manager_final_income),
                manager_salary=q(money(summary_values["manager_salary"]) * share_percent / Decimal("100")),
                payment_requests_count=requests_count,
                active_payment_requests_count=active_requests_count,
                share_percent=q(share_percent),
                is_coauthored=is_coauthored,
                coauthor_name=coauthor_name,
                coauthor_user_id=coauthor_user_id,
                owner_manager_id=owner_manager_id,
                owner_manager_name=owner_manager_name,
            )
        )

        manager_name = user_by_id.get(event.manager_id).name if event.manager_id in user_by_id else None
        request_reads = [
            enrich_payment_request_read_fast(request, event.client_name, event.title, manager_name)
            for request in payment_requests
        ]
        for request_read in request_reads:
            payment_requests_by_id[int(request_read.id)] = request_read

        event_payloads[int(event.id)] = ManagerEventFullPayload(
            event=EventRead.model_validate(event),
            items=[EventItemRead.model_validate(item) for item in items],
            summary=build_event_summary_read_for_bundle(event, items),
            requests=request_reads,
        )
    mark_perf("payloads")

    personal_plan = manager_personal_plan_amount(plan)
    dashboard = ManagerDashboardRead(
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
    payment_requests = sorted(payment_requests_by_id.values(), key=lambda request: request.id, reverse=True)
    response = ManagerDashboardBundleRead(
        dashboard=dashboard,
        payment_requests=payment_requests,
        event_payloads=event_payloads,
    )
    mark_perf("response_model")

    items_count = len(active_items)
    requests_count = sum(len(event.payment_requests or []) for event in events)
    shares_count = sum(len(event.shares or []) for event in events)
    logger.warning(
        "PERF manager-dashboard-bundle month=%s include_drafts=%s manager_id=%s events=%s items=%s requests=%s shares=%s users=%s "
        "base_sql=%.3fs events_sql=%.3fs paid_sync=%.3fs users_sql=%.3fs payloads=%.3fs response_model=%.3fs total=%.3fs",
        month,
        include_drafts,
        manager.id,
        len(events),
        items_count,
        requests_count,
        shares_count,
        len(users),
        delta("parse", "base_sql"),
        delta("base_sql", "events_sql"),
        delta("events_sql", "paid_sync"),
        delta("paid_sync", "users_sql"),
        delta("users_sql", "payloads"),
        delta("payloads", "response_model"),
        perf_marks["response_model"] - perf_total_started,
    )

    return response
