from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event_item import EventItem
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.event_item import EventItemCreate, EventItemRead
from app.services.auth import get_current_user
from app.services.authorization import (
    get_event_or_404,
    get_item_or_404,
    require_event_edit,
    require_event_view,
    require_item_event_edit,
    require_item_event_view,
)


router = APIRouter(tags=["event_items"])

INACTIVE_PAYMENT_STATUSES = {"cancelled", "rejected"}


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def calculate_external_amount(payload: EventItemCreate) -> Decimal:
    return money(payload.external_price) * money(payload.external_quantity or Decimal("1.00")) * money(payload.external_days or Decimal("1.00"))


def active_item_payment_requests_count(db: Session, item_id: int) -> int:
    return (
        db.query(PaymentRequest)
        .filter(
            PaymentRequest.event_item_id == item_id,
            PaymentRequest.status.notin_(list(INACTIVE_PAYMENT_STATUSES)),
        )
        .count()
    )


@router.get("/events/{event_id}/items", response_model=list[EventItemRead])
def list_event_items(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_view(current_user, event, db)

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
    event = get_event_or_404(db, event_id)
    require_event_edit(current_user, event)

    item = EventItem(
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

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


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
    item = get_item_or_404(db, item_id)
    require_item_event_edit(db, current_user, item)

    item.item_type = payload.item_type
    item.external_name = payload.external_name
    item.external_price = payload.external_price
    item.external_quantity = payload.external_quantity
    item.external_days = payload.external_days
    item.external_amount = calculate_external_amount(payload)
    item.external_note = payload.external_note
    item.amount_fact = payload.amount_fact
    item.paid_amount = payload.paid_amount
    item.payment_method = payload.payment_method
    item.iin_bin = payload.iin_bin
    item.iin_bin_locked = payload.iin_bin_locked
    item.tax_check_status = payload.tax_check_status
    item.vat_amount = payload.vat_amount
    item.deduction_amount = payload.deduction_amount
    item.internal_note = payload.internal_note
    item.sort_order = payload.sort_order
    item.updated_at = datetime.utcnow()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/event-items/{item_id}", response_model=EventItemRead)
def delete_event_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_or_404(db, item_id)
    require_item_event_edit(db, current_user, item)

    active_requests_count = active_item_payment_requests_count(db, item.id)
    if active_requests_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить позицию: по ней есть активные заявки на оплату",
        )

    item.is_deleted = True
    item.updated_at = datetime.utcnow()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item
