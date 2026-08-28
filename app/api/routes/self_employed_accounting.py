from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.payment_request import PaymentRequest
from app.models.self_employed_accounting import SelfEmployedAccounting
from app.models.user import User
from app.schemas.self_employed_accounting import (
    SelfEmployedAccountingRead,
    SelfEmployedAccountingUpdate,
)
from app.services.auth import get_current_user


router = APIRouter(prefix="/accounting/self-employed", tags=["self_employed_accounting"])

MAX_RECEIPT_BYTES = 10 * 1024 * 1024
ALLOWED_RECEIPT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
}


def require_accounting_access(user: User) -> None:
    # Accountant is included already for the future dedicated login; today's UI
    # exposes the workspace only to admin.
    if user.role not in {"admin", "accountant"}:
        raise HTTPException(status_code=403, detail="Бухгалтерия доступна только администратору и бухгалтеру")


def clean_text(value: str | None, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).replace("\x00", " ").split()).strip()
    if not cleaned:
        return None
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def clean_iin(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return None
    if len(digits) != 12:
        raise HTTPException(status_code=400, detail="ИИН должен содержать 12 цифр")
    return digits


def get_request_or_404(db: Session, request_id: int) -> PaymentRequest:
    request = db.get(PaymentRequest, int(request_id))
    if request is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if request.payment_method != "self_employed":
        raise HTTPException(status_code=409, detail="Эта заявка не относится к Самозанятым")
    return request


def get_or_create_record(db: Session, request_id: int) -> SelfEmployedAccounting:
    record = db.execute(
        select(SelfEmployedAccounting)
        .where(SelfEmployedAccounting.payment_request_id == int(request_id))
        .with_for_update()
    ).scalar_one_or_none()
    if record is None:
        record = SelfEmployedAccounting(
            payment_request_id=int(request_id),
            parse_status="empty",
            act_status="not_created",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(record)
        db.flush()
    return record


def build_row(
    request: PaymentRequest,
    event: Event,
    manager_name: str | None,
    record: SelfEmployedAccounting | None,
) -> SelfEmployedAccountingRead:
    return SelfEmployedAccountingRead(
        payment_request_id=request.id,
        accounting_id=record.id if record else None,
        event_id=event.id,
        event_title=event.title,
        event_date=event.event_date,
        client_name=event.client_name,
        manager_name=manager_name,
        request_created_at=request.created_at,
        request_status=request.status,
        money_status=getattr(request, "money_status", "waiting_money"),
        request_amount=request.amount_requested,
        item_name=request.item_name_snapshot,
        request_contractor_name=request.contractor_name_snapshot,
        request_comment=request.comment,
        receipt_filename=record.receipt_filename if record else None,
        receipt_content_type=record.receipt_content_type if record else None,
        receipt_size=record.receipt_size if record else None,
        receipt_sha256=record.receipt_sha256 if record else None,
        receipt_uploaded_at=record.receipt_uploaded_at if record else None,
        has_receipt=bool(record and record.receipt_filename and record.receipt_size),
        contractor_full_name=record.contractor_full_name if record else None,
        iin=record.iin if record else None,
        receipt_number=record.receipt_number if record else None,
        receipt_datetime=record.receipt_datetime if record else None,
        service_name=record.service_name if record else None,
        receipt_amount=record.receipt_amount if record else None,
        qr_payload=record.qr_payload if record else None,
        ocr_text=record.ocr_text if record else None,
        parse_confidence=record.parse_confidence if record else None,
        parse_status=record.parse_status if record else "empty",
        confirmed_at=record.confirmed_at if record else None,
        act_status=record.act_status if record else "not_created",
    )


def load_row(db: Session, request_id: int) -> SelfEmployedAccountingRead:
    row = db.execute(
        select(PaymentRequest, Event, User.name, SelfEmployedAccounting)
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(User, User.id == Event.manager_id)
        .outerjoin(
            SelfEmployedAccounting,
            SelfEmployedAccounting.payment_request_id == PaymentRequest.id,
        )
        .where(PaymentRequest.id == int(request_id))
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    request, event, manager_name, record = row
    if request.payment_method != "self_employed":
        raise HTTPException(status_code=409, detail="Эта заявка не относится к Самозанятым")
    return build_row(request, event, manager_name, record)


@router.get("", response_model=list[SelfEmployedAccountingRead])
def list_self_employed_accounting(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)

    query = (
        select(PaymentRequest, Event, User.name, SelfEmployedAccounting)
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(User, User.id == Event.manager_id)
        .outerjoin(
            SelfEmployedAccounting,
            SelfEmployedAccounting.payment_request_id == PaymentRequest.id,
        )
        .where(PaymentRequest.payment_method == "self_employed")
        .order_by(PaymentRequest.created_at.desc(), PaymentRequest.id.desc())
    )

    if month:
        try:
            year_part, month_part = month.split("-")[:2]
            year_num = int(year_part)
            month_num = int(month_part)
            if not 1 <= month_num <= 12:
                raise ValueError
        except Exception as exc:
            raise HTTPException(status_code=400, detail="month must be YYYY-MM") from exc
        month_start = date(year_num, month_num, 1)
        next_month = date(year_num + 1, 1, 1) if month_num == 12 else date(year_num, month_num + 1, 1)
        query = query.where(Event.event_date >= month_start, Event.event_date < next_month)

    rows = db.execute(query).all()
    return [build_row(request, event, manager_name, record) for request, event, manager_name, record in rows]


@router.post("/{request_id}/receipt", response_model=SelfEmployedAccountingRead)
async def upload_self_employed_receipt(
    request_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    get_request_or_404(db, request_id)

    content_type = (file.content_type or "").lower().split(";", 1)[0].strip()
    if content_type not in ALLOWED_RECEIPT_TYPES:
        raise HTTPException(status_code=400, detail="Поддерживаются JPG, PNG, WEBP и PDF")

    content = await file.read(MAX_RECEIPT_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(content) > MAX_RECEIPT_BYTES:
        raise HTTPException(status_code=413, detail="Чек слишком большой. Максимум 10 МБ")

    digest = sha256(content).hexdigest()
    duplicate = db.execute(
        select(SelfEmployedAccounting.payment_request_id)
        .where(
            SelfEmployedAccounting.receipt_sha256 == digest,
            SelfEmployedAccounting.payment_request_id != int(request_id),
        )
        .limit(1)
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Этот же файл чека уже прикреплён к заявке №{duplicate}",
        )

    record = get_or_create_record(db, request_id)
    record.receipt_filename = Path(file.filename or "receipt").name[:255]
    record.receipt_content_type = content_type
    record.receipt_size = len(content)
    record.receipt_sha256 = digest
    record.receipt_data = content
    record.receipt_uploaded_at = datetime.utcnow()
    record.receipt_uploaded_by_user_id = current_user.id

    # A replacement is a new source document. Keep the previous extracted values
    # visible until OCR finishes, but mark them unconfirmed so they cannot silently
    # become the source of a future act.
    record.parse_status = "uploaded"
    record.confirmed_at = None
    record.confirmed_by_user_id = None
    record.updated_at = datetime.utcnow()
    db.add(record)
    db.commit()
    return load_row(db, request_id)


@router.patch("/{request_id}", response_model=SelfEmployedAccountingRead)
def update_self_employed_accounting(
    request_id: int,
    payload: SelfEmployedAccountingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    request = get_request_or_404(db, request_id)
    record = get_or_create_record(db, request_id)

    if payload.contractor_full_name is not None:
        record.contractor_full_name = clean_text(payload.contractor_full_name, 255)
    if payload.iin is not None:
        record.iin = clean_iin(payload.iin)
    if payload.receipt_number is not None:
        record.receipt_number = clean_text(payload.receipt_number, 80)
    if payload.receipt_datetime is not None:
        record.receipt_datetime = payload.receipt_datetime.replace(tzinfo=None)
    if payload.service_name is not None:
        record.service_name = clean_text(payload.service_name)
    if payload.receipt_amount is not None:
        amount = Decimal(payload.receipt_amount).quantize(Decimal("0.01"))
        if amount < 0:
            raise HTTPException(status_code=400, detail="Сумма чека не может быть отрицательной")
        record.receipt_amount = amount
    if payload.qr_payload is not None:
        record.qr_payload = str(payload.qr_payload)[:10000]
    if payload.ocr_text is not None:
        record.ocr_text = str(payload.ocr_text)[:50000]
    if payload.parse_confidence is not None:
        confidence = Decimal(payload.parse_confidence)
        record.parse_confidence = max(Decimal("0"), min(Decimal("100"), confidence))

    if any(
        value is not None
        for value in (
            payload.contractor_full_name,
            payload.iin,
            payload.receipt_number,
            payload.receipt_datetime,
            payload.service_name,
            payload.receipt_amount,
            payload.qr_payload,
            payload.ocr_text,
            payload.parse_confidence,
        )
    ):
        record.parse_status = "reviewed" if payload.mark_confirmed else "parsed"

    if payload.mark_confirmed:
        missing = []
        if not record.contractor_full_name:
            missing.append("ФИО")
        if not record.iin:
            missing.append("ИИН")
        if record.receipt_amount is None:
            missing.append("сумма")
        if not record.service_name:
            missing.append("услуга")
        if missing:
            raise HTTPException(
                status_code=400,
                detail="Для подтверждения заполните: " + ", ".join(missing),
            )
        record.parse_status = "reviewed"
        record.confirmed_at = datetime.utcnow()
        record.confirmed_by_user_id = current_user.id

    record.updated_at = datetime.utcnow()
    db.add(record)
    db.commit()
    return load_row(db, request.id)


@router.get("/{request_id}/receipt")
def download_self_employed_receipt(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    get_request_or_404(db, request_id)

    row = db.execute(
        select(
            SelfEmployedAccounting.receipt_data,
            SelfEmployedAccounting.receipt_filename,
            SelfEmployedAccounting.receipt_content_type,
        ).where(SelfEmployedAccounting.payment_request_id == int(request_id))
    ).one_or_none()
    if row is None or row.receipt_data is None:
        raise HTTPException(status_code=404, detail="Чек не загружен")

    filename = Path(row.receipt_filename or "receipt").name.replace('\"', "")
    ascii_name = "receipt" + (Path(filename).suffix or "")
    encoded_name = quote(filename, safe="")
    headers = {
        "Content-Disposition": f"inline; filename={ascii_name}; filename*=UTF-8''{encoded_name}",
        "Cache-Control": "private, no-store",
    }
    return Response(
        content=row.receipt_data,
        media_type=row.receipt_content_type or "application/octet-stream",
        headers=headers,
    )
