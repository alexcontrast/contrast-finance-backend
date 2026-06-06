from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventRead


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
def list_events(db: Session = Depends(get_db)):
    result = db.execute(select(Event).order_by(Event.id.desc()))
    return result.scalars().all()


@router.post("", response_model=EventRead)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    event = Event(
        client_name=payload.client_name,
        title=payload.title,
        event_date=payload.event_date,
        department_id=payload.department_id,
        manager_id=payload.manager_id,
        status="draft",
        client_calc_type=payload.client_calc_type,
        manager_percent=payload.manager_percent,
        agency_commission_amount=payload.agency_commission_amount,
        agency_commission_spread_enabled="true" if payload.agency_commission_spread_enabled else "false",
        simplified_bank_tax_percent=payload.simplified_bank_tax_percent,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
