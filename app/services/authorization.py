from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_item import EventItem
from app.models.payment_request import PaymentRequest
from app.models.event_share import EventShare
from app.models.user import User


def event_share_user_ids(event: Event) -> set[int]:
    try:
        return {share.user_id for share in (event.shares or [])}
    except Exception:
        return set()


def event_share_department_ids(event: Event) -> set[int]:
    department_ids: set[int] = set()
    try:
        for share in (event.shares or []):
            share_user = getattr(share, "user", None)
            if share_user and share_user.department_id:
                department_ids.add(share_user.department_id)
    except Exception:
        return set()
    return department_ids


def can_view_event(user: User, event: Event, db: Session | None = None) -> bool:
    if user.role == "admin":
        return True

    if user.role == "manager":
        if event.manager_id == user.id or user.id in event_share_user_ids(event):
            return True
        if db is not None:
            shared_event_id = db.execute(
                select(EventShare.event_id).where(
                    EventShare.event_id == event.id,
                    EventShare.user_id == user.id,
                ).limit(1)
            ).scalar_one_or_none()
            return shared_event_id is not None
        return False

    if user.role == "department_head":
        if not user.department_id:
            return False

        if event.department_id == user.department_id:
            return True

        # Fallback for old/stale events where department_id was not updated,
        # but the primary manager already belongs to the head's department.
        event_manager = getattr(event, "manager", None)
        if event_manager and event_manager.department_id == user.department_id:
            return True

        if user.department_id in event_share_department_ids(event):
            return True

        if db is not None:
            owner_department_id = db.execute(
                select(User.department_id).where(User.id == event.manager_id)
            ).scalar_one_or_none()
            if owner_department_id == user.department_id:
                return True

            shared_department_event_id = db.execute(
                select(EventShare.event_id)
                .join(User, User.id == EventShare.user_id)
                .where(
                    EventShare.event_id == event.id,
                    User.department_id == user.department_id,
                )
                .limit(1)
            ).scalar_one_or_none()
            return shared_department_event_id is not None

        return False

    return False


def can_edit_event(user: User, event: Event) -> bool:
    if user.role == "admin":
        return True

    if user.role == "manager":
        return event.manager_id == user.id or user.id in event_share_user_ids(event)

    return False


def require_event_view(user: User, event: Event, db: Session | None = None) -> None:
    if not can_view_event(user, event, db):
        raise HTTPException(status_code=403, detail="No access to this event")


def require_event_edit(user: User, event: Event) -> None:
    if not can_edit_event(user, event):
        raise HTTPException(status_code=403, detail="No permission to edit this event")


def get_event_or_404(db: Session, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def get_item_or_404(db: Session, item_id: int) -> EventItem:
    item = db.get(EventItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Event item not found")
    return item


def get_request_or_404(db: Session, request_id: int) -> PaymentRequest:
    request = db.get(PaymentRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Payment request not found")
    return request


def require_item_event_view(db: Session, user: User, item: EventItem) -> Event:
    event = get_event_or_404(db, item.event_id)
    require_event_view(user, event, db)
    return event


def require_item_event_edit(db: Session, user: User, item: EventItem) -> Event:
    event = get_event_or_404(db, item.event_id)
    require_event_edit(user, event)
    return event


def require_payment_request_view(db: Session, user: User, request: PaymentRequest) -> Event:
    event = get_event_or_404(db, request.event_id)
    require_event_view(user, event, db)
    return event


def require_payment_request_edit(db: Session, user: User, request: PaymentRequest) -> Event:
    event = get_event_or_404(db, request.event_id)

    if user.role == "admin":
        return event

    if user.role == "manager" and (event.manager_id == user.id or user.id in event_share_user_ids(event)):
        return event

    raise HTTPException(status_code=403, detail="No permission for this payment request")
