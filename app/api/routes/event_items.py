from datetime import datetime, timezone
from decimal import Decimal
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.event_item import EventItemCreate, EventItemRead
from app.services.auth import get_current_user
from app.services.payment_totals import sync_event_paid_amounts_from_requests, sync_item_paid_amount_from_requests
from app.services.authorization import (
    get_event_or_404,
    get_item_or_404,
    require_event_edit,
    require_event_view,
    require_item_event_view,
)


router = APIRouter(tags=["event_items"])
logger = logging.getLogger(__name__)

INACTIVE_PAYMENT_STATUSES = {"cancelled", "rejected"}
COORDINATOR_ITEM_TYPE = "coordinator"
INVALID_INVOICE_TAX_STATUSES = {None, "", "not_found", "error"}
WEB_DRAFT_ITEM_KEY_PREFIX = "web-draft"


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def calculate_external_amount(payload: EventItemCreate) -> Decimal:
    return money(payload.external_price) * money(payload.external_quantity or Decimal("1.00")) * money(payload.external_days or Decimal("1.00"))


def utc_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(tzinfo=None)


def require_item_revision(item: EventItem, expected_updated_at: datetime | None) -> None:
    if expected_updated_at is None:
        return
    if utc_naive(item.updated_at) != utc_naive(expected_updated_at):
        raise HTTPException(
            status_code=409,
            detail="Позиция уже изменена в другом браузере. Свежая версия не была перезаписана.",
        )


def touch_event(event: Event) -> None:
    event.updated_at = datetime.utcnow()


def require_estimate_editable(current_user: User, event: Event) -> None:
    if current_user.role == "manager" and event.status not in {"draft", "revision"}:
        raise HTTPException(
            status_code=409,
            detail="Смета уже не является черновиком. Обнови мероприятие перед редактированием.",
        )


class EventItemBulkDeletePayload(BaseModel):
    item_ids: list[int]


def _sec(started_at: float) -> float:
    return time.perf_counter() - started_at


def active_item_payment_requests_count(db: Session, item_id: int) -> int:
    return (
        db.query(PaymentRequest)
        .filter(
            PaymentRequest.event_item_id == item_id,
            PaymentRequest.status.notin_(list(INACTIVE_PAYMENT_STATUSES)),
        )
        .count()
    )


def normalized_iin_bin(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def web_draft_item_key(event_id: int, token: str | None) -> str | None:
    normalized = (token or "").strip()
    if not normalized:
        return None
    return f"{WEB_DRAFT_ITEM_KEY_PREFIX}:{int(event_id)}:{normalized}"


def valid_invoice_tax_context(
    iin_bin: str | None,
    iin_bin_locked: bool,
    tax_check_status: str | None,
) -> bool:
    return (
        len(normalized_iin_bin(iin_bin)) == 12
        and bool(iin_bin_locked)
        and tax_check_status not in INVALID_INVOICE_TAX_STATUSES
    )


def latest_active_invoice_request(db: Session, item_id: int) -> PaymentRequest | None:
    requests = db.execute(
        select(PaymentRequest)
        .where(
            PaymentRequest.event_item_id == int(item_id),
            PaymentRequest.payment_method == "invoice",
            PaymentRequest.status.notin_(list(INACTIVE_PAYMENT_STATUSES)),
        )
        .order_by(PaymentRequest.created_at.desc(), PaymentRequest.id.desc())
    ).scalars().all()
    if not requests:
        return None
    return next(
        (
            request
            for request in requests
            if valid_invoice_tax_context(
                request.iin_bin_snapshot,
                True,
                request.tax_status_snapshot,
            )
        ),
        requests[0],
    )


def protected_invoice_tax_context(
    item: EventItem,
    payload: EventItemCreate,
    invoice_request: PaymentRequest | None,
    allow_complete_override: bool = False,
) -> dict | None:
    """
    Keep an already confirmed invoice context when a stale estimate PATCH tries
    to clear it. This can happen when autosave/localStorage/another tab sends an
    older copy after KGD check or after the payment request was created.

    A complete, freshly checked payload is accepted when there is no active
    invoice request. With an active request only an admin override is accepted.
    """
    payload_is_complete = (
        payload.payment_method == "invoice"
        and valid_invoice_tax_context(
            payload.iin_bin,
            payload.iin_bin_locked,
            payload.tax_check_status,
        )
    )
    if payload_is_complete and (
        invoice_request is None
        or allow_complete_override
    ):
        return None

    current_is_complete = (
        item.payment_method == "invoice"
        and valid_invoice_tax_context(
            item.iin_bin,
            item.iin_bin_locked,
            item.tax_check_status,
        )
    )
    if current_is_complete and (
        invoice_request is not None
        or payload.payment_method == "invoice"
    ):
        return {
            "iin_bin": item.iin_bin,
            "tax_check_status": item.tax_check_status,
            "vat_amount": money(item.vat_amount),
            "deduction_amount": money(item.deduction_amount),
        }

    request_is_complete = invoice_request is not None and valid_invoice_tax_context(
        invoice_request.iin_bin_snapshot,
        True,
        invoice_request.tax_status_snapshot,
    )
    if request_is_complete:
        return {
            "iin_bin": invoice_request.iin_bin_snapshot,
            "tax_check_status": invoice_request.tax_status_snapshot,
            "vat_amount": money(invoice_request.vat_amount_snapshot),
            "deduction_amount": money(invoice_request.deduction_amount_snapshot),
        }

    return None


def lock_event_for_estimate_write(db: Session, event_id: int) -> Event:
    """Serialize an estimate mutation with event status/ownership changes."""
    return db.execute(
        select(Event)
        .where(Event.id == int(event_id))
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one()


def active_coordinator_item(
    db: Session,
    event_id: int,
    exclude_item_id: int | None = None,
) -> EventItem | None:
    statement = (
        select(EventItem)
        .where(
            EventItem.event_id == int(event_id),
            EventItem.item_type == COORDINATOR_ITEM_TYPE,
            EventItem.is_deleted == False,  # noqa: E712
        )
        .order_by(EventItem.updated_at.desc(), EventItem.id.desc())
        .with_for_update()
    )
    if exclude_item_id is not None:
        statement = statement.where(EventItem.id != int(exclude_item_id))
    return db.execute(statement).scalars().first()


@router.get("/events/{event_id}/items", response_model=list[EventItemRead])
def list_event_items(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_view(current_user, event, db)

    sync_event_paid_amounts_from_requests(db, event_id)

    result = db.execute(
        select(EventItem)
        .where(EventItem.event_id == event_id, EventItem.is_deleted == False)  # noqa: E712
        .order_by(EventItem.sort_order, EventItem.id)
    )
    return result.scalars().all()


@router.post("/events/{event_id}/items", response_model=EventItemRead)
def create_event_item(
    event_id: int,
    payload: EventItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started_at = time.perf_counter()
    event = get_event_or_404(db, event_id)
    event = lock_event_for_estimate_write(db, event_id)
    require_event_edit(current_user, event)
    require_estimate_editable(current_user, event)
    auth_sec = _sec(started_at)

    if (
        payload.item_type == "regular"
        and not (payload.external_name or "").strip()
        and not (payload.external_note or "").strip()
        and not (payload.internal_note or "").strip()
        and not payload.payment_method
        and not payload.iin_bin
        and money(payload.external_price) == 0
        and money(payload.amount_fact) == 0
        and money(payload.vat_amount) == 0
        and money(payload.deduction_amount) == 0
    ):
        raise HTTPException(status_code=422, detail="Пустая позиция не сохраняется")

    item = None
    coordinator_reused = False
    idempotent_reused = False
    create_key = web_draft_item_key(event_id, payload.client_create_token)

    # Autosave and a manual save can reach POST at almost the same time. The
    # event row was locked above even before the first item exists, so the
    # second request can reuse the browser token and cannot race with Accept.

    if create_key is not None:
        item = db.execute(
            select(EventItem)
            .where(EventItem.legacy_item_key == create_key)
            .with_for_update()
        ).scalar_one_or_none()
        if item is not None:
            if item.event_id != int(event_id) or item.is_deleted:
                raise HTTPException(
                    status_code=409,
                    detail="Эта временная позиция уже была обработана",
                )
            idempotent_reused = True

    if item is None and payload.item_type == COORDINATOR_ITEM_TYPE:
        # Coordinator remains a singleton even for old cached clients that do
        # not yet send a client_create_token.
        item = active_coordinator_item(db, event_id)
        coordinator_reused = item is not None

    if item is None:
        item = EventItem(
            legacy_item_key=create_key,
            event_id=event_id,
            item_type=payload.item_type,
            external_name=payload.external_name,
            external_price=payload.external_price,
            external_quantity=payload.external_quantity,
            external_days=payload.external_days,
            external_amount=calculate_external_amount(payload),
            external_note=payload.external_note,
            amount_fact=payload.amount_fact,
            paid_amount=payload.paid_amount,
            payment_method=payload.payment_method,
            iin_bin=payload.iin_bin,
            iin_bin_locked=payload.iin_bin_locked,
            tax_check_status=payload.tax_check_status,
            vat_amount=payload.vat_amount,
            deduction_amount=payload.deduction_amount,
            internal_note=payload.internal_note,
            sort_order=payload.sort_order,
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    else:
        invoice_request = latest_active_invoice_request(db, item.id)
        invoice_context = protected_invoice_tax_context(
            item,
            payload,
            invoice_request,
            allow_complete_override=current_user.role == "admin",
        )
        item.item_type = payload.item_type
        item.external_name = payload.external_name
        item.external_price = payload.external_price
        item.external_quantity = payload.external_quantity
        item.external_days = payload.external_days
        item.external_amount = calculate_external_amount(payload)
        item.external_note = payload.external_note
        item.amount_fact = payload.amount_fact
        item.payment_method = payload.payment_method
        item.iin_bin = payload.iin_bin
        item.iin_bin_locked = payload.iin_bin_locked
        item.tax_check_status = payload.tax_check_status
        item.vat_amount = payload.vat_amount
        item.deduction_amount = payload.deduction_amount
        item.internal_note = payload.internal_note
        item.sort_order = payload.sort_order
        item.updated_at = datetime.utcnow()
        if invoice_context is not None:
            item.payment_method = "invoice"
            item.iin_bin = invoice_context["iin_bin"]
            item.iin_bin_locked = True
            item.tax_check_status = invoice_context["tax_check_status"]
            item.vat_amount = invoice_context["vat_amount"]
            item.deduction_amount = invoice_context["deduction_amount"]
    build_sec = _sec(started_at) - auth_sec

    db.add(item)
    touch_event(event)
    db.add(event)
    db.flush()
    if coordinator_reused or idempotent_reused:
        # paid_amount is derived from paid requests and must not be overwritten
        # by a stale autosave payload while reusing an existing row.
        sync_item_paid_amount_from_requests(db, item.id)
    flush_sec = _sec(started_at) - auth_sec - build_sec
    result = EventItemRead.model_validate(item)
    response_sec = _sec(started_at) - auth_sec - build_sec - flush_sec
    # The combined "create + KGD check" endpoint defers this commit so the
    # row and its tax result are atomic: a failed external check must not leave
    # an orphan estimate position behind. Normal API calls still commit here.
    if not db.info.get("defer_event_item_create_commit"):
        db.commit()
    commit_sec = _sec(started_at) - auth_sec - build_sec - flush_sec - response_sec

    logger.warning(
        "PERF event-item-create event_id=%s item_id=%s action=%s user_id=%s role=%s auth=%.3fs build=%.3fs flush=%.3fs response=%.3fs commit=%.3fs total=%.3fs",
        event_id,
        item.id,
        "reuse_idempotent" if idempotent_reused else ("reuse_coordinator" if coordinator_reused else "create"),
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
        auth_sec,
        build_sec,
        flush_sec,
        response_sec,
        commit_sec,
        _sec(started_at),
    )
    return result


@router.post("/events/{event_id}/items/bulk-delete")
def bulk_delete_event_items(
    event_id: int,
    payload: EventItemBulkDeletePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started_at = time.perf_counter()
    event = get_event_or_404(db, event_id)
    event = lock_event_for_estimate_write(db, event_id)
    require_event_edit(current_user, event)
    require_estimate_editable(current_user, event)
    auth_sec = _sec(started_at)

    item_ids = []
    seen: set[int] = set()
    for raw_id in payload.item_ids or []:
        try:
            item_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if item_id > 0 and item_id not in seen:
            seen.add(item_id)
            item_ids.append(item_id)

    if not item_ids:
        return {"ok": True, "event_id": event_id, "deleted_item_ids": []}

    active_item_ids = db.execute(
        select(PaymentRequest.event_item_id)
        .where(
            PaymentRequest.event_item_id.in_(item_ids),
            PaymentRequest.status.notin_(list(INACTIVE_PAYMENT_STATUSES)),
        )
        .distinct()
    ).scalars().all()
    active_sql_sec = _sec(started_at) - auth_sec
    if active_item_ids:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить позицию: по ней есть активные заявки на оплату",
        )

    update_started_at = time.perf_counter()
    result = db.execute(
        update(EventItem)
        .where(
            EventItem.event_id == event_id,
            EventItem.id.in_(item_ids),
            EventItem.is_deleted == False,  # noqa: E712
        )
        .values(is_deleted=True, updated_at=datetime.utcnow())
    )
    update_sec = time.perf_counter() - update_started_at
    deleted_count = int(result.rowcount or 0)
    # Удаление строк сметы должно быть идемпотентным. В локальном черновике
    # браузера могут остаться ID позиций, которые уже были удалены ранее
    # (например, после повторного открытия старого черновика). Такие ID не
    # должны блокировать отправку всего мероприятия на проверку.
    missing_count = max(0, len(item_ids) - deleted_count)

    commit_started_at = time.perf_counter()
    if deleted_count:
        touch_event(event)
        db.add(event)
    db.commit()
    commit_sec = time.perf_counter() - commit_started_at

    logger.warning(
        "PERF event-items-bulk-delete event_id=%s user_id=%s role=%s requested=%s deleted=%s auth=%.3fs active_sql=%.3fs update=%.3fs commit=%.3fs total=%.3fs",
        event_id,
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
        len(item_ids),
        deleted_count,
        auth_sec,
        active_sql_sec,
        update_sec,
        commit_sec,
        _sec(started_at),
    )
    return {
        "ok": True,
        "event_id": event_id,
        "deleted_item_ids": item_ids,
        "deleted_count": deleted_count,
        "missing_count": missing_count,
    }


@router.get("/event-items/{item_id}", response_model=EventItemRead)
def get_event_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_or_404(db, item_id)
    require_item_event_view(db, current_user, item)
    return item


@router.patch("/event-items/{item_id}", response_model=EventItemRead)
def update_event_item(
    item_id: int,
    payload: EventItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started_at = time.perf_counter()
    item = get_item_or_404(db, item_id)
    item_sql_sec = _sec(started_at)
    event = lock_event_for_estimate_write(db, item.event_id)
    require_event_edit(current_user, event)
    require_estimate_editable(current_user, event)
    auth_sec = _sec(started_at) - item_sql_sec
    # Serialize ordinary estimate saves with KGD checks and payment creation.
    # Under PostgreSQL READ COMMITTED this reloads the latest committed row after
    # a concurrent writer finishes.
    item = db.execute(
        select(EventItem)
        .where(EventItem.id == int(item_id))
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one()
    require_item_revision(item, payload.expected_updated_at)
    invoice_request = latest_active_invoice_request(db, item.id)
    invoice_context = protected_invoice_tax_context(
        item,
        payload,
        invoice_request,
        allow_complete_override=current_user.role == "admin",
    )

    if payload.item_type == COORDINATOR_ITEM_TYPE:
        conflicting_coordinator = active_coordinator_item(db, item.event_id, exclude_item_id=item.id)
        if conflicting_coordinator is not None:
            raise HTTPException(
                status_code=409,
                detail="В мероприятии уже есть позиция координатора",
            )

    item.item_type = payload.item_type
    item.external_name = payload.external_name
    item.external_price = payload.external_price
    item.external_quantity = payload.external_quantity
    item.external_days = payload.external_days
    item.external_amount = calculate_external_amount(payload)
    item.external_note = payload.external_note
    item.amount_fact = payload.amount_fact
    item.payment_method = payload.payment_method
    item.iin_bin = payload.iin_bin
    item.iin_bin_locked = payload.iin_bin_locked
    item.tax_check_status = payload.tax_check_status
    item.vat_amount = payload.vat_amount
    item.deduction_amount = payload.deduction_amount
    if invoice_context is not None:
        item.payment_method = "invoice"
        item.iin_bin = invoice_context["iin_bin"]
        item.iin_bin_locked = True
        item.tax_check_status = invoice_context["tax_check_status"]
        item.vat_amount = invoice_context["vat_amount"]
        item.deduction_amount = invoice_context["deduction_amount"]
    item.internal_note = payload.internal_note
    item.sort_order = payload.sort_order
    item.updated_at = datetime.utcnow()
    build_sec = _sec(started_at) - item_sql_sec - auth_sec

    db.add(item)
    touch_event(event)
    db.add(event)
    db.flush()
    # paid_amount is derived exclusively from payment requests.
    # Never trust a stale value coming from the estimate form.
    sync_item_paid_amount_from_requests(db, item.id)
    flush_sec = _sec(started_at) - item_sql_sec - auth_sec - build_sec
    result = EventItemRead.model_validate(item)
    response_sec = _sec(started_at) - item_sql_sec - auth_sec - build_sec - flush_sec
    db.commit()
    commit_sec = _sec(started_at) - item_sql_sec - auth_sec - build_sec - flush_sec - response_sec

    logger.warning(
        "PERF event-item-update item_id=%s event_id=%s user_id=%s role=%s item_sql=%.3fs auth=%.3fs build=%.3fs flush=%.3fs response=%.3fs commit=%.3fs total=%.3fs",
        item_id,
        item.event_id,
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
        item_sql_sec,
        auth_sec,
        build_sec,
        flush_sec,
        response_sec,
        commit_sec,
        _sec(started_at),
    )
    return result


@router.delete("/event-items/{item_id}", response_model=EventItemRead)
def delete_event_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started_at = time.perf_counter()
    item = get_item_or_404(db, item_id)
    item_sql_sec = _sec(started_at)
    event = lock_event_for_estimate_write(db, item.event_id)
    require_event_edit(current_user, event)
    require_estimate_editable(current_user, event)
    auth_sec = _sec(started_at) - item_sql_sec

    active_requests_count = active_item_payment_requests_count(db, item.id)
    active_sql_sec = _sec(started_at) - item_sql_sec - auth_sec
    if active_requests_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить позицию: по ней есть активные заявки на оплату",
        )

    item.is_deleted = True
    item.updated_at = datetime.utcnow()

    db.add(item)
    touch_event(event)
    db.add(event)
    db.flush()
    flush_sec = _sec(started_at) - item_sql_sec - auth_sec - active_sql_sec
    result = EventItemRead.model_validate(item)
    response_sec = _sec(started_at) - item_sql_sec - auth_sec - active_sql_sec - flush_sec
    db.commit()
    commit_sec = _sec(started_at) - item_sql_sec - auth_sec - active_sql_sec - flush_sec - response_sec

    logger.warning(
        "PERF event-item-delete item_id=%s event_id=%s user_id=%s role=%s item_sql=%.3fs auth=%.3fs active_sql=%.3fs flush=%.3fs response=%.3fs commit=%.3fs total=%.3fs",
        item_id,
        item.event_id,
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
        item_sql_sec,
        auth_sec,
        active_sql_sec,
        flush_sec,
        response_sec,
        commit_sec,
        _sec(started_at),
    )
    return result
