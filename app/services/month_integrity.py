"""Closed financial months can only be changed after an explicit reopen."""
from datetime import date
from fastapi import HTTPException
from sqlalchemy import event as orm_event, inspect, select, text
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.event_share import EventShare
from app.models.payment_request import PaymentRequest
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.models.monthly_closing import MonthlyClosing


def lock_months(db, months):
    if db.bind.dialect.name == "postgresql":
        for month in sorted(months):
            db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 42000000 + month.year * 100 + month.month})


@orm_event.listens_for(Session, "before_flush")
def protect_closed_months(db, _context, _instances):
    months = set()
    with db.no_autoflush:
        for obj in set(db.new) | set(db.dirty) | set(db.deleted):
            if obj in db.dirty and not db.is_modified(obj, include_collections=False):
                continue
            if isinstance(obj, (MonthlyExpense, MonthlyPlan)):
                # The existing bonus service deliberately refreshes the closing
                # atomically after creating its unique payout expense.
                if isinstance(obj, MonthlyExpense) and obj.source_type == "manager_bonus":
                    continue
                value = obj.month
                history = inspect(obj).attrs.month.history
                months.update(d.replace(day=1) for d in history.deleted if d)
            elif isinstance(obj, Event):
                value = obj.event_date
                history = inspect(obj).attrs.event_date.history
                months.update(d.replace(day=1) for d in history.deleted if d)
            elif isinstance(obj, (EventItem, EventShare, PaymentRequest)):
                parent = db.get(Event, obj.event_id)
                value = parent.event_date if parent else None
            else:
                continue
            if value:
                months.add(value.replace(day=1))
        if not months:
            return
        lock_months(db, months)
        closing = db.execute(select(MonthlyClosing.month).where(
            MonthlyClosing.month.in_(sorted(months)), MonthlyClosing.status == "closed").with_for_update()).first()
        if closing:
            raise HTTPException(status_code=409, detail=f"Месяц {closing.month:%m.%Y} закрыт. Сначала откройте его в разделе «Закрыть месяц»")
