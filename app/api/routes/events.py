from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, not_, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.event_share import EventShare
from app.models.payment_request import PaymentRequest
from app.models.telegram_message import TelegramMessage
from app.models.user import User
from app.schemas.event import EventCreate, EventRead
from app.services.auth import get_current_user
from app.services.authorization import get_event_or_404, require_event_edit, require_event_view
from app.models.event_item import EventItem
from app.services.event_calculator import calculate_event_summary_values, q


router = APIRouter(tags=["events"])

INACTIVE_PAYMENT_STATUSES = {"cancelled", "rejected"}


class EventManagerActionPayload(BaseModel):
    manager_id: int


class EventActionManagerRead(BaseModel):
    id: int
    name: str
    department_id: int | None = None
    department_name: str | None = None


class EventCustomerPaymentPayload(BaseModel):
    amount: Decimal


class EventCustomerPaymentSetPayload(BaseModel):
    amount: Decimal


class EventManagerPercentPayload(BaseModel):
    manager_percent: Decimal



def normalize_manager_percent(value: Decimal) -> Decimal:
    percent = q(value)
    if percent < Decimal("0.00") or percent > Decimal("100.00"):
        raise HTTPException(status_code=400, detail="Процент менеджера должен быть от 0 до 100")
    return percent



def mark_event_payment_requests_for_telegram_sync(db: Session, request_ids: list[int]) -> None:
    if not request_ids:
        return
    dirty_at = datetime(2000, 1, 1)
    messages = db.execute(
        select(TelegramMessage).where(
            TelegramMessage.payment_request_id.in_(request_ids),
            TelegramMessage.status == "active",
        )
    ).scalars().all()
    for message in messages:
        message.updated_at = dirty_at
        message.error_message = None
        db.add(message)


def active_payment_requests_count(db: Session, event_id: int) -> int:
    return (
        db.query(PaymentRequest)
        .filter(
            PaymentRequest.event_id == event_id,
            PaymentRequest.status.notin_(list(INACTIVE_PAYMENT_STATUSES)),
        )
        .count()
    )


def get_active_manager_or_404(db: Session, manager_id: int) -> User:
    manager = db.get(User, manager_id)
    if manager is None or manager.role != "manager" or not manager.is_active:
        raise HTTPException(status_code=404, detail="Manager not found")
    return manager


def clear_event_shares(db: Session, event_id: int) -> None:
    shares = db.execute(select(EventShare).where(EventShare.event_id == event_id)).scalars().all()
    for share in shares:
        db.delete(share)


@router.get("/events/action-managers", response_model=list[EventActionManagerRead])
def list_action_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    managers = (
        db.execute(
            select(User)
            .where(User.role == "manager", User.is_active == True)  # noqa: E712
            .order_by(User.name, User.id)
        )
        .scalars()
        .all()
    )

    return [
        EventActionManagerRead(
            id=manager.id,
            name=manager.name,
            department_id=manager.department_id,
            department_name=manager.department.name if manager.department else None,
        )
        for manager in managers
    ]


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
        shared_event_ids = select(EventShare.event_id).where(EventShare.user_id == current_user.id)
        query = query.where(or_(Event.manager_id == current_user.id, Event.id.in_(shared_event_ids)))

    elif current_user.role == "department_head":
        shared_event_ids = (
            select(EventShare.event_id)
            .join(User, User.id == EventShare.user_id)
            .where(User.department_id == current_user.department_id)
        )
        event_has_shares = select(EventShare.id).where(EventShare.event_id == Event.id).exists()
        primary_manager_in_department = select(User.department_id).where(User.id == Event.manager_id).scalar_subquery() == current_user.department_id

        query = query.where(
            or_(
                Event.id.in_(shared_event_ids),
                and_(not_(event_has_shares), primary_manager_in_department),
            )
        )
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
        manager_id = current_user.id
        department_id = current_user.department_id

    event = Event(
        client_name=payload.client_name,
        title=payload.title,
        event_date=payload.event_date,
        department_id=department_id,
        manager_id=manager_id,
        status="accepted" if payload.status == "cash_received" else payload.status,
        money_status="cash_received" if payload.status == "cash_received" else "waiting_money",
        client_calc_type=payload.client_calc_type,
        manager_percent=normalize_manager_percent(payload.manager_percent),
        agency_commission_amount=payload.agency_commission_amount,
        customer_paid_amount=getattr(payload, "customer_paid_amount", Decimal("0.00")) or Decimal("0.00"),
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
    event = get_event_or_404(db, event_id)
    require_event_view(current_user, event, db)
    return event


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_edit(current_user, event)

    if current_user.role == "manager" and event.status not in {"draft", "revision"}:
        raise HTTPException(
            status_code=400,
            detail="Менеджер может редактировать только черновик или мероприятие на доработке",
        )

    event.client_name = payload.client_name
    event.title = payload.title
    event.event_date = payload.event_date

    if current_user.role == "admin":
        event.department_id = payload.department_id
        event.manager_id = payload.manager_id

    if payload.status == "cash_received":
        # Legacy compatibility: old frontend used event.status=cash_received.
        event.status = "accepted"
        event.money_status = "cash_received"
    else:
        event.status = payload.status
    event.client_calc_type = payload.client_calc_type
    # Важно: менеджерский PATCH мероприятия не должен затирать процент менеджера.
    # Процент меняется только админом через админ-редактирование или отдельный endpoint
    # /events/{event_id}/manager-percent. Иначе старый черновик/локальный draft менеджера
    # может прислать дефолтные 21% и сбросить админский override при отправке на проверку.
    if current_user.role == "admin":
        event.manager_percent = normalize_manager_percent(payload.manager_percent)
    event.agency_commission_amount = payload.agency_commission_amount
    event.agency_commission_spread_enabled = payload.agency_commission_spread_enabled
    event.simplified_bank_tax_percent = payload.simplified_bank_tax_percent
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def require_admin_event_action(current_user: User) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can perform this action")


@router.patch("/events/{event_id}/manager-percent", response_model=EventRead)
def update_event_manager_percent(
    event_id: int,
    payload: EventManagerPercentPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin_event_action(current_user)
    event = get_event_or_404(db, event_id)

    if event.status == "cancelled":
        raise HTTPException(status_code=400, detail="Нельзя менять процент менеджера у отменённого мероприятия")

    event.manager_percent = normalize_manager_percent(payload.manager_percent)
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/events/{event_id}/accept", response_model=EventRead)
def accept_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin_event_action(current_user)
    event = get_event_or_404(db, event_id)

    if event.status != "review":
        raise HTTPException(status_code=400, detail="Принять можно только мероприятие на проверке")

    event.status = "accepted"
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/events/{event_id}/revision", response_model=EventRead)
def send_event_to_revision(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin_event_action(current_user)
    event = get_event_or_404(db, event_id)

    if event.status not in {"review", "accepted", "cash_received"}:
        raise HTTPException(status_code=400, detail="На доработку можно отправить только мероприятие на проверке, принятое или архивное")

    # Откатываем только рабочий статус мероприятия. Статусы денег не меняем.
    event.status = "revision"
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event




def _event_customer_turnover(db: Session, event: Event) -> Decimal:
    items = db.execute(
        select(EventItem)
        .where(EventItem.event_id == event.id, EventItem.is_deleted == False)  # noqa: E712
        .order_by(EventItem.sort_order, EventItem.id)
    ).scalars().all()
    values = calculate_event_summary_values(event, items)
    return q(values["turnover_with_vat"])


@router.post("/events/{event_id}/customer-payment", response_model=EventRead)
def add_event_customer_payment(
    event_id: int,
    payload: EventCustomerPaymentPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin_event_action(current_user)
    event = get_event_or_404(db, event_id)

    amount = q(payload.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма оплаты заказчика должна быть больше 0")

    turnover = _event_customer_turnover(db, event)
    current_paid = q(getattr(event, "customer_paid_amount", Decimal("0.00")) or Decimal("0.00"))
    new_paid = current_paid + amount
    if turnover > 0 and new_paid > turnover:
        new_paid = turnover

    event.customer_paid_amount = q(new_paid)
    if turnover > 0 and event.customer_paid_amount >= turnover:
        event.money_status = "cash_received"
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.patch("/events/{event_id}/customer-payment", response_model=EventRead)
def set_event_customer_payment(
    event_id: int,
    payload: EventCustomerPaymentSetPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin_event_action(current_user)
    event = get_event_or_404(db, event_id)

    amount = q(payload.amount)
    if amount < 0:
        raise HTTPException(status_code=400, detail="Сумма оплаты заказчика не может быть меньше 0")

    turnover = _event_customer_turnover(db, event)
    if turnover > 0 and amount > turnover:
        amount = turnover

    event.customer_paid_amount = q(amount)
    if turnover > 0 and event.customer_paid_amount >= turnover:
        event.money_status = "cash_received"
    else:
        event.money_status = "waiting_money"
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.post("/events/{event_id}/cash-received", response_model=EventRead)
def mark_event_cash_received(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin_event_action(current_user)
    event = get_event_or_404(db, event_id)

    payment_requests = db.execute(
        select(PaymentRequest).where(
            PaymentRequest.event_id == event.id,
            PaymentRequest.status.notin_(["rejected", "cancelled"]),
        )
    ).scalars().all()

    now = datetime.utcnow()
    changed_request_ids: list[int] = []
    for request in payment_requests:
        # Статус оплаты подрядчику не трогаем. Это независимая ось.
        request.money_status = "cash_received"
        request.cash_received_at = now
        request.updated_at = now
        changed_request_ids.append(request.id)
        db.add(request)

    # Рабочий статус мероприятия не трогаем. Фиксируем только деньги клиента.
    event.money_status = "cash_received"
    event.customer_paid_amount = _event_customer_turnover(db, event)
    event.updated_at = now

    db.add(event)
    mark_event_payment_requests_for_telegram_sync(db, changed_request_ids)
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

    if getattr(event, "money_status", "waiting_money") == "cash_received" or event.status == "cash_received":
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить мероприятие: деньги уже в кассе",
        )

    if active_payment_requests_count(db, event.id) > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить мероприятие: по нему есть активные заявки на оплату",
        )

    # В системе пока нет поля is_deleted у events, поэтому удаление делаем безопасно:
    # переводим в cancelled. Дашборды уже исключают cancelled из статистики и списков.
    event.status = "cancelled"
    event.cancelled_at = datetime.utcnow()
    event.updated_at = datetime.utcnow()
    clear_event_shares(db, event.id)

    db.add(event)
    db.commit()

    return {"ok": True, "event_id": event.id}


@router.delete("/events/{event_id}/admin-force-delete")
def admin_force_delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin_event_action(current_user)
    event = get_event_or_404(db, event_id)

    now = datetime.utcnow()
    requests = db.execute(
        select(PaymentRequest).where(PaymentRequest.event_id == event.id)
    ).scalars().all()

    changed_request_ids: list[int] = []
    for request in requests:
        if request.status not in INACTIVE_PAYMENT_STATUSES or getattr(request, "money_status", None) != "cancelled":
            request.status = "cancelled"
            request.money_status = "cancelled"
            request.rejected_at = request.rejected_at or now
            request.updated_at = now
            changed_request_ids.append(request.id)
            db.add(request)

    # Аварийное удаление для тестовых/ошибочных мероприятий: в текущей схеме events
    # физически не удаляем, а полностью убираем из рабочих списков через cancelled.
    event.status = "cancelled"
    event.money_status = "cancelled"
    event.cancelled_at = now
    event.updated_at = now
    clear_event_shares(db, event.id)
    db.add(event)

    mark_event_payment_requests_for_telegram_sync(db, changed_request_ids)
    db.commit()

    return {"ok": True, "event_id": event.id, "cancelled_requests": len(changed_request_ids)}


@router.post("/events/{event_id}/transfer", response_model=EventRead)
def transfer_event(
    event_id: int,
    payload: EventManagerActionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_edit(current_user, event)

    target_manager = get_active_manager_or_404(db, payload.manager_id)

    event.manager_id = target_manager.id
    event.department_id = target_manager.department_id
    event.updated_at = datetime.utcnow()
    clear_event_shares(db, event.id)

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/events/{event_id}/coauthor", response_model=EventRead)
def add_event_coauthor(
    event_id: int,
    payload: EventManagerActionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_edit(current_user, event)

    coauthor = get_active_manager_or_404(db, payload.manager_id)
    if coauthor.id == event.manager_id:
        raise HTTPException(status_code=400, detail="Этот менеджер уже основной менеджер мероприятия")

    clear_event_shares(db, event.id)
    db.flush()

    db.add(
        EventShare(
            event_id=event.id,
            user_id=event.manager_id,
            share_percent=Decimal("50.00"),
        )
    )
    db.add(
        EventShare(
            event_id=event.id,
            user_id=coauthor.id,
            share_percent=Decimal("50.00"),
        )
    )
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/events/{event_id}/coauthor/remove", response_model=EventRead)
def remove_event_coauthor(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_edit(current_user, event)

    if current_user.role == "manager":
        event.manager_id = current_user.id
        event.department_id = current_user.department_id

    clear_event_shares(db, event.id)
    event.updated_at = datetime.utcnow()

    db.add(event)
    db.commit()
    db.refresh(event)
    return event
