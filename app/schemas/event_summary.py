from decimal import Decimal

from pydantic import BaseModel


class EventSummaryRead(BaseModel):
    event_id: int
    client_name: str
    title: str
    status: str
    client_calc_type: str

    external_total: Decimal
    fact_total: Decimal
    paid_total: Decimal
    customer_paid_amount: Decimal = Decimal("0.00")
    customer_remaining_amount: Decimal = Decimal("0.00")

    regular_external_total: Decimal
    regular_fact_total: Decimal

    coordinator_external_total: Decimal
    coordinator_fact_amount: Decimal
    coordinator_company_share: Decimal

    vat_total: Decimal
    deductions_total: Decimal

    internal_tax_amount: Decimal
    simplified_bank_tax_amount: Decimal

    manager_salary_base: Decimal
    manager_percent: Decimal
    manager_salary: Decimal
    manager_salary_paid: Decimal

    company_income_before_manager_salary: Decimal
    company_income_after_manager_salary: Decimal
    final_company_income: Decimal

    # Explicit calculation fields for the unified event calculator.
    turnover_with_vat: Decimal
    client_vat_amount: Decimal
    contractor_vat_credit: Decimal
    vat_to_pay: Decimal
    tax_rate_percent: Decimal
    tax_base_amount: Decimal
    taxes_total: Decimal
