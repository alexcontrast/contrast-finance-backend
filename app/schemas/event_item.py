from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class EventItemCreate(BaseModel):
    item_type: Literal["regular", "coordinator"] = "regular"
    # Stable browser-generated token used only while a new draft row is being
    # materialized. It makes concurrent autosave/manual-save POSTs idempotent.
    client_create_token: str | None = Field(
        default=None,
        max_length=96,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )

    # Внешняя смета
    external_name: str = Field(max_length=255, description="Название позиции для клиента")
    external_price: Decimal = Field(default=Decimal("0.00"), ge=0, le=Decimal("100000000000"))
    external_quantity: Decimal = Field(default=Decimal("1"), ge=1, le=100000, multiple_of=1)
    external_days: Decimal = Field(default=Decimal("1"), ge=1, le=100000, multiple_of=1)
    external_note: str | None = None

    # Внутренняя смета
    amount_fact: Decimal | None = Field(default=None, ge=0, le=Decimal("100000000000"))
    paid_amount: Decimal = Decimal("0.00")
    payment_method: Literal["invoice", "card", "cash", "self_employed"] | None = None
    reset_tax_context: bool = False

    iin_bin: str | None = None
    iin_bin_locked: bool = False
    tax_check_status: str | None = None

    # Лаконичные столбики внутренней сметы: НДС и Вычеты
    vat_amount: Decimal = Decimal("0.00")
    deduction_amount: Decimal = Decimal("0.00")

    internal_note: str | None = None
    sort_order: int = 0
    # Sent only when an existing row is updated. It prevents a stale browser
    # tab from silently overwriting a newer version of the same estimate row.
    expected_updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_amount_range(self):
        if self.external_price * self.external_quantity * self.external_days > Decimal("999999999999.99"):
            raise ValueError("Сумма позиции превышает допустимый предел")
        return self


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
    creation_replayed: bool = False

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
