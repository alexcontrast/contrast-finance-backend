from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.user import User
from app.schemas.coordinator import CoordinatorCreate
from app.schemas.event_item import EventItemRead
from app.services.auth import get_current_user
from app.services.authorization import require_event_edit


router = APIRouter(tags=["coordinator"])


@router.post("/events/{event_id}/coordinator", response_model=EventItemRead)
def create_coordinator_item(
    event_id: int,
    payload: CoordinatorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Быстро создаёт позицию координатора.

    Правило координатора в summary:
    - 50% от суммы по смете = факт/оплата координатора
    - 50% = доля компании
    - координатор не участвует в ЗП менеджера
    """
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    require_event_edit(current_user, event)

    # Coordinator is a singleton inside an event. Locking the event row also
    # protects the empty state: two concurrent requests cannot both decide
    # that the coordinator is missing.
    db.execute(
        select(Event.id)
        .where(Event.id == int(event_id))
        .with_for_update()
    ).scalar_one()

    item = db.execute(
        select(EventItem)
        .where(
            EventItem.event_id == int(event_id),
            EventItem.item_type == "coordinator",
            EventItem.is_deleted == False,  # noqa: E712
        )
        .order_by(EventItem.updated_at.desc(), EventItem.id.desc())
        .with_for_update()
    ).scalars().first()

    coordinator_fact = (payload.external_amount * Decimal("0.50")).quantize(Decimal("0.01"))

    if item is None:
        item = EventItem(
            event_id=event_id,
            item_type="coordinator",
            external_name=payload.external_name,
            external_price=payload.external_amount,
            external_quantity=Decimal("1.00"),
            external_days=Decimal("1.00"),
            external_amount=payload.external_amount,
            external_note=payload.external_note,
            amount_fact=coordinator_fact,
            paid_amount=Decimal("0.00"),
            payment_method="cash",
            iin_bin=None,
            iin_bin_locked=False,
            tax_check_status=None,
            vat_amount=Decimal("0.00"),
            deduction_amount=Decimal("0.00"),
            internal_note="Автоматически: 50% координатору, 50% в доход компании",
            sort_order=payload.sort_order,
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    else:
        item.external_name = payload.external_name
        item.external_price = payload.external_amount
        item.external_quantity = Decimal("1.00")
        item.external_days = Decimal("1.00")
        item.external_amount = payload.external_amount
        item.external_note = payload.external_note
        item.amount_fact = coordinator_fact
        item.payment_method = "cash"
        item.iin_bin = None
        item.iin_bin_locked = False
        item.tax_check_status = None
        item.vat_amount = Decimal("0.00")
        item.deduction_amount = Decimal("0.00")
        item.internal_note = "Автоматически: 50% координатору, 50% в доход компании"
        item.sort_order = payload.sort_order
        item.updated_at = datetime.utcnow()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item
