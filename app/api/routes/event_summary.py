from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.event_item import EventItem
from app.schemas.event_summary import EventSummaryRead


router = APIRouter(tags=["event_summary"])


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q(value: Decimal) -> Decimal:
    return money(value).quantize(Decimal("0.01"))


def item_fact_or_plan(item: EventItem) -> Decimal:
    """
    Для внутренней экономики используем факт, если он заполнен.
    Если факта нет — сумму по внешней смете.
    """
    return money(item.amount_fact) if item.amount_fact is not None else money(item.external_amount)


def calculate_internal_tax(event: Event, regular_external_total: Decimal) -> Decimal:
    """
    Внутренняя налоговая нагрузка:
    - ИП Contrast Event: 12% от суммы без НДС
    - ОУР без НДС: такая же внутренняя логика, но без клиентского НДС
    - Упрощенка: 5%
    - Нал: 0
    """
    calc_type = event.client_calc_type

    if calc_type == "ip_contrast_event":
        amount_without_vat = regular_external_total / Decimal("1.12")
        return q(amount_without_vat * Decimal("0.12"))

    if calc_type == "our_no_vat":
        return q(regular_external_total * Decimal("0.12"))

    if calc_type == "simplified":
        return q(regular_external_total * Decimal("0.05"))

    return Decimal("0.00")


def calculate_simplified_bank_tax(event: Event, regular_external_total: Decimal) -> Decimal:
    """
    Для Упрощенки есть одна строка: банковские и налоговые платежи, %.
    Это процент сверху сметы, который влияет на внутреннюю экономику/клиентскую надбавку.
    """
    if event.client_calc_type != "simplified":
        return Decimal("0.00")

    percent = money(event.simplified_bank_tax_percent)
    if percent <= 0:
        return Decimal("0.00")

    return q(regular_external_total * percent / Decimal("100"))


@router.get("/events/{event_id}/summary", response_model=EventSummaryRead)
def get_event_summary(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    result = db.execute(
        select(EventItem)
        .where(EventItem.event_id == event_id, EventItem.is_deleted == False)  # noqa: E712
        .order_by(EventItem.sort_order, EventItem.id)
    )
    items = result.scalars().all()

    regular_items = [item for item in items if item.item_type != "coordinator"]
    coordinator_items = [item for item in items if item.item_type == "coordinator"]

    external_total = sum((money(item.external_amount) for item in items), Decimal("0.00"))
    fact_total = sum((item_fact_or_plan(item) for item in items), Decimal("0.00"))
    paid_total = sum((money(item.paid_amount) for item in items), Decimal("0.00"))

    regular_external_total = sum((money(item.external_amount) for item in regular_items), Decimal("0.00"))
    regular_fact_total = sum((item_fact_or_plan(item) for item in regular_items), Decimal("0.00"))

    coordinator_external_total = sum((money(item.external_amount) for item in coordinator_items), Decimal("0.00"))
    coordinator_fact_amount = q(coordinator_external_total * Decimal("0.50"))
    coordinator_company_share = q(coordinator_external_total * Decimal("0.50"))

    vat_total = sum((money(item.vat_amount) for item in regular_items), Decimal("0.00"))
    deductions_total = sum((money(item.deduction_amount) for item in regular_items), Decimal("0.00"))

    internal_tax_amount = calculate_internal_tax(event, regular_external_total)
    simplified_bank_tax_amount = calculate_simplified_bank_tax(event, regular_external_total)

    # База для ЗП менеджера:
    # доход по обычным позициям - факт обычных подрядчиков - налоги/платежи + НДС/вычеты.
    company_income_before_manager_salary = (
        regular_external_total
        - regular_fact_total
        - internal_tax_amount
        - simplified_bank_tax_amount
        + vat_total
        + deductions_total
    )

    manager_salary_base = company_income_before_manager_salary
    manager_percent = money(event.manager_percent)

    if manager_salary_base <= 0:
        manager_salary = Decimal("0.00")
    else:
        manager_salary = q(manager_salary_base * manager_percent / Decimal("100"))

    company_income_after_manager_salary = q(company_income_before_manager_salary - manager_salary)

    # Координаторская доля компании добавляется после всех вычетов и ЗП менеджера.
    final_company_income = q(company_income_after_manager_salary + coordinator_company_share)

    return EventSummaryRead(
        event_id=event.id,
        client_name=event.client_name,
        title=event.title,
        status=event.status,
        client_calc_type=event.client_calc_type,

        external_total=q(external_total),
        fact_total=q(fact_total),
        paid_total=q(paid_total),

        regular_external_total=q(regular_external_total),
        regular_fact_total=q(regular_fact_total),

        coordinator_external_total=q(coordinator_external_total),
        coordinator_fact_amount=q(coordinator_fact_amount),
        coordinator_company_share=q(coordinator_company_share),

        vat_total=q(vat_total),
        deductions_total=q(deductions_total),

        internal_tax_amount=q(internal_tax_amount),
        simplified_bank_tax_amount=q(simplified_bank_tax_amount),

        manager_salary_base=q(manager_salary_base),
        manager_percent=q(manager_percent),
        manager_salary=q(manager_salary),

        company_income_before_manager_salary=q(company_income_before_manager_salary),
        company_income_after_manager_salary=q(company_income_after_manager_salary),
        final_company_income=q(final_company_income),
    )
