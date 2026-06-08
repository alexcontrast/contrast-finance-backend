from decimal import Decimal

from app.core.config import get_settings
from app.models.event import Event
from app.models.event_item import EventItem




def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q(value: Decimal) -> Decimal:
    return money(value).quantize(Decimal("0.01"))


def q0(value: Decimal) -> Decimal:
    return money(value).quantize(Decimal("1"))


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


def client_vat_amount(event: Event, client_base_amount: Decimal) -> Decimal:
    """
    НДС с клиентской сметы.

    ip_contrast_event: внешняя смета хранится без НДС, клиентский НДС добавляется сверху.
    our_no_vat / simplified / cash: НДС клиенту не добавляется.
    """
    if event.client_calc_type == "ip_contrast_event":
        return q0(client_base_amount * get_settings().VAT_RATE)
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
        return q(regular_turnover_with_vat)

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

    # Внешняя смета хранится без клиентского НДС.
    # Оборот для клиента = внешняя смета + агентская комиссия + клиентский НДС/упрощённый markup.
    items_external_total = sum((money(item.external_amount) for item in business_items), Decimal("0.00"))
    agency_commission_percent = money(event.agency_commission_amount)
    agency_commission_amount = q0(items_external_total * agency_commission_percent / Decimal("100.00"))

    regular_external_total = sum((money(item.external_amount) for item in regular_items), Decimal("0.00"))
    regular_fact_total = sum((item_fact_or_plan(item) for item in regular_items), Decimal("0.00"))

    coordinator_external_total = sum((money(item.external_amount) for item in coordinator_items), Decimal("0.00"))
    coordinator_fact_amount = q0(coordinator_external_total * Decimal("0.50"))
    coordinator_company_share = q0(coordinator_external_total * Decimal("0.50"))

    client_base_amount = q0(items_external_total + agency_commission_amount)
    simplified_markup_amount = calculate_simplified_bank_tax(event, client_base_amount)
    client_vat = client_vat_amount(event, client_base_amount)
    turnover_with_vat = q0(client_base_amount + client_vat + simplified_markup_amount)
    external_total = turnover_with_vat

    fact_total = sum((item_fact_or_plan(item) for item in regular_items), Decimal("0.00")) + coordinator_fact_amount
    paid_total = sum((money(item.paid_amount) for item in items), Decimal("0.00"))
    manager_salary_paid = sum((money(item.paid_amount) for item in manager_salary_items), Decimal("0.00"))

    contractor_vat_credit = sum((item_vat_credit(item) for item in regular_items), Decimal("0.00"))
    vat_to_pay = q0(client_vat - contractor_vat_credit)
    if vat_to_pay < 0:
        vat_to_pay = Decimal("0.00")

    deductions_total = sum((item_deduction(item) for item in regular_items), Decimal("0.00"))

    # Внутренний налог считается от клиентской базы без НДС:
    # позиции + агентская комиссия. Координатор входит в налоговую базу, но не в базу 21%.
    internal_tax_amount = q0(calculate_internal_tax(event, client_base_amount))
    simplified_bank_tax_amount = simplified_markup_amount

    # Комиссия обычных позиций = смета обычных позиций - факт обычных позиций.
    # Клиентский НДС не минусуем из дохода: он не добавлялся в доходную базу, это транзит.
    # НДС подрядчиков в зачёт и налоговые вычеты добавляют экономию/доход.
    regular_positions_commission = q0(regular_external_total - regular_fact_total)
    manager_salary_base = (
        regular_positions_commission
        + agency_commission_amount
        + contractor_vat_credit
        + deductions_total
        - internal_tax_amount
    )

    company_income_before_manager_salary = manager_salary_base
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
        "regular_positions_commission": q0(regular_positions_commission),
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
        "turnover_with_vat": q0(turnover_with_vat),
        "client_vat_amount": q0(client_vat),
        "contractor_vat_credit": q0(contractor_vat_credit),
        "vat_to_pay": q0(vat_to_pay),
        "tax_rate_percent": q(tax_rate_percent(event)),
        "tax_base_amount": q0(client_base_amount),
        "taxes_total": q0(internal_tax_amount),
        "taxes_net": q0(internal_tax_amount - deductions_total),
        "vat_net": q0(vat_to_pay),
        "agency_commission_amount": q0(agency_commission_amount),
        "manager_salary_negative_commission": q0(manager_salary * Decimal("-1")),
    }
