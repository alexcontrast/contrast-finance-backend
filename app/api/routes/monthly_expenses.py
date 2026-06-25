from datetime import date, datetime
import logging
import time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.schemas.monthly_expense import (
    MonthlyExpenseCreate,
    MonthlyExpenseRead,
    MonthlyExpenseSummaryRead,
    MonthlyExpenseUpdate,
)


router = APIRouter(tags=["monthly_expenses"])
logger = logging.getLogger("contrast.performance")


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q(value: Decimal) -> Decimal:
    return money(value).quantize(Decimal("0.01"))


def normalize_month(month: date) -> date:
    return month.replace(day=1)


def parse_month(month: str) -> date:
    try:
        parts = [int(part) for part in month.split("-")]
        return date(parts[0], parts[1], 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM or YYYY-MM-DD") from exc


def default_split_percentages(db: Session, month: date) -> tuple[Decimal, Decimal]:
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month)).scalar_one_or_none()
    if plan is None:
        return Decimal("66.67"), Decimal("33.33")

    sanzhar_percent = money(plan.sanzhar_share_percent)
    raufal_percent = money(plan.raufal_share_percent)

    if sanzhar_percent < 0 or raufal_percent < 0 or q(sanzhar_percent + raufal_percent) == Decimal("0.00"):
        return Decimal("66.67"), Decimal("33.33")

    return sanzhar_percent, raufal_percent


def calculate_allocation(payload: MonthlyExpenseCreate, db: Session, month: date) -> tuple[Decimal, Decimal]:
    amount = money(payload.amount)
    allocation_type = payload.allocation_type

    if allocation_type == "default_split":
        sanzhar_percent, _ = default_split_percentages(db, month)
        sanzhar = q(amount * sanzhar_percent / Decimal("100"))
        raufal = q(amount - sanzhar)
        return sanzhar, raufal

    if allocation_type == "sanzhar_only":
        return q(amount), Decimal("0.00")

    if allocation_type == "raufal_only":
        return Decimal("0.00"), q(amount)

    if allocation_type == "custom":
        sanzhar = q(money(payload.sanzhar_amount))
        raufal = q(money(payload.raufal_amount))
        if q(sanzhar + raufal) != q(amount):
            raise HTTPException(
                status_code=400,
                detail="Для custom сумма sanzhar_amount + raufal_amount должна равняться amount",
            )
        return sanzhar, raufal

    raise HTTPException(
        status_code=400,
        detail="allocation_type должен быть default_split, sanzhar_only, raufal_only или custom",
    )


def allocated_amounts_for_expense(db: Session, expense: MonthlyExpense) -> tuple[Decimal, Decimal]:
    if expense.allocation_type == "default_split":
        sanzhar_percent, _ = default_split_percentages(db, normalize_month(expense.month))
        sanzhar = q(money(expense.amount) * sanzhar_percent / Decimal("100"))
        return sanzhar, q(money(expense.amount) - sanzhar)

    return q(money(expense.sanzhar_amount)), q(money(expense.raufal_amount))


def allocated_amounts_for_expense_with_plan(expense: MonthlyExpense, plan: MonthlyPlan | None) -> tuple[Decimal, Decimal]:
    """Fast allocation for list endpoints: avoid one MonthlyPlan query per expense."""
    if expense.allocation_type == "default_split":
        sanzhar_percent = money(plan.sanzhar_share_percent) if plan is not None else Decimal("66.67")
        sanzhar = q(money(expense.amount) * sanzhar_percent / Decimal("100"))
        return sanzhar, q(money(expense.amount) - sanzhar)

    return q(money(expense.sanzhar_amount)), q(money(expense.raufal_amount))


def expense_to_read_with_plan(expense: MonthlyExpense, plan: MonthlyPlan | None) -> MonthlyExpenseRead:
    sanzhar_amount, raufal_amount = allocated_amounts_for_expense_with_plan(expense, plan)
    return MonthlyExpenseRead(
        id=expense.id,
        month=expense.month,
        title=expense.title,
        amount=expense.amount,
        allocation_type=expense.allocation_type,
        sanzhar_amount=sanzhar_amount,
        raufal_amount=raufal_amount,
        comment=expense.comment,
        created_by_user_id=expense.created_by_user_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


def calculate_allocation_for_existing_amount(
    expense: MonthlyExpense,
    db: Session,
    new_amount: Decimal,
) -> tuple[Decimal, Decimal]:
    amount = q(new_amount)

    if amount <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="amount must be greater than zero")

    if expense.allocation_type == "default_split":
        sanzhar_percent, _ = default_split_percentages(db, normalize_month(expense.month))
        sanzhar = q(amount * sanzhar_percent / Decimal("100"))
        return sanzhar, q(amount - sanzhar)

    if expense.allocation_type == "sanzhar_only":
        return amount, Decimal("0.00")

    if expense.allocation_type == "raufal_only":
        return Decimal("0.00"), amount

    if expense.allocation_type == "custom":
        old_sanzhar = money(expense.sanzhar_amount)
        old_raufal = money(expense.raufal_amount)
        old_total = q(old_sanzhar + old_raufal)

        if old_total <= Decimal("0.00"):
            sanzhar_percent, _ = default_split_percentages(db, normalize_month(expense.month))
            sanzhar = q(amount * sanzhar_percent / Decimal("100"))
            return sanzhar, q(amount - sanzhar)

        sanzhar = q(amount * old_sanzhar / old_total)
        return sanzhar, q(amount - sanzhar)

    raise HTTPException(
        status_code=400,
        detail="allocation_type должен быть default_split, sanzhar_only, raufal_only или custom",
    )

def expense_to_read(db: Session, expense: MonthlyExpense) -> MonthlyExpenseRead:
    sanzhar_amount, raufal_amount = allocated_amounts_for_expense(db, expense)
    return MonthlyExpenseRead(
        id=expense.id,
        month=expense.month,
        title=expense.title,
        amount=expense.amount,
        allocation_type=expense.allocation_type,
        sanzhar_amount=sanzhar_amount,
        raufal_amount=raufal_amount,
        comment=expense.comment,
        created_by_user_id=expense.created_by_user_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.post("/monthly-expenses", response_model=MonthlyExpenseRead)
def create_monthly_expense(payload: MonthlyExpenseCreate, db: Session = Depends(get_db)):
    month = normalize_month(payload.month)
    sanzhar_amount, raufal_amount = calculate_allocation(payload, db, month)

    expense = MonthlyExpense(
        month=month,
        title=payload.title,
        amount=payload.amount,
        allocation_type=payload.allocation_type,
        sanzhar_amount=sanzhar_amount,
        raufal_amount=raufal_amount,
        comment=payload.comment,
        created_by_user_id=payload.created_by_user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense_to_read(db, expense)


@router.get("/monthly-expenses", response_model=list[MonthlyExpenseRead])
def list_monthly_expenses(month: str | None = None, db: Session = Depends(get_db)):
    started_at = time.perf_counter()
    month_date = parse_month(month) if month else None

    query_started_at = started_at
    query = select(MonthlyExpense)

    if month_date:
        # MonthlyExpense.month is normalized to the first day of the month, so an equality
        # filter is enough and lets PostgreSQL use a normal index if one exists.
        query = query.where(MonthlyExpense.month == month_date)

    result = db.execute(query.order_by(MonthlyExpense.month.desc(), MonthlyExpense.id.desc()))
    expenses = result.scalars().all()
    query_s = time.perf_counter() - query_started_at

    plan_started_at = time.perf_counter()
    plans_by_month: dict[date, MonthlyPlan | None] = {}
    if month_date:
        plans_by_month[month_date] = db.execute(
            select(MonthlyPlan).where(MonthlyPlan.month == month_date)
        ).scalar_one_or_none()
    else:
        unique_months = {normalize_month(expense.month) for expense in expenses}
        if unique_months:
            plans = db.execute(select(MonthlyPlan).where(MonthlyPlan.month.in_(unique_months))).scalars().all()
            plans_by_month = {plan.month: plan for plan in plans}
            for expense_month in unique_months:
                plans_by_month.setdefault(expense_month, None)
    plan_s = time.perf_counter() - plan_started_at

    response_started_at = time.perf_counter()
    response = [
        expense_to_read_with_plan(expense, plans_by_month.get(normalize_month(expense.month)))
        for expense in expenses
    ]
    response_s = time.perf_counter() - response_started_at
    logger.info(
        "PERF monthly-expenses month=%s count=%s query=%.3fs plan=%.3fs response=%.3fs total=%.3fs",
        month,
        len(response),
        query_s,
        plan_s,
        response_s,
        time.perf_counter() - started_at,
    )
    return response


@router.get("/monthly-expenses/summary", response_model=MonthlyExpenseSummaryRead)
def get_monthly_expenses_summary(month: str, db: Session = Depends(get_db)):
    month_date = parse_month(month)

    expenses = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == month_date.year,
            extract("month", MonthlyExpense.month) == month_date.month,
        )
    ).scalars().all()

    total = sum((money(expense.amount) for expense in expenses), Decimal("0.00"))
    allocated = [allocated_amounts_for_expense(db, expense) for expense in expenses]
    sanzhar = sum((amounts[0] for amounts in allocated), Decimal("0.00"))
    raufal = sum((amounts[1] for amounts in allocated), Decimal("0.00"))

    return MonthlyExpenseSummaryRead(
        month=month_date,
        total_amount=q(total),
        sanzhar_amount=q(sanzhar),
        raufal_amount=q(raufal),
        expenses_count=len(expenses),
    )


@router.patch("/monthly-expenses/{expense_id}", response_model=MonthlyExpenseRead)
def update_monthly_expense(expense_id: int, payload: MonthlyExpenseUpdate, db: Session = Depends(get_db)):
    expense = db.get(MonthlyExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    new_amount = q(money(payload.amount))
    sanzhar_amount, raufal_amount = calculate_allocation_for_existing_amount(expense, db, new_amount)

    expense.amount = new_amount
    expense.sanzhar_amount = sanzhar_amount
    expense.raufal_amount = raufal_amount
    expense.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(expense)
    return expense_to_read(db, expense)


@router.delete("/monthly-expenses/{expense_id}")
def delete_monthly_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(MonthlyExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    deleted = {
        "id": expense.id,
        "ok": True,
    }
    db.delete(expense)
    db.commit()
    return deleted
