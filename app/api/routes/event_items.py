from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.event_item import EventItem
from app.schemas.event_item import EventItemCreate, EventItemRead, EventItemUpdate


router = APIRouter(tags=["event_items"])


def calculate_external_amount(price, quantity, days):
    return price * quantity * days


@router.get("/events/{event_id}/items", response_model=list[EventItemRead])
def list_event_items(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    result = db.execute(
        select(EventItem)
        .where(EventItem.event_id == event_id, EventItem.is_deleted == False)  # noqa: E712
        .order_by(EventItem.sort_order, EventItem.id)
    )
    return result.scalars().all()


@router.post("/events/{event_id}/items", response_model=EventItemRead)
def create_event_item(event_id: int, payload: EventItemCreate, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    external_amount = calculate_external_amount(
        payload.external_price,
        payload.external_quantity,
        payload.external_days,
    )

    item = EventItem(
        event_id=event_id,
        item_type=payload.item_type,

        external_name=payload.external_name,
        external_price=payload.external_price,
        external_quantity=payload.external_quantity,
        external_days=payload.external_days,
        external_amount=external_amount,
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


@router.patch("/event-items/{item_id}", response_model=EventItemRead)
def update_event_item(item_id: int, payload: EventItemUpdate, db: Session = Depends(get_db)):
    item = db.get(EventItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Event item not found")

    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(item, field, value)

    if any(field in data for field in ["external_price", "external_quantity", "external_days"]):
        item.external_amount = calculate_external_amount(
            item.external_price,
            item.external_quantity,
            item.external_days,
        )

    item.updated_at = datetime.utcnow()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item
