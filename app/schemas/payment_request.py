from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentRequestCreate(BaseModel):
    amount_requested: Decimal = Field(description="Сумма заявки — главное поле карточки")
    comment: str | None = None
    # Separate service field for website: surname is required for self-employed,
    # while comment remains an optional manager comment for Telegram/card display.
    self_employed_surname: str | None = None

    # Optional override. If empty, system uses payment_method from event item.
    payment_method: str | None = Field(default=None, description="invoice / card / cash / self_employed")

    # Required for card payments.
    card_number: str | None = None


class PaymentRequestStatusUpdate(BaseModel):
    # new / to_pay / paid / rejected / tax_check_needed
    status: str


class PaymentRequestMoneyStatusUpdate(BaseModel):
    # waiting_money / cash_received / cancelled
    money_status: str


class PaymentRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    event_item_id: int
    created_by_user_id: int

    amount_requested: Decimal
    payment_method: str
    status: str
    money_status: str
    comment: str | None

    item_name_snapshot: str | None
    item_amount_plan_snapshot: Decimal
    item_amount_fact_snapshot: Decimal | None
    item_paid_amount_snapshot: Decimal
    item_remaining_snapshot: Decimal

    contractor_id: int | None
    contractor_name_snapshot: str | None
    iin_bin_snapshot: str | None
    tax_status_snapshot: str | None
    tax_status_label: str | None = None

    # Frontend convenience fields.
    client_name: str | None = None
    event_title: str | None = None
    event_date: date | None = None
    manager_name: str | None = None
    position: str | None = None

    vat_status_snapshot: str | None
    vat_amount_snapshot: Decimal
    deduction_amount_snapshot: Decimal
    tax_source_snapshot: str | None

    card_number: str | None
    manual_tax_mode: bool
    warning_over_remaining: bool

    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None
    cash_received_at: datetime | None
    rejected_at: datetime | None


class PaymentRequestCardRead(BaseModel):
    """
    Лаконичная карточка заявки для будущего frontend/Telegram.

    Суммы НДС и Вычетов намеренно не показываем.
    Показываем только короткий налоговый статус.
    """
    id: int
    position: str | None
    amount_plan: Decimal
    fact: Decimal | None
    remaining: Decimal

    amount_requested: Decimal

    payment_method: str
    card_number: str | None = None
    iin_bin: str | None = None
    tax_status: str | None = None

    comment: str | None
    status: str
    money_status: str = "waiting_money"
    warning_over_remaining: bool
