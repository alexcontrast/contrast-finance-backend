from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SelfEmployedAccountingUpdate(BaseModel):
    contractor_full_name: str | None = Field(default=None, max_length=255)
    iin: str | None = Field(default=None, max_length=20)
    receipt_number: str | None = Field(default=None, max_length=80)
    receipt_datetime: datetime | None = None
    service_name: str | None = None
    receipt_amount: Decimal | None = None
    qr_payload: str | None = None
    ocr_text: str | None = None
    parse_confidence: Decimal | None = None
    mark_confirmed: bool = False


class SelfEmployedAccountingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_request_id: int
    accounting_id: int | None = None

    event_id: int
    event_title: str | None = None
    event_date: date | None = None
    client_name: str | None = None
    manager_name: str | None = None

    request_created_at: datetime
    request_status: str
    money_status: str
    request_amount: Decimal
    item_name: str | None = None
    request_contractor_name: str | None = None
    request_comment: str | None = None

    receipt_filename: str | None = None
    receipt_content_type: str | None = None
    receipt_size: int | None = None
    receipt_sha256: str | None = None
    receipt_uploaded_at: datetime | None = None
    has_receipt: bool = False

    contractor_full_name: str | None = None
    iin: str | None = None
    receipt_number: str | None = None
    receipt_datetime: datetime | None = None
    service_name: str | None = None
    receipt_amount: Decimal | None = None

    qr_payload: str | None = None
    ocr_text: str | None = None
    parse_confidence: Decimal | None = None
    parse_status: str = "empty"
    confirmed_at: datetime | None = None
    act_status: str = "not_created"
