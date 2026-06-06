from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentRequestCreate(BaseModel):
    amount_requested: Decimal = Field(description="Сумма заявки — главное поле карточки")
    comment: str | None = None

    # Optional override. If empty, system uses payment_method from event item.
    payment_method: str | None = Field(default=None, description="invoice / card / cash / self_employed")

    # Required later for card payments, but in v0.7 only stored.
    card_number: str | None = None


class PaymentRequestStatusUpdate(BaseModel):
    # new / to_pay / paid / cash_received / rejected / tax_check_needed
    status: str


class PaymentRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    event_item_id: int
    created_by_user_id: int

    amount_requested: Decimal
    payment_method: str
    status: str
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
