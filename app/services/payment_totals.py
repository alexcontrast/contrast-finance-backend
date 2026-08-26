from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value

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

    paid_total = money(total)
    if money(item.paid_amount) == paid_total:
        return item

    # paid_amount is derived/cache data, not an estimate edit. Persist it without
    # advancing EventItem.updated_at; otherwise an admin/Telegram payment status
    # change makes an open estimate look as if the row was edited in another tab.
    current_revision = item.updated_at
    db.execute(
        update(EventItem)
        .where(EventItem.id == item.id)
        .values(paid_amount=paid_total, updated_at=current_revision)
    )
    set_committed_value(item, "paid_amount", paid_total)
    set_committed_value(item, "updated_at", current_revision)
    return item


def sync_event_paid_amounts_from_requests(db: Session, event_id: int) -> None:
    """Refresh paid totals in memory for a GET response without writing revisions.

    ``paid_amount`` is derived from paid payment requests. A read endpoint must not
    update Event/EventItem rows: doing so changed ``event.updated_at`` while the
    editor was opening and made the same browser look like a concurrent browser.
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

    for item in items:
        set_committed_value(item, "paid_amount", money(totals.get(item.id, Decimal("0.00"))))
