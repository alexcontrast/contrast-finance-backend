from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event_item import EventItem
from app.models.payment_request import PaymentRequest


def money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def sync_item_paid_amount_from_requests(db: Session, item_id: int) -> EventItem | None:
    """
    EventItem.paid_amount is a denormalized UI/cache field.
    The source of truth is paid PaymentRequest rows.
    """
    item = db.get(EventItem, int(item_id))
    if item is None:
        return None

    total = db.execute(
        select(func.coalesce(func.sum(PaymentRequest.amount_requested), 0)).where(
            PaymentRequest.event_item_id == item.id,
            PaymentRequest.status == "paid",
        )
    ).scalar_one()

    item.paid_amount = money(total)
    db.add(item)
    db.flush()
    return item


def sync_event_paid_amounts_from_requests(db: Session, event_id: int) -> None:
    """
    Repairs/refreshes all paid_amount values for one event before rendering
    estimates and summaries.
    """
    items = db.execute(
        select(EventItem).where(
            EventItem.event_id == int(event_id),
            EventItem.is_deleted == False,  # noqa: E712
        )
    ).scalars().all()

    if not items:
        return

    item_ids = [item.id for item in items]
    totals = dict(
        db.execute(
            select(
                PaymentRequest.event_item_id,
                func.coalesce(func.sum(PaymentRequest.amount_requested), 0),
            )
            .where(
                PaymentRequest.event_item_id.in_(item_ids),
                PaymentRequest.status == "paid",
            )
            .group_by(PaymentRequest.event_item_id)
        ).all()
    )

    changed = False
    for item in items:
        actual = money(totals.get(item.id, Decimal("0.00")))
        if money(item.paid_amount) != actual:
            item.paid_amount = actual
            db.add(item)
            changed = True

    if changed:
        db.flush()
