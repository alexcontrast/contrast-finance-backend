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


class SelfEmployedAccountingGroupCreate(BaseModel):
    request_ids: list[int] = Field(min_length=2, max_length=100)


class SelfEmployedAccountingAttachCreate(BaseModel):
    request_ids: list[int] = Field(min_length=1, max_length=100)


class SelfEmployedAccountingMemberRead(BaseModel):
    payment_request_id: int
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
    request_iin: str | None = None
    request_comment: str | None = None


class SelfEmployedAccountingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    row_key: str
    row_kind: str = "request"  # request / receipt
    is_receipt_only: bool = False

    # For request-backed rows this is the first member and remains a convenient
    # backwards-compatible handle. Standalone receipt rows have no request id.
    payment_request_id: int | None = None
    payment_request_ids: list[int] = Field(default_factory=list)
    request_count: int = 0
    accounting_id: int | None = None
    is_grouped: bool = False
    members: list[SelfEmployedAccountingMemberRead] = Field(default_factory=list)

    event_id: int | None = None
    event_title: str | None = None
    event_date: date | None = None
    client_name: str | None = None
    manager_name: str | None = None

    request_created_at: datetime | None = None
    request_status: str | None = None
    money_status: str | None = None
    request_amount: Decimal = Decimal("0.00")
    item_name: str | None = None
    request_contractor_name: str | None = None
    request_iin: str | None = None
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


class SelfEmployedReceiptImportRead(BaseModel):
    row: SelfEmployedAccountingRead
    match_status: str  # matched / unmatched / ambiguous
    matched_request_ids: list[int] = Field(default_factory=list)
    message: str


class SelfEmployedReceiptQrResolveCreate(BaseModel):
    qr_payload: str = Field(min_length=1, max_length=10000)


class SelfEmployedReceiptQrResolveRead(BaseModel):
    contractor_full_name: str | None = None
    iin: str | None = None
    receipt_number: str | None = None
    receipt_datetime: datetime | None = None
    service_name: str | None = None
    receipt_amount: Decimal | None = None
    qr_payload: str
    parse_confidence: Decimal = Decimal("100.00")
    source: str = "kgd_qr"
    message: str = "Данные получены из КГД по QR чека"


class R1CustomerProfileRead(BaseModel):
    name: str
    bin_iin: str
    country: str
    address: str
    iik: str
    bank_name: str
    bik: str
    kbe: str
    director: str
