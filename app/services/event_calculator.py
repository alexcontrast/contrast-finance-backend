from decimal import Decimal

from app.core.config import get_settings
from app.models.event import Event
from app.models.event_item import EventItem


VAT_RATE = Decimal("0.12")
VAT_DIVISOR = Decimal("1.12")


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q(value: Decimal) -> Decimal:
    return money(value).quantize(Decimal("0.01"))


def item_fact_or_plan(item: EventItem) -> Decimal:
    return money(item.amount_fact) if item.amount_fact is not None else money(item.external_amount)


def is_invoice_item(item: EventItem) -> bool:
    return item.payment_method == "invoice"


def is_self_employed_item(item: EventItem) -> bool:
    return item.payment_method == "self_employed"


def item_vat_credit(item: EventItem) -> Decimal:
    """НДС подрядчика, который можно взять в зачёт."""
    if not is_invoice_item(item):
        return Decimal("0.00")
    return money(item.vat_amount)


def item_deduction(item: EventItem) -> Decimal:
    """
    Вычеты подрядчиков:
    - По счету: из позиции/КГД
    - Самозанятый: 10%, если не записано явно
    - Налик/карта: 0
    """
    if is_invoice_item(item):
        return money(item.deduction_amount)

    if is_self_employed_item(item):
        stored = money(item.deduction_amount)
        if stored > 0:
            return stored
        return q(item_fact_or_plan(item) * Decimal("0.10"))

    return Decimal("0.00")


def client_vat_amount(event: Event, turnover_with_vat: Decimal) -> Decimal:
    """
    НДС с клиентской сметы.

    ip_contrast_event: считаем, что внешняя сумма уже с НДС, поэтому НДС = сумма * 12 / 112.
    our_no_vat / simplified / cash: НДС клиенту не добавляется.
    """
    if event.client_calc_type == "ip_contrast_event":
        return q(turnover_with_vat / VAT_DIVISOR * VAT_RATE)
    return Decimal("0.00")


def tax_rate_percent(event: Event) -> Decimal:
    if event.client_calc_type in {"ip_contrast_event", "our_no_vat"}:
        return Decimal("12.00")
    if event.client_calc_type == "simplified":
        return Decimal("5.00")
    return Decimal("0.00")


def tax_base_amount(event: Event, regular_turnover_with_vat: Decimal) -> Decimal:
    """
    База внутреннего налога.

    ip_contrast_event: 12% от суммы без НДС.
    our_no_vat: 12% от суммы, потому что клиенту НДС сверху не добавляем.
    simplified: 5% от суммы.
    cash: 0.
    """
    if event.client_calc_type == "ip_contrast_event":
        return q(regular_turnover_with_vat / VAT_DIVISOR)

    if event.client_calc_type in {"our_no_vat", "simplified"}:
        return q(regular_turnover_with_vat)

    return Decimal("0.00")


def calculate_internal_tax(event: Event, regular_turnover_with_vat: Decimal) -> Decimal:
    base = tax_base_amount(event, regular_turnover_with_vat)

    if event.client_calc_type in {"ip_contrast_event", "our_no_vat"}:
        return q(base * get_settings().CONTRAST_INTERNAL_TAX_RATE)

    if event.client_calc_type == "simplified":
        return q(base * get_settings().SIMPLIFIED_TAX_RATE)

    return Decimal("0.00")


def calculate_simplified_bank_tax(event: Event, regular_turnover_with_vat: Decimal) -> Decimal:
    if event.client_calc_type != "simplified":
        return Decimal("0.00")

    percent = money(event.simplified_bank_tax_percent)
    if percent <= 0:
        return Decimal("0.00")

    return q(regular_turnover_with_vat * percent / Decimal("100"))


def calculate_event_summary_values(event: Event, items: list[EventItem]) -> dict:
    """
    Единый калькулятор мероприятия.

    Термины:
    - external_total / turnover_with_vat: оборот для клиента, сумма внешней сметы.
    - client_vat_amount: НДС с клиентской сметы.
    - contractor_vat_credit: НДС подрядчиков, который берём в зачёт.
    - vat_to_pay: НДС к оплате = клиентский НДС - НДС подрядчиков.
    - deductions_total: прочие вычеты подрядчиков, которые уменьшают налоговую нагрузку/увеличивают доход.
    - manager_salary: 21% от базы менеджера, координатор не участвует в базе.
    - coordinator_company_share: 50% координатора в доход компании, добавляется после ЗП менеджера.
    """
    manager_salary_items = [item for item in items if item.item_type == "manager_salary"]
    business_items = [item for item in items if item.item_type != "manager_salary"]
    regular_items = [item for item in business_items if item.item_type != "coordinator"]
    coordinator_items = [item for item in business_items if item.item_type == "coordinator"]

    # Оборот — внешняя смета клиента. Для ip_contrast_event считаем, что она уже с НДС.
    turnover_with_vat = sum((money(item.external_amount) for item in business_items), Decimal("0.00"))
    external_total = turnover_with_vat

    fact_total = sum((item_fact_or_plan(item) for item in business_items), Decimal("0.00"))
    paid_total = sum((money(item.paid_amount) for item in items), Decimal("0.00"))
    manager_salary_paid = sum((money(item.paid_amount) for item in manager_salary_items), Decimal("0.00"))

    regular_external_total = sum((money(item.external_amount) for item in regular_items), Decimal("0.00"))
    regular_fact_total = sum((item_fact_or_plan(item) for item in regular_items), Decimal("0.00"))

    coordinator_external_total = sum((money(item.external_amount) for item in coordinator_items), Decimal("0.00"))
    coordinator_fact_amount = q(coordinator_external_total * Decimal("0.50"))
    coordinator_company_share = q(coordinator_external_total * Decimal("0.50"))

    client_vat = client_vat_amount(event, turnover_with_vat)
    contractor_vat_credit = sum((item_vat_credit(item) for item in regular_items), Decimal("0.00"))
    vat_to_pay = q(client_vat - contractor_vat_credit)

    deductions_total = sum((item_deduction(item) for item in regular_items), Decimal("0.00"))

    internal_tax_amount = calculate_internal_tax(event, regular_external_total)
    simplified_bank_tax_amount = calculate_simplified_bank_tax(event, regular_external_total)

    # Координатор исключён из базы менеджерских 21%.
    company_income_before_manager_salary = (
        regular_external_total
        - regular_fact_total
        - internal_tax_amount
        - simplified_bank_tax_amount
        - vat_to_pay
        + deductions_total
    )

    manager_salary_base = company_income_before_manager_salary
    manager_percent = money(event.manager_percent)

    if manager_salary_base <= 0:
        manager_salary = Decimal("0.00")
    else:
        manager_salary = q(manager_salary_base * manager_percent / Decimal("100"))

    company_income_after_manager_salary = q(company_income_before_manager_salary - manager_salary)
    final_company_income = q(company_income_after_manager_salary + coordinator_company_share)

    return {
        # Legacy-compatible fields.
        "external_total": q(external_total),
        "fact_total": q(fact_total),
        "paid_total": q(paid_total),
        "regular_external_total": q(regular_external_total),
        "regular_fact_total": q(regular_fact_total),
        "coordinator_external_total": q(coordinator_external_total),
        "coordinator_fact_amount": q(coordinator_fact_amount),
        "coordinator_company_share": q(coordinator_company_share),
        "vat_total": q(vat_to_pay),
        "deductions_total": q(deductions_total),
        "internal_tax_amount": q(internal_tax_amount),
        "simplified_bank_tax_amount": q(simplified_bank_tax_amount),
        "manager_salary_base": q(manager_salary_base),
        "manager_percent": q(manager_percent),
        "manager_salary": q(manager_salary),
        "manager_salary_paid": q(manager_salary_paid),
        "company_income_before_manager_salary": q(company_income_before_manager_salary),
        "company_income_after_manager_salary": q(company_income_after_manager_salary),
        "final_company_income": q(final_company_income),

        # New explicit fields for frontend and future manager cabinet.
        "turnover_with_vat": q(turnover_with_vat),
        "client_vat_amount": q(client_vat),
        "contractor_vat_credit": q(contractor_vat_credit),
        "vat_to_pay": q(vat_to_pay),
        "tax_rate_percent": q(tax_rate_percent(event)),
        "tax_base_amount": q(tax_base_amount(event, regular_external_total)),
        "taxes_total": q(internal_tax_amount + simplified_bank_tax_amount),
    }
