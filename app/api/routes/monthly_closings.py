from datetime import date, datetime
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
from app.schemas.monthly_closing import MonthlyClosingCalculateRead, MonthlyClosingRead
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["monthly_closings"])


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


def get_department_income(db: Session, department_id: int, year: int, month: int) -> Decimal:
    # Month closing excludes cancelled events and includes drafts by current agreed dashboard default.
    events = db.execute(
        select(Event).where(
            Event.department_id == department_id,
            extract("year", Event.event_date) == year,
            extract("month", Event.event_date) == month,
            Event.status != "cancelled",
        )
    ).scalars().all()

    income = Decimal("0.00")

    for event in events:
        items = db.execute(
            select(EventItem)
            .where(EventItem.event_id == event.id, EventItem.is_deleted == False)  # noqa: E712
            .order_by(EventItem.sort_order, EventItem.id)
        ).scalars().all()

        values = calculate_event_summary_values(event, items)
        income += money(values["final_company_income"])

    return q(income)


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


def head_percent(income: Decimal, plan: Decimal) -> Decimal:
    return Decimal("15.00") if income >= plan and plan > 0 else Decimal("10.00")


def head_salary(income: Decimal, expenses: Decimal, percent: Decimal) -> Decimal:
    base = income - expenses
    if base <= 0:
        return Decimal("0.00")
    return q(base * percent / Decimal("100"))


def calculate_closing(db: Session, month_date: date) -> MonthlyClosingCalculateRead:
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Monthly plan not found")

    sanzhar = get_department_by_name(db, "Санжар")
    raufal = get_department_by_name(db, "Рауфаль")

    if sanzhar is None or raufal is None:
        raise HTTPException(status_code=400, detail="Departments Санжар and Рауфаль must exist")

    sanzhar_plan = department_plan_amount(plan, "Санжар")
    raufal_plan = department_plan_amount(plan, "Рауфаль")

    sanzhar_income = get_department_income(db, sanzhar.id, month_date.year, month_date.month)
    raufal_income = get_department_income(db, raufal.id, month_date.year, month_date.month)

    sanzhar_expenses = get_department_expenses(db, "Санжар", month_date.year, month_date.month)
    raufal_expenses = get_department_expenses(db, "Рауфаль", month_date.year, month_date.month)

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

    return MonthlyClosingCalculateRead(
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


@router.get("/monthly-closings/calculate", response_model=MonthlyClosingCalculateRead)
def calculate_monthly_closing(month: str, db: Session = Depends(get_db)):
    month_date = parse_month(month)
    return calculate_closing(db, month_date)


@router.post("/monthly-closings/close", response_model=MonthlyClosingRead)
def close_month(month: str, closed_by_user_id: int, db: Session = Depends(get_db)):
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
    closing.closed_by_user_id = closed_by_user_id
    closing.closed_at = now

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
