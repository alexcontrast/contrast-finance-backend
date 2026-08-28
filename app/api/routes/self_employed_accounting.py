from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.payment_request import PaymentRequest
from app.models.self_employed_accounting import SelfEmployedAccounting
from app.models.self_employed_accounting_request import SelfEmployedAccountingRequest
from app.models.user import User
from app.schemas.self_employed_accounting import (
    SelfEmployedAccountingGroupCreate,
    SelfEmployedAccountingMemberRead,
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
INACTIVE_REQUEST_STATUSES = {"cancelled", "rejected"}


def require_accounting_access(user: User) -> None:
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


def is_active_request(request: PaymentRequest, event: Event) -> bool:
    return (
        request.payment_method == "self_employed"
        and request.status not in INACTIVE_REQUEST_STATUSES
        and getattr(request, "money_status", None) != "cancelled"
        and event.status != "cancelled"
    )


def get_request_or_404(db: Session, request_id: int, *, require_active: bool = True) -> tuple[PaymentRequest, Event]:
    row = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id == int(request_id))
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    request, event = row
    if request.payment_method != "self_employed":
        raise HTTPException(status_code=409, detail="Эта заявка не относится к Самозанятым")
    if require_active and not is_active_request(request, event):
        raise HTTPException(status_code=409, detail="Отменённая заявка не участвует в бухгалтерии")
    return request, event


def find_record_for_request(db: Session, request_id: int) -> SelfEmployedAccounting | None:
    record = db.execute(
        select(SelfEmployedAccounting)
        .join(
            SelfEmployedAccountingRequest,
            SelfEmployedAccountingRequest.accounting_id == SelfEmployedAccounting.id,
        )
        .where(SelfEmployedAccountingRequest.payment_request_id == int(request_id))
    ).scalar_one_or_none()
    if record is not None:
        return record

    # Defensive compatibility for a DB that was started on 0014 and receives a
    # write before 0015's membership backfill for some reason.
    legacy = db.execute(
        select(SelfEmployedAccounting).where(SelfEmployedAccounting.payment_request_id == int(request_id))
    ).scalar_one_or_none()
    if legacy is not None:
        existing_link = db.execute(
            select(SelfEmployedAccountingRequest.id).where(
                SelfEmployedAccountingRequest.payment_request_id == int(request_id)
            )
        ).scalar_one_or_none()
        if existing_link is None:
            db.add(
                SelfEmployedAccountingRequest(
                    accounting_id=legacy.id,
                    payment_request_id=int(request_id),
                    created_at=datetime.utcnow(),
                )
            )
            db.flush()
        return legacy
    return None


def get_or_create_record(db: Session, request_id: int) -> SelfEmployedAccounting:
    record = find_record_for_request(db, request_id)
    if record is not None:
        # Lock the shared accounting row after resolving membership.
        return db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id == record.id)
            .with_for_update()
        ).scalar_one()

    record = SelfEmployedAccounting(
        payment_request_id=int(request_id),
        parse_status="empty",
        act_status="not_created",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(record)
    db.flush()
    db.add(
        SelfEmployedAccountingRequest(
            accounting_id=record.id,
            payment_request_id=int(request_id),
            created_at=datetime.utcnow(),
        )
    )
    db.flush()
    return record


def record_has_business_data(record: SelfEmployedAccounting) -> bool:
    return bool(
        record.receipt_filename
        or record.receipt_sha256
        or record.contractor_full_name
        or record.iin
        or record.receipt_number
        or record.receipt_datetime
        or record.service_name
        or record.receipt_amount is not None
        or record.qr_payload
        or record.ocr_text
        or record.parse_status not in {None, "", "empty"}
        or record.confirmed_at
        or record.act_status not in {None, "", "not_created"}
    )


def _same_or_summary(values: list[str | None], summary: str) -> str | None:
    clean = [str(value).strip() for value in values if value and str(value).strip()]
    unique = list(dict.fromkeys(clean))
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return summary


def build_row(
    members: list[tuple[PaymentRequest, Event, str | None]],
    record: SelfEmployedAccounting | None,
) -> SelfEmployedAccountingRead:
    if not members:
        raise ValueError("Accounting group must contain at least one active request")

    members = sorted(members, key=lambda item: (item[0].created_at, item[0].id))
    anchor_request, anchor_event, _ = members[0]
    total = sum((Decimal(item[0].amount_requested) for item in members), Decimal("0.00"))
    request_ids = [item[0].id for item in members]
    request_statuses = [item[0].status for item in members]
    money_statuses = [getattr(item[0], "money_status", "waiting_money") for item in members]

    member_rows = [
        SelfEmployedAccountingMemberRead(
            payment_request_id=request.id,
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
            request_iin=request.iin_bin_snapshot,
            request_comment=request.comment,
        )
        for request, event, manager_name in members
    ]

    item_names = [request.item_name_snapshot for request, _, _ in members]
    comments = [request.comment for request, _, _ in members]
    contractor_names = [request.contractor_name_snapshot for request, _, _ in members]

    return SelfEmployedAccountingRead(
        payment_request_id=anchor_request.id,
        payment_request_ids=request_ids,
        request_count=len(request_ids),
        accounting_id=record.id if record else None,
        is_grouped=len(request_ids) > 1,
        members=member_rows,
        event_id=anchor_event.id,
        event_title=_same_or_summary([event.title for _, event, _ in members], f"{len(set(event.id for _, event, _ in members))} мероприятий"),
        event_date=min((event.event_date for _, event, _ in members if event.event_date), default=None),
        client_name=_same_or_summary([event.client_name for _, event, _ in members], "Несколько клиентов"),
        manager_name=_same_or_summary([manager for _, _, manager in members], "Несколько менеджеров"),
        request_created_at=max(request.created_at for request, _, _ in members),
        request_status=request_statuses[0] if len(set(request_statuses)) == 1 else "mixed",
        money_status=money_statuses[0] if len(set(money_statuses)) == 1 else "mixed",
        request_amount=total,
        item_name=" + ".join(dict.fromkeys(name for name in item_names if name)) or None,
        request_contractor_name=_same_or_summary(contractor_names, "Самозанятый"),
        request_iin=_same_or_summary([request.iin_bin_snapshot for request, _, _ in members], ""),
        request_comment=" · ".join(dict.fromkeys(comment for comment in comments if comment)) or None,
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


def _active_member_query():
    return (
        select(PaymentRequest, Event, User.name)
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(User, User.id == Event.manager_id)
        .where(
            PaymentRequest.payment_method == "self_employed",
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
    )


def load_group_row(db: Session, request_id: int) -> SelfEmployedAccountingRead:
    request, _ = get_request_or_404(db, request_id)
    record = find_record_for_request(db, request.id)
    if record is None:
        member = db.execute(_active_member_query().where(PaymentRequest.id == request.id)).one_or_none()
        if member is None:
            raise HTTPException(status_code=404, detail="Заявка не найдена в бухгалтерии")
        return build_row([member], None)

    member_ids = db.execute(
        select(SelfEmployedAccountingRequest.payment_request_id).where(
            SelfEmployedAccountingRequest.accounting_id == record.id
        )
    ).scalars().all()
    members = db.execute(
        _active_member_query().where(PaymentRequest.id.in_(member_ids))
    ).all()
    if not members:
        raise HTTPException(status_code=404, detail="В группе нет активных заявок")
    return build_row(list(members), record)


def _contractor_identity(requests: list[PaymentRequest]) -> tuple[str | None, str | None]:
    iins = {
        "".join(ch for ch in str(request.iin_bin_snapshot or "") if ch.isdigit())
        for request in requests
        if request.iin_bin_snapshot
    }
    iins.discard("")
    if len(iins) > 1:
        raise HTTPException(status_code=409, detail="Нельзя объединить заявки разных самозанятых: ИИН не совпадает")

    names = {
        " ".join(str(request.contractor_name_snapshot or "").lower().split())
        for request in requests
        if request.contractor_name_snapshot
    }
    names.discard("")
    if not iins and len(names) > 1:
        raise HTTPException(status_code=409, detail="Нельзя объединить заявки разных самозанятых: ФИО не совпадает")

    return (next(iter(iins), None), next(iter(names), None))


@router.get("", response_model=list[SelfEmployedAccountingRead])
def list_self_employed_accounting(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)

    query = (
        select(
            PaymentRequest,
            Event,
            User.name,
            SelfEmployedAccountingRequest.accounting_id,
            SelfEmployedAccounting,
        )
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(User, User.id == Event.manager_id)
        .outerjoin(
            SelfEmployedAccountingRequest,
            SelfEmployedAccountingRequest.payment_request_id == PaymentRequest.id,
        )
        .outerjoin(
            SelfEmployedAccounting,
            SelfEmployedAccounting.id == SelfEmployedAccountingRequest.accounting_id,
        )
        .where(
            PaymentRequest.payment_method == "self_employed",
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
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
    grouped_members: dict[tuple[str, int], list[tuple[PaymentRequest, Event, str | None]]] = defaultdict(list)
    records: dict[tuple[str, int], SelfEmployedAccounting | None] = {}
    for request, event, manager_name, accounting_id, record in rows:
        key = ("accounting", int(accounting_id)) if accounting_id is not None else ("request", int(request.id))
        grouped_members[key].append((request, event, manager_name))
        records[key] = record

    result = [build_row(members, records.get(key)) for key, members in grouped_members.items()]
    result.sort(key=lambda row: (row.request_created_at, row.payment_request_id), reverse=True)
    return result


@router.post("/groups", response_model=SelfEmployedAccountingRead)
def group_self_employed_requests(
    payload: SelfEmployedAccountingGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    requested_ids = list(dict.fromkeys(int(value) for value in payload.request_ids))
    if len(requested_ids) < 2:
        raise HTTPException(status_code=400, detail="Выберите минимум две заявки")

    selected_rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(requested_ids))
    ).all()
    if len(selected_rows) != len(requested_ids):
        raise HTTPException(status_code=404, detail="Одна из выбранных заявок не найдена")
    for request, event in selected_rows:
        if request.payment_method != "self_employed":
            raise HTTPException(status_code=409, detail=f"Заявка №{request.id} не относится к Самозанятым")
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Заявка №{request.id} отменена и не может входить в чек")

    existing_links = db.execute(
        select(SelfEmployedAccountingRequest).where(
            SelfEmployedAccountingRequest.payment_request_id.in_(requested_ids)
        )
    ).scalars().all()
    source_group_ids = sorted({link.accounting_id for link in existing_links})

    # Selecting an already grouped row means selecting the whole receipt group,
    # not silently tearing one of its requests away from the others.
    all_request_ids = set(requested_ids)
    if source_group_ids:
        all_request_ids.update(
            db.execute(
                select(SelfEmployedAccountingRequest.payment_request_id).where(
                    SelfEmployedAccountingRequest.accounting_id.in_(source_group_ids)
                )
            ).scalars().all()
        )

    all_rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(sorted(all_request_ids)))
    ).all()
    for request, event in all_rows:
        if request.payment_method != "self_employed" or not is_active_request(request, event):
            raise HTTPException(
                status_code=409,
                detail=f"Группа содержит отменённую/неактивную заявку №{request.id}; сначала разъедините группу",
            )
    _contractor_identity([request for request, _ in all_rows])

    source_records = []
    if source_group_ids:
        source_records = db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id.in_(source_group_ids))
            .with_for_update()
        ).scalars().all()

    meaningful = [record for record in source_records if record_has_business_data(record)]
    if len(meaningful) > 1:
        raise HTTPException(
            status_code=409,
            detail="Нельзя объединить группы, в которых уже есть разные чеки или распознанные данные",
        )

    destination = meaningful[0] if meaningful else (source_records[0] if source_records else None)
    if destination is not None and destination.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя менять состав группы после формирования АВР")

    if destination is None:
        anchor_id = requested_ids[0]
        destination = SelfEmployedAccounting(
            payment_request_id=anchor_id,
            parse_status="empty",
            act_status="not_created",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(destination)
        db.flush()

    # Move complete source groups into the destination and add previously
    # ungrouped requests. payment_request_id is unique, so membership itself
    # guarantees that a request cannot belong to two checks.
    if source_group_ids:
        links = db.execute(
            select(SelfEmployedAccountingRequest).where(
                SelfEmployedAccountingRequest.accounting_id.in_(source_group_ids)
            )
        ).scalars().all()
        for link in links:
            link.accounting_id = destination.id
            db.add(link)

    linked_request_ids = set(
        db.execute(
            select(SelfEmployedAccountingRequest.payment_request_id).where(
                SelfEmployedAccountingRequest.accounting_id == destination.id
            )
        ).scalars().all()
    )
    for request_id in sorted(all_request_ids):
        if request_id not in linked_request_ids:
            db.add(
                SelfEmployedAccountingRequest(
                    accounting_id=destination.id,
                    payment_request_id=request_id,
                    created_at=datetime.utcnow(),
                )
            )

    db.flush()
    for record in source_records:
        if record.id != destination.id:
            db.delete(record)
    # Membership changes alter the expected receipt total. Even if the receipt was
    # already reviewed, force a fresh confirmation instead of leaving a stale green
    # status on a different group composition.
    if record_has_business_data(destination):
        destination.parse_status = "parsed" if destination.receipt_filename or destination.contractor_full_name or destination.receipt_amount is not None else "empty"
        destination.confirmed_at = None
        destination.confirmed_by_user_id = None
    destination.updated_at = datetime.utcnow()
    db.add(destination)
    db.commit()
    return load_group_row(db, requested_ids[0])


@router.post("/groups/{request_id}/split")
def split_self_employed_group(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    get_request_or_404(db, request_id)
    record = find_record_for_request(db, request_id)
    if record is None:
        return {"ok": True, "split": 0}

    member_ids = db.execute(
        select(SelfEmployedAccountingRequest.payment_request_id).where(
            SelfEmployedAccountingRequest.accounting_id == record.id
        )
    ).scalars().all()
    if len(member_ids) <= 1:
        return {"ok": True, "split": 0}
    if record_has_business_data(record):
        raise HTTPException(
            status_code=409,
            detail="После загрузки чека или распознавания данных группу нельзя разъединить",
        )

    count = len(member_ids)
    db.delete(record)  # membership rows cascade
    db.commit()
    return {"ok": True, "split": count}


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

    record = get_or_create_record(db, request_id)
    digest = sha256(content).hexdigest()
    duplicate = db.execute(
        select(SelfEmployedAccounting.payment_request_id)
        .where(
            SelfEmployedAccounting.receipt_sha256 == digest,
            SelfEmployedAccounting.id != record.id,
        )
        .limit(1)
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Этот же файл чека уже прикреплён к другой бухгалтерской группе (заявка №{duplicate})",
        )

    record.receipt_filename = Path(file.filename or "receipt").name[:255]
    record.receipt_content_type = content_type
    record.receipt_size = len(content)
    record.receipt_sha256 = digest
    record.receipt_data = content
    record.receipt_uploaded_at = datetime.utcnow()
    record.receipt_uploaded_by_user_id = current_user.id
    record.parse_status = "uploaded"
    record.confirmed_at = None
    record.confirmed_by_user_id = None
    record.updated_at = datetime.utcnow()
    db.add(record)
    db.commit()
    return load_group_row(db, request_id)


@router.patch("/{request_id}", response_model=SelfEmployedAccountingRead)
def update_self_employed_accounting(
    request_id: int,
    payload: SelfEmployedAccountingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    request, _ = get_request_or_404(db, request_id)
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
    return load_group_row(db, request.id)


@router.get("/{request_id}/receipt")
def download_self_employed_receipt(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    get_request_or_404(db, request_id)
    record = find_record_for_request(db, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Чек не загружен")

    row = db.execute(
        select(
            SelfEmployedAccounting.receipt_data,
            SelfEmployedAccounting.receipt_filename,
            SelfEmployedAccounting.receipt_content_type,
        ).where(SelfEmployedAccounting.id == record.id)
    ).one_or_none()
    if row is None or row.receipt_data is None:
        raise HTTPException(status_code=404, detail="Чек не загружен")

    filename = Path(row.receipt_filename or "receipt").name.replace('"', "")
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
