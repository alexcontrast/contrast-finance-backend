from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
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

    coordinator_fact = (payload.external_amount * Decimal("0.50")).quantize(Decimal("0.01"))

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

    db.add(item)
    db.commit()
    db.refresh(item)
    return item
