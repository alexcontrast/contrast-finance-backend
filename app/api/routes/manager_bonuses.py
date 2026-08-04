from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.routes.monthly_closings import apply_calculated_to_closing, calculate_closing
from app.db.session import get_db
from app.models.monthly_closing import MonthlyClosing
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.models.user import User
from app.schemas.monthly_expense import ManagerBonusRead
from app.services.auth import require_roles
from app.services.manager_bonus import MANAGER_BONUS_PERCENT, manager_bonus_amount, manager_income_for_month


router = APIRouter(tags=["manager_bonuses"])


def q(value) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def parse_month(month: str) -> date:
    try:
        year, month_number = [int(part) for part in str(month).split("-")[:2]]
        return date(year, month_number, 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM") from exc


def bonus_to_read(expense: MonthlyExpense, manager: User) -> ManagerBonusRead:
    department = manager.department
    return ManagerBonusRead(
        id=expense.id,
        month=expense.month,
        manager_id=manager.id,
        manager_name=manager.name,
        department_id=manager.department_id,
        department_name=department.name if department else "",
        income_amount=q(expense.bonus_income_amount),
        bonus_percent=q(expense.bonus_percent or MANAGER_BONUS_PERCENT),
        bonus_amount=q(expense.amount),
        paid_at=expense.created_at,
    )


def existing_bonus(db: Session, manager_id: int, month: date) -> MonthlyExpense | None:
    return db.execute(
        select(MonthlyExpense).where(
            MonthlyExpense.source_type == "manager_bonus",
            MonthlyExpense.manager_id == manager_id,
            MonthlyExpense.month == month,
        )
    ).scalar_one_or_none()


@router.post("/manager-bonuses/{manager_id}/pay", response_model=ManagerBonusRead)
def pay_manager_bonus(
    manager_id: int,
    month: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    month_date = parse_month(month)
    manager = db.execute(
        select(User).options(selectinload(User.department)).where(User.id == manager_id)
    ).scalar_one_or_none()
    if manager is None:
        raise HTTPException(status_code=404, detail="Менеджер не найден")
    if manager.role != "manager":
        raise HTTPException(status_code=400, detail="Бонус можно выплатить только менеджеру")
    if manager.department is None or manager.department.name not in {"Санжар", "Рауфаль"}:
        raise HTTPException(status_code=400, detail="У менеджера не указан отдел Санжар или Рауфаль")

    paid = existing_bonus(db, manager.id, month_date)
    if paid is not None:
        return bonus_to_read(paid, manager)

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=400, detail="На выбранный месяц не задан план")

    personal_plan = q(q(plan.company_plan_amount) * q(plan.manager_personal_plan_percent) / Decimal("100"))
    if personal_plan <= 0:
        raise HTTPException(status_code=400, detail="Личный план менеджера за выбранный месяц равен нулю")

    income_amount = manager_income_for_month(db, manager.id, month_date)
    if income_amount < personal_plan:
        raise HTTPException(
            status_code=400,
            detail=f"План ещё не выполнен: доход {income_amount}, план {personal_plan}",
        )

    bonus_amount = manager_bonus_amount(income_amount)
    if bonus_amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма бонуса должна быть больше нуля")

    now = datetime.utcnow()
    is_sanzhar = manager.department.name == "Санжар"
    expense = MonthlyExpense(
        month=month_date,
        title=f"Бонус менеджера — {manager.name}",
        amount=bonus_amount,
        allocation_type="sanzhar_only" if is_sanzhar else "raufal_only",
        sanzhar_amount=bonus_amount if is_sanzhar else Decimal("0.00"),
        raufal_amount=Decimal("0.00") if is_sanzhar else bonus_amount,
        comment=f"5% от дохода компании {income_amount} за {month_date.strftime('%Y-%m')}",
        created_by_user_id=current_admin.id,
        source_type="manager_bonus",
        manager_id=manager.id,
        bonus_income_amount=income_amount,
        bonus_percent=MANAGER_BONUS_PERCENT,
        created_at=now,
        updated_at=now,
    )

    try:
        db.add(expense)
        db.flush()

        closing = db.execute(
            select(MonthlyClosing).where(MonthlyClosing.month == month_date)
        ).scalar_one_or_none()
        if closing is not None and closing.status == "closed":
            calculated = calculate_closing(db, month_date)
            apply_calculated_to_closing(closing, calculated)
            closing.updated_at = now
            db.add(closing)

        db.commit()
        db.refresh(expense)
        return bonus_to_read(expense, manager)
    except IntegrityError:
        db.rollback()
        paid = existing_bonus(db, manager.id, month_date)
        if paid is not None:
            manager = db.execute(
                select(User).options(selectinload(User.department)).where(User.id == manager_id)
            ).scalar_one()
            return bonus_to_read(paid, manager)
        raise
