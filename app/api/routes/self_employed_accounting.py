from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.r1_profile import R1_CUSTOMER_PROFILE
from app.models.event import Event
from app.models.payment_request import PaymentRequest
from app.models.self_employed_accounting import SelfEmployedAccounting
from app.models.self_employed_accounting_request import SelfEmployedAccountingRequest
from app.models.user import User
from app.schemas.self_employed_accounting import (
    SelfEmployedAccountingAttachCreate,
    SelfEmployedAccountingGroupCreate,
    SelfEmployedAccountingMemberRead,
    SelfEmployedAccountingRead,
    SelfEmployedAccountingUpdate,
    SelfEmployedReceiptImportRead,
    R1CustomerProfileRead,
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


def clean_decimal(value: str | Decimal | None) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).replace(" ", "").replace(",", ".")
    try:
        result = Decimal(raw).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Некорректная сумма чека") from exc
    if result < 0:
        raise HTTPException(status_code=400, detail="Сумма чека не может быть отрицательной")
    return result


def clean_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректная дата чека") from exc


def is_active_request(request: PaymentRequest, event: Event, *, require_visible: bool = True) -> bool:
    return (
        request.payment_method == "self_employed"
        and request.status not in INACTIVE_REQUEST_STATUSES
        and getattr(request, "money_status", None) != "cancelled"
        and event.status != "cancelled"
        and (not require_visible or bool(getattr(request, "self_employed_accounting_visible", False)))
    )


def get_request_or_404(
    db: Session,
    request_id: int,
    *,
    require_active: bool = True,
    require_visible: bool = True,
) -> tuple[PaymentRequest, Event]:
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
    if require_visible and not getattr(request, "self_employed_accounting_visible", False):
        raise HTTPException(status_code=409, detail="Эта историческая заявка не участвует в новой бухгалтерии")
    if require_active and not is_active_request(request, event, require_visible=require_visible):
        raise HTTPException(status_code=409, detail="Отменённая заявка не участвует в бухгалтерии")
    return request, event


def find_record_for_request(db: Session, request_id: int) -> SelfEmployedAccounting | None:
    # Since 0015 membership is the source of truth. Do not fall back to the old
    # payment_request_id anchor: detaching a request from a receipt must stay detached.
    return db.execute(
        select(SelfEmployedAccounting)
        .join(
            SelfEmployedAccountingRequest,
            SelfEmployedAccountingRequest.accounting_id == SelfEmployedAccounting.id,
        )
        .where(SelfEmployedAccountingRequest.payment_request_id == int(request_id))
    ).scalar_one_or_none()


def get_record_or_404(db: Session, accounting_id: int, *, lock: bool = False) -> SelfEmployedAccounting:
    query = select(SelfEmployedAccounting).where(SelfEmployedAccounting.id == int(accounting_id))
    if lock:
        query = query.with_for_update()
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Бухгалтерская строка не найдена")
    return record


def get_or_create_record(db: Session, request_id: int) -> SelfEmployedAccounting:
    record = find_record_for_request(db, request_id)
    if record is not None:
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


def create_standalone_record(db: Session) -> SelfEmployedAccounting:
    record = SelfEmployedAccounting(
        payment_request_id=None,
        parse_status="empty",
        act_status="not_created",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(record)
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


def _surname_key(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    letters = "".join(ch if ch.isalpha() or ch in "-'" else " " for ch in text.casefold())
    tokens = [token.strip("-'") for token in letters.split() if len(token.strip("-'")) >= 2]
    return tokens[0] if tokens else None


def _visible_active_member_query():
    return (
        select(PaymentRequest, Event, User.name)
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(User, User.id == Event.manager_id)
        .where(
            PaymentRequest.payment_method == "self_employed",
            PaymentRequest.self_employed_accounting_visible.is_(True),
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
    )


def _members_for_record(db: Session, accounting_id: int) -> list[tuple[PaymentRequest, Event, str | None]]:
    member_ids = db.execute(
        select(SelfEmployedAccountingRequest.payment_request_id).where(
            SelfEmployedAccountingRequest.accounting_id == int(accounting_id)
        )
    ).scalars().all()
    if not member_ids:
        return []
    return list(
        db.execute(
            _visible_active_member_query().where(PaymentRequest.id.in_(member_ids))
        ).all()
    )


def _member_rows(members: list[tuple[PaymentRequest, Event, str | None]]) -> list[SelfEmployedAccountingMemberRead]:
    return [
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


def _receipt_fields(record: SelfEmployedAccounting | None) -> dict:
    return {
        "receipt_filename": record.receipt_filename if record else None,
        "receipt_content_type": record.receipt_content_type if record else None,
        "receipt_size": record.receipt_size if record else None,
        "receipt_sha256": record.receipt_sha256 if record else None,
        "receipt_uploaded_at": record.receipt_uploaded_at if record else None,
        "has_receipt": bool(record and record.receipt_filename and record.receipt_size),
        "contractor_full_name": record.contractor_full_name if record else None,
        "iin": record.iin if record else None,
        "receipt_number": record.receipt_number if record else None,
        "receipt_datetime": record.receipt_datetime if record else None,
        "service_name": record.service_name if record else None,
        "receipt_amount": record.receipt_amount if record else None,
        "qr_payload": record.qr_payload if record else None,
        "ocr_text": record.ocr_text if record else None,
        "parse_confidence": record.parse_confidence if record else None,
        "parse_status": record.parse_status if record else "empty",
        "confirmed_at": record.confirmed_at if record else None,
        "act_status": record.act_status if record else "not_created",
    }


def build_row(
    members: list[tuple[PaymentRequest, Event, str | None]],
    record: SelfEmployedAccounting | None,
) -> SelfEmployedAccountingRead:
    if not members:
        if record is None:
            raise ValueError("Standalone accounting row requires a record")
        return SelfEmployedAccountingRead(
            row_key=f"accounting:{record.id}",
            row_kind="receipt",
            is_receipt_only=True,
            payment_request_id=None,
            payment_request_ids=[],
            request_count=0,
            accounting_id=record.id,
            is_grouped=False,
            members=[],
            request_amount=Decimal("0.00"),
            request_status="unlinked",
            money_status=None,
            request_created_at=record.receipt_uploaded_at or record.created_at,
            **_receipt_fields(record),
        )

    members = sorted(members, key=lambda item: (item[0].created_at, item[0].id))
    anchor_request, anchor_event, _ = members[0]
    total = sum((Decimal(item[0].amount_requested) for item in members), Decimal("0.00"))
    request_ids = [item[0].id for item in members]
    request_statuses = [item[0].status for item in members]
    money_statuses = [getattr(item[0], "money_status", "waiting_money") for item in members]
    item_names = [request.item_name_snapshot for request, _, _ in members]
    comments = [request.comment for request, _, _ in members]
    contractor_names = [request.contractor_name_snapshot for request, _, _ in members]

    return SelfEmployedAccountingRead(
        row_key=f"accounting:{record.id}" if record else f"request:{anchor_request.id}",
        row_kind="request",
        is_receipt_only=False,
        payment_request_id=anchor_request.id,
        payment_request_ids=request_ids,
        request_count=len(request_ids),
        accounting_id=record.id if record else None,
        is_grouped=len(request_ids) > 1,
        members=_member_rows(members),
        event_id=anchor_event.id,
        event_title=_same_or_summary(
            [event.title for _, event, _ in members],
            f"{len(set(event.id for _, event, _ in members))} мероприятий",
        ),
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
        **_receipt_fields(record),
    )


def load_accounting_row(db: Session, accounting_id: int) -> SelfEmployedAccountingRead:
    record = get_record_or_404(db, accounting_id)
    return build_row(_members_for_record(db, record.id), record)


def load_group_row(db: Session, request_id: int) -> SelfEmployedAccountingRead:
    request, _ = get_request_or_404(db, request_id)
    record = find_record_for_request(db, request.id)
    if record is None:
        member = db.execute(_visible_active_member_query().where(PaymentRequest.id == request.id)).one_or_none()
        if member is None:
            raise HTTPException(status_code=404, detail="Заявка не найдена в бухгалтерии")
        return build_row([member], None)
    return load_accounting_row(db, record.id)


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


def _row_matches_accounting_month(
    row: SelfEmployedAccountingRead,
    month_bounds: tuple[date, date],
) -> bool:
    start, end = month_bounds
    if row.has_receipt and row.receipt_datetime:
        return start <= row.receipt_datetime.date() < end
    if row.has_receipt and not row.receipt_datetime:
        return bool(row.event_date and start <= row.event_date < end)
    return bool(row.event_date and start <= row.event_date < end)


def _month_bounds(month: str) -> tuple[date, date]:
    try:
        year_part, month_part = month.split("-")[:2]
        year_num = int(year_part)
        month_num = int(month_part)
        if not 1 <= month_num <= 12:
            raise ValueError
    except Exception as exc:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM") from exc
    start = date(year_num, month_num, 1)
    end = date(year_num + 1, 1, 1) if month_num == 12 else date(year_num, month_num + 1, 1)
    return start, end


@router.get("/r1/customer-profile", response_model=R1CustomerProfileRead)
def get_r1_customer_profile(
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    return R1CustomerProfileRead(**R1_CUSTOMER_PROFILE)


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
            PaymentRequest.self_employed_accounting_visible.is_(True),
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
    )

    # Do not filter request-backed rows by the event date in SQL. Once a receipt
    # exists, accounting belongs to the month printed on that receipt, even when
    # the event/request lives in another month. We therefore build rows first and
    # apply the accounting-month rule below.
    month_bounds = _month_bounds(month) if month else None

    rows = db.execute(query).all()
    grouped_members: dict[tuple[str, int], list[tuple[PaymentRequest, Event, str | None]]] = defaultdict(list)
    records: dict[tuple[str, int], SelfEmployedAccounting | None] = {}
    for request, event, manager_name, accounting_id, record in rows:
        key = ("accounting", int(accounting_id)) if accounting_id is not None else ("request", int(request.id))
        grouped_members[key].append((request, event, manager_name))
        records[key] = record

    result = [build_row(members, records.get(key)) for key, members in grouped_members.items()]

    if month_bounds:
        # A real e-Salyq receipt date is the source of truth for accounting
        # period. Rows still waiting for a receipt remain discoverable by event
        # month so the accountant can attach the future receipt.
        result = [row for row in result if _row_matches_accounting_month(row, month_bounds)]

    # Receipt-first workflow: imported checks can exist before a request is found.
    no_members = ~exists(
        select(SelfEmployedAccountingRequest.id).where(
            SelfEmployedAccountingRequest.accounting_id == SelfEmployedAccounting.id
        )
    )
    standalone_query = select(SelfEmployedAccounting).where(
        no_members,
        SelfEmployedAccounting.receipt_filename.is_not(None),
    )
    standalone_records = db.execute(standalone_query).scalars().all()
    for record in standalone_records:
        if month_bounds:
            # Standalone imported receipts are distributed strictly by the issue
            # date read from the receipt. If OCR did not read a date yet, keep the
            # row in the month of upload until it is corrected manually.
            probe = record.receipt_datetime or record.receipt_uploaded_at or record.created_at
            if probe and not (month_bounds[0] <= probe.date() < month_bounds[1]):
                continue
        result.append(build_row([], record))

    def sort_key(row: SelfEmployedAccountingRead):
        probe = row.receipt_datetime or row.request_created_at or row.receipt_uploaded_at or datetime.min
        return (probe, row.accounting_id or 0, row.payment_request_id or 0)

    result.sort(key=sort_key, reverse=True)
    return result


@router.post("/groups", response_model=SelfEmployedAccountingRead)
def group_self_employed_requests(
    payload: SelfEmployedAccountingGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Legacy checkbox grouping remains available to old clients; drag/drop is preferred."""
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
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Заявка №{request.id} не участвует в новой бухгалтерии")

    existing_links = db.execute(
        select(SelfEmployedAccountingRequest).where(
            SelfEmployedAccountingRequest.payment_request_id.in_(requested_ids)
        )
    ).scalars().all()
    source_group_ids = sorted({link.accounting_id for link in existing_links})
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
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Группа содержит неактивную заявку №{request.id}")
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
        raise HTTPException(status_code=409, detail="Нельзя объединить строки, у которых уже есть разные чеки")
    destination = meaningful[0] if meaningful else (source_records[0] if source_records else None)
    if destination is not None and destination.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя менять состав строки после формирования АВР")
    if destination is None:
        destination = SelfEmployedAccounting(
            payment_request_id=requested_ids[0],
            parse_status="empty",
            act_status="not_created",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(destination)
        db.flush()

    if source_group_ids:
        links = db.execute(
            select(SelfEmployedAccountingRequest).where(
                SelfEmployedAccountingRequest.accounting_id.in_(source_group_ids)
            )
        ).scalars().all()
        for link in links:
            link.accounting_id = destination.id
            db.add(link)

    linked = set(
        db.execute(
            select(SelfEmployedAccountingRequest.payment_request_id).where(
                SelfEmployedAccountingRequest.accounting_id == destination.id
            )
        ).scalars().all()
    )
    for request_id in sorted(all_request_ids):
        if request_id not in linked:
            db.add(SelfEmployedAccountingRequest(accounting_id=destination.id, payment_request_id=request_id))
    db.flush()
    for record in source_records:
        if record.id != destination.id:
            db.delete(record)
    if record_has_business_data(destination):
        if destination.receipt_filename and destination.parse_status == "reviewed":
            destination.parse_status = "parsed"
        destination.confirmed_at = None
        destination.confirmed_by_user_id = None
    destination.updated_at = datetime.utcnow()
    db.add(destination)
    db.commit()
    return load_accounting_row(db, destination.id)


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
        raise HTTPException(status_code=409, detail="Строку с чеком разъединяйте кнопками «Отвязать» у заявок")
    count = len(member_ids)
    db.delete(record)
    db.commit()
    return {"ok": True, "split": count}


def _save_receipt_binary(
    db: Session,
    record: SelfEmployedAccounting,
    *,
    content: bytes,
    filename: str,
    content_type: str,
    current_user: User,
) -> None:
    digest = sha256(content).hexdigest()
    duplicate = db.execute(
        select(SelfEmployedAccounting.id).where(
            SelfEmployedAccounting.receipt_sha256 == digest,
            SelfEmployedAccounting.id != record.id,
        ).limit(1)
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail=f"Этот файл чека уже загружен (строка #{duplicate})")
    record.receipt_filename = Path(filename or "receipt").name[:255]
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


def _apply_import_metadata(
    record: SelfEmployedAccounting,
    *,
    contractor_full_name: str | None,
    iin: str | None,
    receipt_number: str | None,
    receipt_datetime: str | None,
    service_name: str | None,
    receipt_amount: str | None,
    qr_payload: str | None,
    ocr_text: str | None,
    parse_confidence: str | None,
) -> None:
    record.contractor_full_name = clean_text(contractor_full_name, 255)
    record.iin = clean_iin(iin)
    record.receipt_number = clean_text(receipt_number, 80)
    record.receipt_datetime = clean_datetime(receipt_datetime)
    record.service_name = clean_text(service_name)
    record.receipt_amount = clean_decimal(receipt_amount)
    record.qr_payload = str(qr_payload)[:10000] if qr_payload else None
    record.ocr_text = str(ocr_text)[:50000] if ocr_text else None
    if parse_confidence not in {None, ""}:
        try:
            confidence = Decimal(str(parse_confidence))
        except InvalidOperation:
            confidence = Decimal("0")
        record.parse_confidence = max(Decimal("0"), min(Decimal("100"), confidence))
    if any([
        record.contractor_full_name,
        record.iin,
        record.receipt_number,
        record.receipt_datetime,
        record.service_name,
        record.receipt_amount is not None,
        record.qr_payload,
        record.ocr_text,
    ]):
        record.parse_status = "parsed"


def _unreceipted_candidate_groups(db: Session) -> list[tuple[list[PaymentRequest], SelfEmployedAccounting | None]]:
    rows = db.execute(
        select(PaymentRequest, Event, SelfEmployedAccountingRequest.accounting_id, SelfEmployedAccounting)
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(
            SelfEmployedAccountingRequest,
            SelfEmployedAccountingRequest.payment_request_id == PaymentRequest.id,
        )
        .outerjoin(SelfEmployedAccounting, SelfEmployedAccounting.id == SelfEmployedAccountingRequest.accounting_id)
        .where(
            PaymentRequest.payment_method == "self_employed",
            PaymentRequest.self_employed_accounting_visible.is_(True),
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
    ).all()
    grouped: dict[tuple[str, int], list[PaymentRequest]] = defaultdict(list)
    records: dict[tuple[str, int], SelfEmployedAccounting | None] = {}
    for request, _event, accounting_id, record in rows:
        key = ("accounting", int(accounting_id)) if accounting_id is not None else ("request", int(request.id))
        grouped[key].append(request)
        records[key] = record
    result = []
    for key, requests in grouped.items():
        record = records.get(key)
        if record and record.receipt_filename:
            continue
        result.append((requests, record))
    return result


def _auto_match_receipt(
    db: Session,
    contractor_full_name: str | None,
    receipt_amount: Decimal | None,
) -> tuple[SelfEmployedAccounting | None, str, list[int]]:
    surname = _surname_key(contractor_full_name)
    if not surname or receipt_amount is None:
        return None, "unmatched", []

    matches: list[tuple[list[PaymentRequest], SelfEmployedAccounting | None]] = []
    for requests, record in _unreceipted_candidate_groups(db):
        total = sum((Decimal(request.amount_requested) for request in requests), Decimal("0.00")).quantize(Decimal("0.01"))
        if total != receipt_amount:
            continue
        request_surnames = {_surname_key(request.contractor_name_snapshot) for request in requests}
        request_surnames.discard(None)
        if surname in request_surnames:
            matches.append((requests, record))

    if len(matches) != 1:
        return None, "ambiguous" if len(matches) > 1 else "unmatched", []

    requests, record = matches[0]
    if record is None:
        record = get_or_create_record(db, requests[0].id)
    return record, "matched", [request.id for request in requests]


@router.post("/receipts/import", response_model=SelfEmployedReceiptImportRead)
async def import_self_employed_receipt(
    file: UploadFile = File(...),
    contractor_full_name: str | None = Form(default=None),
    iin: str | None = Form(default=None),
    receipt_number: str | None = Form(default=None),
    receipt_datetime: str | None = Form(default=None),
    service_name: str | None = Form(default=None),
    receipt_amount: str | None = Form(default=None),
    qr_payload: str | None = Form(default=None),
    ocr_text: str | None = Form(default=None),
    parse_confidence: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    content_type = (file.content_type or "").lower().split(";", 1)[0].strip()
    if content_type not in ALLOWED_RECEIPT_TYPES:
        raise HTTPException(status_code=400, detail="Поддерживаются JPG, PNG, WEBP и PDF")
    content = await file.read(MAX_RECEIPT_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(content) > MAX_RECEIPT_BYTES:
        raise HTTPException(status_code=413, detail="Чек слишком большой. Максимум 10 МБ")

    normalized_amount = clean_decimal(receipt_amount)
    record, match_status, matched_ids = _auto_match_receipt(db, contractor_full_name, normalized_amount)
    if record is None:
        record = create_standalone_record(db)

    _save_receipt_binary(
        db,
        record,
        content=content,
        filename=file.filename or "receipt",
        content_type=content_type,
        current_user=current_user,
    )
    _apply_import_metadata(
        record,
        contractor_full_name=contractor_full_name,
        iin=iin,
        receipt_number=receipt_number,
        receipt_datetime=receipt_datetime,
        service_name=service_name,
        receipt_amount=receipt_amount,
        qr_payload=qr_payload,
        ocr_text=ocr_text,
        parse_confidence=parse_confidence,
    )
    db.add(record)
    db.commit()

    if match_status == "matched":
        message = f"Чек автоматически привязан к заявке{'м' if len(matched_ids) > 1 else ''} №" + ", №".join(str(i) for i in matched_ids)
    elif match_status == "ambiguous":
        message = "Есть несколько заявок с такой фамилией и суммой — чек оставлен отдельной строкой"
    else:
        message = "Точного совпадения фамилии и суммы нет — чек создан отдельной строкой"
    return SelfEmployedReceiptImportRead(
        row=load_accounting_row(db, record.id),
        match_status=match_status,
        matched_request_ids=matched_ids,
        message=message,
    )


@router.post("/receipts/{accounting_id}/attach", response_model=SelfEmployedAccountingRead)
def attach_requests_to_receipt(
    accounting_id: int,
    payload: SelfEmployedAccountingAttachCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    target = get_record_or_404(db, accounting_id, lock=True)
    if not target.receipt_filename:
        raise HTTPException(status_code=409, detail="Перетаскивать заявки можно только на строку с чеком")
    if target.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя менять состав после формирования АВР")

    request_ids = list(dict.fromkeys(int(value) for value in payload.request_ids))
    rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(request_ids))
    ).all()
    if len(rows) != len(request_ids):
        raise HTTPException(status_code=404, detail="Одна из заявок не найдена")
    for request, event in rows:
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Заявка №{request.id} не участвует в новой бухгалтерии")

    source_ids: set[int] = set()
    for request_id in request_ids:
        source = find_record_for_request(db, request_id)
        if source is None or source.id == target.id:
            continue
        source = get_record_or_404(db, source.id, lock=True)
        if source.receipt_filename:
            raise HTTPException(status_code=409, detail="Нельзя перетащить строку, у которой уже есть другой чек")
        if source.act_status not in {None, "", "not_created"}:
            raise HTTPException(status_code=409, detail="Нельзя переносить заявку после формирования АВР")
        source_ids.add(source.id)

    # Move all members of a source request group, not only its anchor row.
    expanded_request_ids = set(request_ids)
    if source_ids:
        expanded_request_ids.update(
            db.execute(
                select(SelfEmployedAccountingRequest.payment_request_id).where(
                    SelfEmployedAccountingRequest.accounting_id.in_(source_ids)
                )
            ).scalars().all()
        )

    expanded_rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(sorted(expanded_request_ids)))
    ).all()
    for request, event in expanded_rows:
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Группа содержит неактивную заявку №{request.id}")

    links = db.execute(
        select(SelfEmployedAccountingRequest).where(
            SelfEmployedAccountingRequest.payment_request_id.in_(sorted(expanded_request_ids))
        )
    ).scalars().all()
    linked_ids = {link.payment_request_id for link in links}
    for link in links:
        link.accounting_id = target.id
        db.add(link)
    for request_id in sorted(expanded_request_ids - linked_ids):
        db.add(SelfEmployedAccountingRequest(accounting_id=target.id, payment_request_id=request_id))
    db.flush()

    # Source rows without receipts become redundant after their requests moved.
    for source_id in source_ids:
        source = db.get(SelfEmployedAccounting, source_id)
        if source is not None:
            remaining = db.execute(
                select(SelfEmployedAccountingRequest.id).where(
                    SelfEmployedAccountingRequest.accounting_id == source_id
                ).limit(1)
            ).scalar_one_or_none()
            if remaining is None:
                db.delete(source)

    target.confirmed_at = None
    target.confirmed_by_user_id = None
    if target.parse_status == "reviewed":
        target.parse_status = "parsed"
    target.updated_at = datetime.utcnow()
    db.add(target)
    db.commit()
    return load_accounting_row(db, target.id)


@router.delete("/receipts/{accounting_id}/requests/{request_id}", response_model=SelfEmployedAccountingRead)
def detach_request_from_receipt(
    accounting_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    target = get_record_or_404(db, accounting_id, lock=True)
    get_request_or_404(db, request_id)
    if target.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя менять состав после формирования АВР")
    link = db.execute(
        select(SelfEmployedAccountingRequest).where(
            SelfEmployedAccountingRequest.accounting_id == target.id,
            SelfEmployedAccountingRequest.payment_request_id == int(request_id),
        )
    ).scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Эта заявка не привязана к чеку")
    db.delete(link)
    # payment_request_id is only a legacy anchor from 0014. Membership is the
    # source of truth now; clear the anchor when that request is detached so the
    # request can later receive a different receipt without hitting the old
    # unique constraint.
    if target.payment_request_id == int(request_id):
        target.payment_request_id = None
    target.confirmed_at = None
    target.confirmed_by_user_id = None
    if target.parse_status == "reviewed":
        target.parse_status = "parsed"
    target.updated_at = datetime.utcnow()
    db.add(target)
    db.commit()
    return load_accounting_row(db, target.id)


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
    _save_receipt_binary(
        db,
        record,
        content=content,
        filename=file.filename or "receipt",
        content_type=content_type,
        current_user=current_user,
    )
    db.add(record)
    db.commit()
    return load_group_row(db, request_id)


def _update_record(record: SelfEmployedAccounting, payload: SelfEmployedAccountingUpdate, current_user: User) -> None:
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
        record.receipt_amount = clean_decimal(payload.receipt_amount)
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
            raise HTTPException(status_code=400, detail="Для подтверждения заполните: " + ", ".join(missing))
        record.parse_status = "reviewed"
        record.confirmed_at = datetime.utcnow()
        record.confirmed_by_user_id = current_user.id
    record.updated_at = datetime.utcnow()


@router.patch("/receipts/{accounting_id}", response_model=SelfEmployedAccountingRead)
def update_receipt_accounting(
    accounting_id: int,
    payload: SelfEmployedAccountingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    record = get_record_or_404(db, accounting_id, lock=True)
    _update_record(record, payload, current_user)
    db.add(record)
    db.commit()
    return load_accounting_row(db, record.id)


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
    _update_record(record, payload, current_user)
    db.add(record)
    db.commit()
    return load_group_row(db, request.id)


def _receipt_response(db: Session, record: SelfEmployedAccounting) -> Response:
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
    return Response(
        content=row.receipt_data,
        media_type=row.receipt_content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename={ascii_name}; filename*=UTF-8''{encoded_name}",
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/receipts/{accounting_id}/file")
def download_accounting_receipt_by_id(
    accounting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    return _receipt_response(db, get_record_or_404(db, accounting_id))


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
    return _receipt_response(db, record)
