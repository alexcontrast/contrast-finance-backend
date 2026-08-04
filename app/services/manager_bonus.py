from datetime import date
from decimal import Decimal

from sqlalchemy import extract, select
from sqlalchemy.orm import Session, selectinload

from app.models.event import Event
from app.services.event_calculator import calculate_event_summary_values, money, q


MANAGER_BONUS_PERCENT = Decimal("5.00")


def manager_income_for_month(db: Session, manager_id: int, month: date) -> Decimal:
    """Return the same manager income used by the personal-plan progress."""
    events = db.execute(
        select(Event)
        .options(selectinload(Event.items), selectinload(Event.shares))
        .where(
            extract("year", Event.event_date) == month.year,
            extract("month", Event.event_date) == month.month,
            Event.status != "cancelled",
        )
        .order_by(Event.id)
    ).scalars().unique().all()

    total = Decimal("0.00")
    for event in events:
        shares = list(event.shares or [])
        if shares:
            share_percent = sum(
                (money(share.share_percent) for share in shares if int(share.user_id) == int(manager_id)),
                Decimal("0.00"),
            )
        elif int(event.manager_id or 0) == int(manager_id):
            share_percent = Decimal("100.00")
        else:
            share_percent = Decimal("0.00")

        if share_percent <= 0:
            continue

        items = [item for item in (event.items or []) if item.is_deleted is False]
        summary = calculate_event_summary_values(event, items)
        total += q(money(summary["final_company_income"]) * share_percent / Decimal("100"))

    return q(total)


def manager_bonus_amount(income_amount: Decimal) -> Decimal:
    return q(money(income_amount) * MANAGER_BONUS_PERCENT / Decimal("100"))
