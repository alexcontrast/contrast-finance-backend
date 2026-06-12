from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.event_share import EventShare
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.schemas.payment_request import (
    PaymentRequestCardRead,
    PaymentRequestCreate,
    PaymentRequestMoneyStatusUpdate,
    PaymentRequestRead,
    PaymentRequestStatusUpdate,
)
from app.services.auth import get_current_user
from app.services.event_calculator import calculate_event_summary_values, q
from app.services.authorization import (
    get_event_or_404,
    get_item_or_404,
    get_request_or_404,
    require_event_view,
    require_item_event_edit,
    require_payment_request_edit,
    require_payment_request_view,
)


router = APIRouter(tags=["payment_requests"])


def tax_status_label(tax_status: str | None) -> str | None:
    labels = {
        "our_vat": "ОУР с НДС",
        "our_no_vat": "ОУР без НДС",
        "simplified": "Упрощенка",
        "snr": "СНР",
        "self_employed": "Самозанятый",
        "not_found": "Не проверен",
        None: None,
    }
    return labels.get(tax_status, tax_status)


def payment_method_label(payment_method: str | None) -> str | None:
    labels = {
        "invoice": "По счету",
        "card": "На карту",
        "cash": "Налик",
        "self_employed": "Самозанятый",
    }
    return labels.get(payment_method, payment_method)


def calculate_item_remaining(item: EventItem) -> Decimal:
    """
    Остаток:
    - если факт есть: Факт - Оплачено
    - если факта нет: Сумма по смете - Оплачено
    """
    base_amount = item.amount_fact if item.amount_fact is not None else item.external_amount
    return base_amount - item.paid_amount


def get_event_items_for_summary(db: Session, event_id: int) -> list[EventItem]:
    return db.execute(
        select(EventItem)
        .where(EventItem.event_id == event_id, EventItem.is_deleted == False)  # noqa: E712
        .order_by(EventItem.sort_order, EventItem.id)
    ).scalars().all()


def get_or_create_manager_salary_item(db: Session, event: Event, manager_salary: Decimal) -> EventItem:
    item = db.execute(
        select(EventItem)
        .where(
            EventItem.event_id == event.id,
            EventItem.item_type == "manager_salary",
            EventItem.is_deleted == False,  # noqa: E712
        )
        .order_by(EventItem.id)
    ).scalar_one_or_none()

    if item is None:
        item = EventItem(
            event_id=event.id,
            item_type="manager_salary",
            external_name="Менеджер 21%",
            external_price=Decimal("0.00"),
            external_quantity=Decimal("1.00"),
            external_days=Decimal("1.00"),
            external_amount=Decimal("0.00"),
            external_note=None,
            amount_fact=q(manager_salary),
            paid_amount=Decimal("0.00"),
            payment_method=None,
            iin_bin=None,
            iin_bin_locked=False,
            tax_check_status=None,
            vat_amount=Decimal("0.00"),
            deduction_amount=Decimal("0.00"),
            internal_note="Системная позиция ЗП менеджера",
            sort_order=999999,
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(item)
        db.flush()
    else:
        item.external_amount = Decimal("0.00")
        item.external_price = Decimal("0.00")
        item.external_quantity = Decimal("1.00")
        item.external_days = Decimal("1.00")
        item.amount_fact = q(manager_salary)
        item.vat_amount = Decimal("0.00")
        item.deduction_amount = Decimal("0.00")
        item.updated_at = datetime.utcnow()
        db.add(item)
        db.flush()

    return item


def validate_manager_salary_payment_rules(payment_method: str, payload: PaymentRequestCreate):
    if payment_method not in {"card", "cash"}:
        raise HTTPException(
            status_code=400,
            detail="ЗП менеджера можно оформить только На карту или Налик",
        )

    if payment_method == "card" and not looks_like_card_number(payload.card_number):
        raise HTTPException(
            status_code=400,
            detail="Для ЗП менеджера На карту нужен номер карты из 16 цифр",
        )


def normalize_payment_method(payment_method: str | None) -> str | None:
    if payment_method is None:
        return None

    aliases = {
        "по счету": "invoice",
        "по счёту": "invoice",
        "invoice": "invoice",

        "на карту": "card",
        "card": "card",

        "налик": "cash",
        "нал": "cash",
        "cash": "cash",

        "самозанятый": "self_employed",
        "self_employed": "self_employed",
    }

    key = payment_method.strip().lower()
    return aliases.get(key, payment_method)


def looks_like_card_number(card_number: str | None) -> bool:
    if not card_number:
        return False

    digits = "".join(ch for ch in card_number if ch.isdigit())
    return len(digits) == 16


def comment_has_surname(comment: str | None) -> bool:
    if not comment:
        return False

    words = [word.strip(" ,.;:!?()[]{}") for word in comment.split()]
    return any(len(word) >= 2 and any(ch.isalpha() for ch in word) for word in words)


def validate_payment_request_rules(item: EventItem, payment_method: str, payload: PaymentRequestCreate):
    """
    invoice / По счету:
    - BIN / ИИН обязателен
    - BIN / ИИН должен быть зафиксирован
    - налоговый статус должен быть определён
    - статус not_found не считается полноценной проверкой

    card / На карту:
    - номер карты обязателен и должен содержать 16 цифр

    self_employed / Самозанятый:
    - фамилия обязательна в комментарии

    cash / Налик:
    - без дополнительных обязательных полей
    """
    if payment_method == "invoice":
        if not item.iin_bin:
            raise HTTPException(
                status_code=400,
                detail="Для оплаты По счету нужен BIN / ИИН в позиции",
            )

        if not item.iin_bin_locked:
            raise HTTPException(
                status_code=400,
                detail="Для оплаты По счету BIN / ИИН должен быть проверен и зафиксирован",
            )

        if not item.tax_check_status or item.tax_check_status == "not_found":
            raise HTTPException(
                status_code=400,
                detail="Для оплаты По счету нужен подтвержденный налоговый статус",
            )

    if payment_method == "card":
        if not looks_like_card_number(payload.card_number):
            raise HTTPException(
                status_code=400,
                detail="Для оплаты На карту нужен номер карты из 16 цифр",
            )

    if payment_method == "self_employed":
        if not comment_has_surname(payload.comment):
            raise HTTPException(
                status_code=400,
                detail="Для Самозанятого фамилия обязательна в комментарии",
            )

    if payment_method not in {"invoice", "card", "cash", "self_employed"}:
        raise HTTPException(
            status_code=400,
            detail="Некорректный способ оплаты. Используй invoice, card, cash или self_employed",
        )


def enrich_payment_request_read(request: PaymentRequest, db: Session | None = None) -> PaymentRequestRead:
    data = PaymentRequestRead.model_validate(request)
    data.tax_status_label = tax_status_label(request.tax_status_snapshot)
    data.position = request.item_name_snapshot

    if db is not None:
        event = db.get(Event, request.event_id)
        if event is not None:
            data.client_name = event.client_name
            data.event_title = event.title

            manager = db.get(User, event.manager_id) if event.manager_id else None
            if manager is not None:
                data.manager_name = manager.name

    return data


def build_payment_request_card(request: PaymentRequest) -> PaymentRequestCardRead:
    return PaymentRequestCardRead(
        id=request.id,
        position=request.item_name_snapshot,
        amount_plan=request.item_amount_plan_snapshot,
        fact=request.item_amount_fact_snapshot,
        remaining=request.item_remaining_snapshot,
        amount_requested=request.amount_requested,
        payment_method=payment_method_label(request.payment_method) or request.payment_method,
        card_number=request.card_number,
        iin_bin=request.iin_bin_snapshot,
        tax_status=tax_status_label(request.tax_status_snapshot),
        comment=request.comment,
        status=request.status,
        money_status=getattr(request, "money_status", "waiting_money"),
        warning_over_remaining=request.warning_over_remaining,
    )


def event_scope_query_for_user(query, user: User):
    """
    Adds event-based visibility for payment requests:
    admin -> all
    manager -> own events
    department_head -> own department
    """
    query = query.join(Event, Event.id == PaymentRequest.event_id)

    if user.role == "admin":
        return query

    if user.role == "manager":
        return query.where(Event.manager_id == user.id)

    if user.role == "department_head":
        shared_event_ids = select(EventShare.event_id).join(
            User, User.id == EventShare.user_id
        ).where(User.department_id == user.department_id)
        return query.where(or_(Event.department_id == user.department_id, Event.id.in_(shared_event_ids)))

    raise HTTPException(status_code=403, detail="Not enough permissions")


@router.get("/payment-requests", response_model=list[PaymentRequestRead])
def list_payment_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PaymentRequest).order_by(PaymentRequest.id.desc())
    query = event_scope_query_for_user(query, current_user)

    result = db.execute(query)
    return [enrich_payment_request_read(request, db) for request in result.scalars().all()]


@router.get("/payment-requests/{request_id}", response_model=PaymentRequestRead)
def get_payment_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = get_request_or_404(db, request_id)
    require_payment_request_view(db, current_user, request)
    return enrich_payment_request_read(request, db)


@router.get("/payment-requests/{request_id}/card", response_model=PaymentRequestCardRead)
def get_payment_request_card(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = get_request_or_404(db, request_id)
    require_payment_request_view(db, current_user, request)
    return build_payment_request_card(request)


@router.get("/events/{event_id}/payment-requests", response_model=list[PaymentRequestRead])
def list_event_payment_requests(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)
    require_event_view(current_user, event)

    result = db.execute(
        select(PaymentRequest)
        .where(PaymentRequest.event_id == event_id)
        .order_by(PaymentRequest.id.desc())
    )
    return [enrich_payment_request_read(request, db) for request in result.scalars().all()]


@router.post("/event-items/{item_id}/payment-requests", response_model=PaymentRequestRead)
def create_payment_request(
    item_id: int,
    payload: PaymentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_item_or_404(db, item_id)

    # Admin can create; manager only for own event; department_head is read-only.
    event = require_item_event_edit(db, current_user, item)

    payment_method = normalize_payment_method(payload.payment_method) or normalize_payment_method(item.payment_method)

    if not payment_method:
        raise HTTPException(
            status_code=400,
            detail="У позиции не указан способ оплаты",
        )

    validate_payment_request_rules(item, payment_method, payload)

    remaining = calculate_item_remaining(item)
    warning_over_remaining = payload.amount_requested > remaining

    request = PaymentRequest(
        event_id=event.id,
        event_item_id=item.id,
        created_by_user_id=current_user.id,
        amount_requested=payload.amount_requested,
        payment_method=payment_method,
        status="new",
        money_status=getattr(event, "money_status", "waiting_money"),
        comment=payload.comment,

        item_name_snapshot=item.external_name,
        item_amount_plan_snapshot=item.external_amount,
        item_amount_fact_snapshot=item.amount_fact,
        item_paid_amount_snapshot=item.paid_amount,
        item_remaining_snapshot=remaining,

        contractor_id=None,
        contractor_name_snapshot=payload.comment if payment_method == "self_employed" else None,
        iin_bin_snapshot=item.iin_bin if payment_method == "invoice" else None,
        tax_status_snapshot=item.tax_check_status if payment_method == "invoice" else (
            "self_employed" if payment_method == "self_employed" else None
        ),
        vat_status_snapshot="vat" if item.tax_check_status == "our_vat" else (
            "no_vat" if payment_method in {"invoice", "self_employed"} else None
        ),
        vat_amount_snapshot=item.vat_amount if payment_method == "invoice" else Decimal("0.00"),
        deduction_amount_snapshot=item.deduction_amount if payment_method in {"invoice", "self_employed"} else Decimal("0.00"),
        tax_source_snapshot="event_item" if payment_method in {"invoice", "self_employed"} else None,

        card_number=payload.card_number if payment_method == "card" else None,
        manual_tax_mode=False,
        warning_over_remaining=warning_over_remaining,

        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return enrich_payment_request_read(request, db)




@router.post("/events/{event_id}/manager-salary/payment-requests", response_model=PaymentRequestRead)
def create_manager_salary_payment_request(
    event_id: int,
    payload: PaymentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = get_event_or_404(db, event_id)

    if current_user.role == "department_head":
        raise HTTPException(status_code=403, detail="Department head is read-only")

    if current_user.role == "manager" and event.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Manager can request salary only for own event")

    if current_user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Only admin or manager can create manager salary request")

    payment_method = normalize_payment_method(payload.payment_method)
    if not payment_method:
        raise HTTPException(
            status_code=400,
            detail="Для заявки на ЗП менеджера нужно выбрать способ оплаты: card или cash",
        )

    validate_manager_salary_payment_rules(payment_method, payload)

    items = get_event_items_for_summary(db, event.id)
    summary = calculate_event_summary_values(event, items)
    manager_salary = q(summary["manager_salary"])

    if manager_salary <= 0:
        raise HTTPException(status_code=400, detail="ЗП менеджера по этому мероприятию равна 0")

    salary_item = get_or_create_manager_salary_item(db, event, manager_salary)
    remaining = calculate_item_remaining(salary_item)
    warning_over_remaining = payload.amount_requested > remaining

    request = PaymentRequest(
        event_id=event.id,
        event_item_id=salary_item.id,
        created_by_user_id=current_user.id,
        amount_requested=payload.amount_requested,
        payment_method=payment_method,
        status="new",
        money_status=getattr(event, "money_status", "waiting_money"),
        comment=payload.comment,

        item_name_snapshot=salary_item.external_name,
        item_amount_plan_snapshot=Decimal("0.00"),
        item_amount_fact_snapshot=salary_item.amount_fact,
        item_paid_amount_snapshot=salary_item.paid_amount,
        item_remaining_snapshot=remaining,

        contractor_id=None,
        contractor_name_snapshot=None,
        iin_bin_snapshot=None,
        tax_status_snapshot=None,
        vat_status_snapshot=None,
        vat_amount_snapshot=Decimal("0.00"),
        deduction_amount_snapshot=Decimal("0.00"),
        tax_source_snapshot=None,

        card_number=payload.card_number if payment_method == "card" else None,
        manual_tax_mode=False,
        warning_over_remaining=warning_over_remaining,

        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return enrich_payment_request_read(request, db)


@router.patch("/payment-requests/{request_id}/status", response_model=PaymentRequestRead)
def update_payment_request_status(
    request_id: int,
    payload: PaymentRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = get_request_or_404(db, request_id)

    allowed = {"new", "to_pay", "paid", "rejected", "tax_check_needed", "cash_received"}
    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail="status должен быть new, to_pay, paid, rejected или tax_check_needed",
        )

    event = require_payment_request_edit(db, current_user, request)

    # Admin can manage all statuses.
    # Manager/coauthor can only cancel unpaid requests in an event they can edit.
    # Department head remains read-only because require_payment_request_edit rejects it.
    if current_user.role != "admin":
        if current_user.role == "manager" and payload.status == "rejected":
            if request.status in {"paid"}:
                raise HTTPException(
                    status_code=400,
                    detail="Оплаченную заявку нельзя отменить менеджером",
                )

            # require_payment_request_edit() above already checks that the manager
            # is either event owner or coauthor. Therefore any coauthor of the event
            # may cancel an unpaid request, even if it was created by another coauthor.
        else:
            raise HTTPException(
                status_code=403,
                detail="Менеджер или соавтор может только отменить неоплаченную заявку",
            )

    previous_status = request.status

    item = db.get(EventItem, request.event_item_id)

    if payload.status == "cash_received":
        # Legacy compatibility: old button used status=cash_received.
        # Now this only changes money_status and does not change contractor payment status.
        request.money_status = "cash_received"
        request.cash_received_at = datetime.utcnow()
        request.updated_at = datetime.utcnow()
        db.add(request)
        db.commit()
        db.refresh(request)
        return enrich_payment_request_read(request, db)

    request.status = payload.status
    request.updated_at = datetime.utcnow()

    if payload.status == "paid" and previous_status != "paid":
        request.paid_at = datetime.utcnow()

        if item is not None:
            item.paid_amount = item.paid_amount + request.amount_requested
            item.updated_at = datetime.utcnow()
            db.add(item)

    if payload.status == "rejected":
        request.rejected_at = datetime.utcnow()
        request.money_status = "cancelled"

        # Refund: if an already paid request is cancelled, remove it from paid amount.
        if previous_status in {"paid"} and item is not None:
            item.paid_amount = item.paid_amount - request.amount_requested
            if item.paid_amount < 0:
                item.paid_amount = 0
            item.updated_at = datetime.utcnow()
            db.add(item)

    db.add(request)
    db.commit()
    db.refresh(request)

    return enrich_payment_request_read(request, db)


@router.patch("/payment-requests/{request_id}/money-status", response_model=PaymentRequestRead)
def update_payment_request_money_status(
    request_id: int,
    payload: PaymentRequestMoneyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = get_request_or_404(db, request_id)

    if payload.money_status not in {"waiting_money", "cash_received", "cancelled"}:
        raise HTTPException(status_code=400, detail="money_status должен быть waiting_money, cash_received или cancelled")

    event = require_payment_request_edit(db, current_user, request)

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Статус денег может менять только админ")

    request.money_status = payload.money_status
    if payload.money_status == "cash_received":
        request.cash_received_at = datetime.utcnow()

        # Если хотя бы одна заявка по мероприятию отмечена как деньги в кассе,
        # мероприятие тоже получает money_status=cash_received.
        event.money_status = "cash_received"
        event.updated_at = datetime.utcnow()
        db.add(event)

    request.updated_at = datetime.utcnow()
    db.add(request)
    db.commit()
    db.refresh(request)
    return enrich_payment_request_read(request, db)
