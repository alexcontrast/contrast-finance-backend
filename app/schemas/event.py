from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    client_name: str = Field(description="Заказчик")
    title: str = Field(description="Название мероприятия")
    event_date: date
    department_id: int
    manager_id: int

    # ip_contrast_event / our_no_vat / simplified / cash
    client_calc_type: str

    manager_percent: Decimal = Decimal("21.00")
    agency_commission_amount: Decimal = Decimal("0.00")
    agency_commission_spread_enabled: bool = False
    simplified_bank_tax_percent: Decimal | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    title: str
    event_date: date
    department_id: int
    manager_id: int
    status: str
    client_calc_type: str
    manager_percent: Decimal
    agency_commission_amount: Decimal
    agency_commission_spread_enabled: str
    simplified_bank_tax_percent: Decimal | None
    created_at: datetime
    updated_at: datetime
