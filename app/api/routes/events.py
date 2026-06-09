from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.event import EventCreate, EventRead
from app.services.auth import get_current_user
from app.services.authorization import require_event_edit, require_event_view


router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventRead])
def list_events(
    department_id: int | None = None,
    manager_id: int | None = None,
    include_cancelled: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Event)

    if not include_cancelled:
        query = query.where(Event.status != "cancelled")

    if current_user.role == "admin":
        if department_id is not None:
            query = query.where(Event.department_id == department_id)
        if manager_id is not None:
            query = query.where(Event.manager_id == manager_id)

    elif current_user.role == "manager":
        # Manager can see only own events, regardless of incoming manager_id.
        query = query.where(Event.manager_id == current_user.id)

    elif current_user.role == "department_head":
        # Department head is read-only and sees only own department.
        query = query.where(Event.department_id == current_user.department_id)
        if manager_id is not None:
            query = query.where(Event.manager_id == manager_id)

    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = db.execute(query.order_by(Event.event_date.desc(), Event.id.desc()))
    return result.scalars().all()


@router.post("/events", response_model=EventRead)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Only admin or manager can create events")

    manager_id = payload.manager_id
    department_id = payload.department_id

    if current_user.role == "manager":
        # Manager creates only own events.
        manager_id = current_user.id
        department_id = current_user.department_id

    event = Event(
        client_name=payload.client_name,
        title=payload.title,
        event_date=payload.event_date,
        department_id=department_id,
        manager_id=manager_id,
        status=payload.status,
        client_calc_type=payload.client_calc_type,
        manager_percent=payload.manager_percent,
        agency_commission_amount=payload.agency_commission_amount,
        agency_commission_spread_enabled=payload.agency_commission_spread_enabled,
        simplified_bank_tax_percent=payload.simplified_bank_tax_percent,
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    require_event_view(current_user, event)
    return event


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    require_event_edit(current_user, event)

    event.client_name = payload.client_name
    event.title = payload.title
    event.event_date = payload.event_date

    if current_user.role == "admin":
        event.department_id = payload.department_id
        event.manager_id = payload.manager_id

    event.status = payload.status
    event.client_calc_type = payload.client_calc_type
    event.manager_percent = payload.manager_percent
    event.agency_commission_amount = payload.agency_commission_amount
    event.agency_commission_spread_enabled = payload.agency_commission_spread_enabled
    event.simplified_bank_tax_percent = payload.simplified_bank_tax_percent

    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_edit(current_user, event)

    if event.status not in {"draft", "revision"}:
        raise HTTPException(
            status_code=400,
            detail="Удалять можно только черновики или мероприятия на доработке",
        )

    active_requests_count = (
        db.query(PaymentRequest)
        .filter(
            PaymentRequest.event_id == event.id,
            PaymentRequest.status.notin_(["cancelled", "rejected"]),
        )
        .count()
    )
    if active_requests_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить мероприятие: по нему есть активные заявки на оплату",
        )

    event.is_deleted = True
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()

    return {"ok": True, "event_id": event.id}

