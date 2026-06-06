from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.monthly_expense import MonthlyExpense
from app.schemas.monthly_expense import (
    MonthlyExpenseCreate,
    MonthlyExpenseRead,
    MonthlyExpenseSummaryRead,
)


router = APIRouter(tags=["monthly_expenses"])


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


def calculate_allocation(payload: MonthlyExpenseCreate) -> tuple[Decimal, Decimal]:
    amount = money(payload.amount)
    allocation_type = payload.allocation_type

    if allocation_type == "default_split":
        sanzhar = q(amount * Decimal("2") / Decimal("3"))
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


@router.post("/monthly-expenses", response_model=MonthlyExpenseRead)
def create_monthly_expense(payload: MonthlyExpenseCreate, db: Session = Depends(get_db)):
    month = normalize_month(payload.month)
    sanzhar_amount, raufal_amount = calculate_allocation(payload)

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
    return expense


@router.get("/monthly-expenses", response_model=list[MonthlyExpenseRead])
def list_monthly_expenses(month: str | None = None, db: Session = Depends(get_db)):
    query = select(MonthlyExpense)

    if month:
        month_date = parse_month(month)
        query = query.where(
            extract("year", MonthlyExpense.month) == month_date.year,
            extract("month", MonthlyExpense.month) == month_date.month,
        )

    result = db.execute(query.order_by(MonthlyExpense.month.desc(), MonthlyExpense.id.desc()))
    return result.scalars().all()


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
    sanzhar = sum((money(expense.sanzhar_amount) for expense in expenses), Decimal("0.00"))
    raufal = sum((money(expense.raufal_amount) for expense in expenses), Decimal("0.00"))

    return MonthlyExpenseSummaryRead(
        month=month_date,
        total_amount=q(total),
        sanzhar_amount=q(sanzhar),
        raufal_amount=q(raufal),
        expenses_count=len(expenses),
    )
