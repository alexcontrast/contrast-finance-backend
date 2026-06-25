from datetime import date, datetime
import logging
import time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, select
from collections import defaultdict
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.event_share import EventShare
from app.models.monthly_closing import MonthlyClosing
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.models.user import User
from app.schemas.monthly_closing import MonthlyClosingCalculateRead, MonthlyClosingRead
from app.services.auth import require_roles
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["monthly_closings"])
logger = logging.getLogger("contrast.performance")


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


def get_department_by_name(db: Session, name: str) -> Department | None:
    return db.execute(select(Department).where(Department.name == name)).scalar_one_or_none()


def allocated_amount(value: Decimal, share_percent: Decimal) -> Decimal:
    return q(money(value) * money(share_percent) / Decimal("100"))


def get_department_income_amounts(db: Session, year: int, month: int) -> dict[int, Decimal]:
    """
    Fast department income calculation for closing.

    Before v0.40.55 closing calculated each department separately. That meant:
    - loading the same month's events twice;
    - loading items per event twice;
    - loading shares per event twice.

    With 40+ events this became the last slow part of the admin site. Here we load
    events, items, shares and users once, calculate every event once, then split
    income by the same event_shares rules.
    """
    events = db.execute(
        select(Event).where(
            extract("year", Event.event_date) == year,
            extract("month", Event.event_date) == month,
            Event.status != "cancelled",
        )
    ).scalars().all()

    if not events:
        return {}

    event_ids = [event.id for event in events]

    items = db.execute(
        select(EventItem)
        .where(
            EventItem.event_id.in_(event_ids),
            EventItem.is_deleted == False,  # noqa: E712
        )
        .order_by(EventItem.event_id, EventItem.sort_order, EventItem.id)
    ).scalars().all()
    items_by_event_id: dict[int, list[EventItem]] = defaultdict(list)
    for item in items:
        items_by_event_id[item.event_id].append(item)

    shares = db.execute(
        select(EventShare).where(EventShare.event_id.in_(event_ids))
    ).scalars().all()
    shares_by_event_id: dict[int, list[EventShare]] = defaultdict(list)
    for share in shares:
        shares_by_event_id[share.event_id].append(share)

    users = db.execute(select(User)).scalars().all()
    user_by_id = {user.id: user for user in users}

    incomes_by_department_id: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for event in events:
        values = calculate_event_summary_values(event, items_by_event_id.get(event.id, []))
        event_income = money(values["final_company_income"])
        event_shares = shares_by_event_id.get(event.id, [])

        if not event_shares:
            manager = user_by_id.get(event.manager_id)
            department_id = manager.department_id if manager and manager.department_id else event.department_id
            if department_id:
                incomes_by_department_id[department_id] += event_income
            continue

        for share in event_shares:
            manager = user_by_id.get(share.user_id)
            if manager and manager.department_id:
                incomes_by_department_id[manager.department_id] += allocated_amount(event_income, share.share_percent)

    return {department_id: q(income) for department_id, income in incomes_by_department_id.items()}


def get_department_income(db: Session, department_id: int, year: int, month: int) -> Decimal:
    # Kept for backward compatibility with older internal calls.
    return q(get_department_income_amounts(db, year, month).get(department_id, Decimal("0.00")))

def expense_default_split_amounts(expense: MonthlyExpense, plan: MonthlyPlan | None) -> tuple[Decimal, Decimal]:
    sanzhar_percent = money(plan.sanzhar_share_percent) if plan is not None else Decimal("66.67")
    sanzhar = q(money(expense.amount) * sanzhar_percent / Decimal("100"))
    return sanzhar, q(money(expense.amount) - sanzhar)


def get_department_expense_amounts(db: Session, month_date: date, plan: MonthlyPlan | None) -> dict[str, Decimal]:
    expenses = db.execute(
        select(MonthlyExpense).where(MonthlyExpense.month == month_date)
    ).scalars().all()

    totals = {"Санжар": Decimal("0.00"), "Рауфаль": Decimal("0.00")}

    for expense in expenses:
        if expense.allocation_type == "default_split":
            sanzhar_amount, raufal_amount = expense_default_split_amounts(expense, plan)
        else:
            sanzhar_amount, raufal_amount = money(expense.sanzhar_amount), money(expense.raufal_amount)

        totals["Санжар"] += sanzhar_amount
        totals["Рауфаль"] += raufal_amount

    return {name: q(amount) for name, amount in totals.items()}


def get_department_expenses(db: Session, department_name: str, year: int, month: int) -> Decimal:
    # Kept for backward compatibility with older internal calls.
    month_date = date(year, month, 1)
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    return q(get_department_expense_amounts(db, month_date, plan).get(department_name, Decimal("0.00")))

def head_percent(income: Decimal, plan: Decimal) -> Decimal:
    return Decimal("15.00") if income >= plan and plan > 0 else Decimal("10.00")


def head_salary(income: Decimal, expenses: Decimal, percent: Decimal) -> Decimal:
    base = income - expenses
    if base <= 0:
        return Decimal("0.00")
    return q(base * percent / Decimal("100"))


def calculate_closing(db: Session, month_date: date) -> MonthlyClosingCalculateRead:
    started_at = time.perf_counter()
    step_started_at = started_at
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    plan_s = time.perf_counter() - step_started_at
    if plan is None:
        logger.info("PERF monthly-closing-calculate month=%s error=no_plan plan_sql=%.3fs total=%.3fs", month_date, plan_s, time.perf_counter() - started_at)
        raise HTTPException(status_code=404, detail="Monthly plan not found")

    step_started_at = time.perf_counter()
    sanzhar = get_department_by_name(db, "Санжар")
    raufal = get_department_by_name(db, "Рауфаль")
    departments_s = time.perf_counter() - step_started_at

    if sanzhar is None or raufal is None:
        raise HTTPException(status_code=400, detail="Departments Санжар and Рауфаль must exist")

    step_started_at = time.perf_counter()
    sanzhar_plan = department_plan_amount(plan, "Санжар")
    raufal_plan = department_plan_amount(plan, "Рауфаль")
    plan_calc_s = time.perf_counter() - step_started_at

    step_started_at = time.perf_counter()
    incomes_by_department_id = get_department_income_amounts(db, month_date.year, month_date.month)
    incomes_s = time.perf_counter() - step_started_at
    sanzhar_income = incomes_by_department_id.get(sanzhar.id, Decimal("0.00"))
    raufal_income = incomes_by_department_id.get(raufal.id, Decimal("0.00"))

    step_started_at = time.perf_counter()
    expenses_by_department = get_department_expense_amounts(db, month_date, plan)
    expenses_s = time.perf_counter() - step_started_at
    sanzhar_expenses = expenses_by_department.get("Санжар", Decimal("0.00"))
    raufal_expenses = expenses_by_department.get("Рауфаль", Decimal("0.00"))

    sanzhar_completion = completion_percent(sanzhar_income, sanzhar_plan)
    raufal_completion = completion_percent(raufal_income, raufal_plan)

    sanzhar_head_pct = head_percent(sanzhar_income, sanzhar_plan)
    raufal_head_pct = head_percent(raufal_income, raufal_plan)

    sanzhar_head_salary = head_salary(sanzhar_income, sanzhar_expenses, sanzhar_head_pct)
    raufal_head_salary = head_salary(raufal_income, raufal_expenses, raufal_head_pct)

    sanzhar_remaining = q(sanzhar_income - sanzhar_expenses - sanzhar_head_salary)
    raufal_remaining = q(raufal_income - raufal_expenses - raufal_head_salary)

    founders_total = q(sanzhar_remaining + raufal_remaining)
    founder_amount = q(founders_total / Decimal("3"))

    response_started_at = time.perf_counter()
    response = MonthlyClosingCalculateRead(
        month=month_date,
        company_plan_amount=q(plan.company_plan_amount),

        sanzhar_plan_amount=q(sanzhar_plan),
        sanzhar_income_amount=q(sanzhar_income),
        sanzhar_expense_amount=q(sanzhar_expenses),
        sanzhar_completion_percent=q(sanzhar_completion),
        sanzhar_head_percent=q(sanzhar_head_pct),
        sanzhar_head_salary=q(sanzhar_head_salary),
        sanzhar_remaining_after_head=q(sanzhar_remaining),

        raufal_plan_amount=q(raufal_plan),
        raufal_income_amount=q(raufal_income),
        raufal_expense_amount=q(raufal_expenses),
        raufal_completion_percent=q(raufal_completion),
        raufal_head_percent=q(raufal_head_pct),
        raufal_head_salary=q(raufal_head_salary),
        raufal_remaining_after_head=q(raufal_remaining),

        founders_total_amount=q(founders_total),
        founder_one_amount=q(founder_amount),
        founder_two_amount=q(founder_amount),
        founder_three_amount=q(founder_amount),

        status="draft",
    )
    response_s = time.perf_counter() - response_started_at
    logger.info(
        "PERF monthly-closing-calculate month=%s plan_sql=%.3fs departments_sql=%.3fs plan_calc=%.3fs incomes=%.3fs expenses=%.3fs response=%.3fs total=%.3fs",
        month_date,
        plan_s,
        departments_s,
        plan_calc_s,
        incomes_s,
        expenses_s,
        response_s,
        time.perf_counter() - started_at,
    )
    return response


@router.get("/monthly-closings/calculate", response_model=MonthlyClosingCalculateRead)
def calculate_monthly_closing(
    month: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    month_date = parse_month(month)
    return calculate_closing(db, month_date)


@router.post("/monthly-closings/close", response_model=MonthlyClosingRead)
def close_month(
    month: str,
    closed_by_user_id: int | None = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    month_date = parse_month(month)
    calculated = calculate_closing(db, month_date)

    existing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()
    now = datetime.utcnow()

    if existing is None:
        closing = MonthlyClosing(
            month=month_date,
            created_at=now,
            updated_at=now,
        )
    else:
        closing = existing
        closing.updated_at = now

    closing.company_plan_amount = calculated.company_plan_amount

    closing.sanzhar_plan_amount = calculated.sanzhar_plan_amount
    closing.sanzhar_income_amount = calculated.sanzhar_income_amount
    closing.sanzhar_expense_amount = calculated.sanzhar_expense_amount
    closing.sanzhar_completion_percent = calculated.sanzhar_completion_percent
    closing.sanzhar_head_percent = calculated.sanzhar_head_percent
    closing.sanzhar_head_salary = calculated.sanzhar_head_salary
    closing.sanzhar_remaining_after_head = calculated.sanzhar_remaining_after_head

    closing.raufal_plan_amount = calculated.raufal_plan_amount
    closing.raufal_income_amount = calculated.raufal_income_amount
    closing.raufal_expense_amount = calculated.raufal_expense_amount
    closing.raufal_completion_percent = calculated.raufal_completion_percent
    closing.raufal_head_percent = calculated.raufal_head_percent
    closing.raufal_head_salary = calculated.raufal_head_salary
    closing.raufal_remaining_after_head = calculated.raufal_remaining_after_head

    closing.founders_total_amount = calculated.founders_total_amount
    closing.founder_one_amount = calculated.founder_one_amount
    closing.founder_two_amount = calculated.founder_two_amount
    closing.founder_three_amount = calculated.founder_three_amount

    closing.status = "closed"
    closing.closed_by_user_id = closed_by_user_id or current_admin.id
    closing.closed_at = now

    db.add(closing)
    db.commit()
    db.refresh(closing)
    return closing


@router.post("/monthly-closings/reopen", response_model=MonthlyClosingRead)
def reopen_month(
    month: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    month_date = parse_month(month)
    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()
    if closing is None:
        raise HTTPException(status_code=404, detail="Monthly closing not found")

    closing.status = "reopened"
    closing.closed_at = None
    closing.closed_by_user_id = None
    closing.updated_at = datetime.utcnow()

    db.add(closing)
    db.commit()
    db.refresh(closing)
    return closing


@router.get("/monthly-closings", response_model=list[MonthlyClosingRead])
def list_monthly_closings(db: Session = Depends(get_db)):
    return db.execute(select(MonthlyClosing).order_by(MonthlyClosing.month.desc())).scalars().all()


@router.get("/monthly-closings/by-month", response_model=MonthlyClosingRead)
def get_monthly_closing(month: str, db: Session = Depends(get_db)):
    month_date = parse_month(month)
    closing = db.execute(select(MonthlyClosing).where(MonthlyClosing.month == month_date)).scalar_one_or_none()
    if closing is None:
        raise HTTPException(status_code=404, detail="Monthly closing not found")
    return closing
