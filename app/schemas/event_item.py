from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class EventItemCreate(BaseModel):
    item_type: str = Field(default="regular", description="regular / coordinator")

    # Внешняя смета
    external_name: str = Field(description="Название позиции для клиента")
    external_price: Decimal = Decimal("0.00")
    external_quantity: Decimal = Decimal("1.00")
    external_days: Decimal = Decimal("1.00")
    external_note: str | None = None

    # Внутренняя смета
    amount_fact: Decimal | None = None
    paid_amount: Decimal = Decimal("0.00")
    payment_method: str | None = Field(default=None, description="invoice / card / cash / self_employed")

    iin_bin: str | None = None
    iin_bin_locked: bool = False
    tax_check_status: str | None = None

    # Лаконичные столбики внутренней сметы: НДС и Вычеты
    vat_amount: Decimal = Decimal("0.00")
    deduction_amount: Decimal = Decimal("0.00")

    internal_note: str | None = None
    sort_order: int = 0


class EventItemUpdate(BaseModel):
    item_type: str | None = None

    external_name: str | None = None
    external_price: Decimal | None = None
    external_quantity: Decimal | None = None
    external_days: Decimal | None = None
    external_note: str | None = None

    amount_fact: Decimal | None = None
    paid_amount: Decimal | None = None
    payment_method: str | None = None

    iin_bin: str | None = None
    iin_bin_locked: bool | None = None
    tax_check_status: str | None = None

    vat_amount: Decimal | None = None
    deduction_amount: Decimal | None = None

    internal_note: str | None = None
    sort_order: int | None = None
    is_deleted: bool | None = None


class EventItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    item_type: str

    external_name: str
    external_price: Decimal
    external_quantity: Decimal
    external_days: Decimal
    external_amount: Decimal
    external_note: str | None

    amount_fact: Decimal | None
    paid_amount: Decimal
    payment_method: str | None

    iin_bin: str | None
    iin_bin_locked: bool
    tax_check_status: str | None

    vat_amount: Decimal
    deduction_amount: Decimal

    internal_note: str | None
    sort_order: int
    is_deleted: bool

    created_at: datetime
    updated_at: datetime
