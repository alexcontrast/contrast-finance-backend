from datetime import datetime
import logging
import time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.models.user import User
from app.schemas.monthly_plan import CompanyDashboardRead, DepartmentDashboardRead, MonthlyPlanCreate, MonthlyPlanRead
from app.services.auth import require_roles
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["monthly"])
logger = logging.getLogger("contrast.performance")


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def normalize_month(month):
    return month.replace(day=1)


def get_plan_or_404(db: Session, month):
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == normalize_month(month))).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Monthly plan not found")
    return plan


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


def get_department_income(db: Session, department_id: int, year: int, month: int, include_drafts: bool) -> tuple[Decimal, int, int]:
    query = select(Event).where(
        Event.department_id == department_id,
        extract("year", Event.event_date) == year,
        extract("month", Event.event_date) == month,
        Event.status != "cancelled",
    )

    if not include_drafts:
        query = query.where(Event.status != "draft")

    events = db.execute(query).scalars().all()

    income = Decimal("0.00")
    drafts_count = 0

    for event in events:
        if event.status == "draft":
            drafts_count += 1

        items = db.execute(
            select(EventItem)
            .where(EventItem.event_id == event.id, EventItem.is_deleted == False)  # noqa: E712
            .order_by(EventItem.sort_order, EventItem.id)
        ).scalars().all()

        values = calculate_event_summary_values(event, items)
        income += money(values["final_company_income"])

    return q(income), len(events), drafts_count


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


@router.post("/monthly-plans", response_model=MonthlyPlanRead)
def create_or_update_monthly_plan(
    payload: MonthlyPlanCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    month = normalize_month(payload.month)
    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month)).scalar_one_or_none()

    if plan is None:
        plan = MonthlyPlan(
            month=month,
            company_plan_amount=payload.company_plan_amount,
            sanzhar_share_percent=payload.sanzhar_share_percent,
            raufal_share_percent=payload.raufal_share_percent,
            manager_personal_plan_percent=payload.manager_personal_plan_percent,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    else:
        plan.company_plan_amount = payload.company_plan_amount
        plan.sanzhar_share_percent = payload.sanzhar_share_percent
        plan.raufal_share_percent = payload.raufal_share_percent
        plan.manager_personal_plan_percent = payload.manager_personal_plan_percent
        plan.updated_at = datetime.utcnow()

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/monthly-plans", response_model=list[MonthlyPlanRead])
def list_monthly_plans(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    started_at = time.perf_counter()
    plans = db.execute(select(MonthlyPlan).order_by(MonthlyPlan.month.desc())).scalars().all()
    logger.info(
        "PERF monthly-plans user_id=%s count=%s total=%.3fs",
        getattr(current_admin, "id", None),
        len(plans),
        time.perf_counter() - started_at,
    )
    return plans


@router.get("/monthly-dashboard", response_model=CompanyDashboardRead)
def get_monthly_dashboard(month: str, include_drafts: bool = True, db: Session = Depends(get_db)):
    """
    month format: YYYY-MM-01 or YYYY-MM-DD.
    The day is normalized to the first day of month.
    """
    from datetime import date

    try:
        parts = [int(part) for part in month.split("-")]
        month_date = date(parts[0], parts[1], 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM or YYYY-MM-DD") from exc

    plan = get_plan_or_404(db, month_date)
    departments = db.execute(select(Department).where(Department.is_active == True).order_by(Department.id)).scalars().all()  # noqa: E712

    rows = []
    company_fact = Decimal("0.00")

    for department in departments:
        dept_plan = department_plan_amount(plan, department.name)
        fact_income, events_count, drafts_count = get_department_income(
            db=db,
            department_id=department.id,
            year=month_date.year,
            month=month_date.month,
            include_drafts=include_drafts,
        )
        expenses = get_department_expenses(
            db=db,
            department_name=department.name,
            year=month_date.year,
            month=month_date.month,
        )

        company_fact += fact_income

        rows.append(
            DepartmentDashboardRead(
                month=month_date,
                department_id=department.id,
                department_name=department.name,
                plan_amount=q(dept_plan),
                fact_income_amount=q(fact_income),
                completion_percent=completion_percent(fact_income, dept_plan),
                remaining_to_plan=q(dept_plan - fact_income),
                events_count=events_count,
                drafts_count=drafts_count,
                expenses_amount=q(expenses),
                include_drafts=include_drafts,
            )
        )

    return CompanyDashboardRead(
        month=month_date,
        company_plan_amount=q(plan.company_plan_amount),
        company_fact_income_amount=q(company_fact),
        company_completion_percent=completion_percent(company_fact, money(plan.company_plan_amount)),
        manager_personal_plan_amount=manager_personal_plan_amount(plan),
        departments=rows,
    )
