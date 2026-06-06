from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event_item import EventItem
from app.models.payment_request import PaymentRequest
from app.schemas.payment_request import (
    PaymentRequestCardRead,
    PaymentRequestCreate,
    PaymentRequestRead,
    PaymentRequestStatusUpdate,
)


router = APIRouter(tags=["payment_requests"])


def tax_status_label(tax_status: str | None) -> str | None:
    labels = {
        "our_vat": "ОУР с НДС",
        "our_no_vat": "ОУР без НДС",
        "simplified": "Упрощенка",
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
    """
    Минимальная проверка для самозанятого:
    в комментарии должно быть хотя бы одно слово из 2+ букв.
    """
    if not comment:
        return False

    words = [word.strip(" ,.;:!?()[]{}") for word in comment.split()]
    return any(len(word) >= 2 and any(ch.isalpha() for ch in word) for word in words)


def validate_payment_request_rules(item: EventItem, payment_method: str, payload: PaymentRequestCreate):
    """
    Правила v0.10:

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


def enrich_payment_request_read(request: PaymentRequest) -> PaymentRequestRead:
    data = PaymentRequestRead.model_validate(request)
    data.tax_status_label = tax_status_label(request.tax_status_snapshot)
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
        warning_over_remaining=request.warning_over_remaining,
    )


@router.get("/payment-requests", response_model=list[PaymentRequestRead])
def list_payment_requests(db: Session = Depends(get_db)):
    result = db.execute(select(PaymentRequest).order_by(PaymentRequest.id.desc()))
    return [enrich_payment_request_read(request) for request in result.scalars().all()]


@router.get("/payment-requests/{request_id}", response_model=PaymentRequestRead)
def get_payment_request(request_id: int, db: Session = Depends(get_db)):
    request = db.get(PaymentRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Payment request not found")
    return enrich_payment_request_read(request)


@router.get("/payment-requests/{request_id}/card", response_model=PaymentRequestCardRead)
def get_payment_request_card(request_id: int, db: Session = Depends(get_db)):
    request = db.get(PaymentRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Payment request not found")
    return build_payment_request_card(request)


@router.get("/events/{event_id}/payment-requests", response_model=list[PaymentRequestRead])
def list_event_payment_requests(event_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        select(PaymentRequest)
        .where(PaymentRequest.event_id == event_id)
        .order_by(PaymentRequest.id.desc())
    )
    return [enrich_payment_request_read(request) for request in result.scalars().all()]


@router.post("/event-items/{item_id}/payment-requests", response_model=PaymentRequestRead)
def create_payment_request(
    item_id: int,
    payload: PaymentRequestCreate,
    created_by_user_id: int,
    db: Session = Depends(get_db),
):
    """
    Создаёт заявку по конкретной позиции.

    v0.10:
    - invoice требует зафиксированный BIN / ИИН и налоговый статус
    - заявка забирает налоговый snapshot из позиции
    - карточка заявки показывает налоговый статус, но не суммы НДС/Вычетов
    """
    item = db.get(EventItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Event item not found")

    payment_method = normalize_payment_method(payload.payment_method or item.payment_method)
    if not payment_method:
        raise HTTPException(status_code=400, detail="payment_method is required")

    validate_payment_request_rules(item, payment_method, payload)

    remaining = calculate_item_remaining(item)
    warning_over_remaining = payload.amount_requested > remaining

    request = PaymentRequest(
        event_id=item.event_id,
        event_item_id=item.id,
        created_by_user_id=created_by_user_id,

        amount_requested=payload.amount_requested,
        payment_method=payment_method,
        status="new",
        comment=payload.comment,

        item_name_snapshot=item.external_name,
        item_amount_plan_snapshot=item.external_amount,
        item_amount_fact_snapshot=item.amount_fact,
        item_paid_amount_snapshot=item.paid_amount,
        item_remaining_snapshot=remaining,

        contractor_id=None,
        contractor_name_snapshot=None,
        iin_bin_snapshot=item.iin_bin if payment_method == "invoice" else None,
        tax_status_snapshot=item.tax_check_status if payment_method == "invoice" else (
            "self_employed" if payment_method == "self_employed" else None
        ),
        vat_status_snapshot="vat" if item.tax_check_status == "our_vat" else "no_vat",
        vat_amount_snapshot=item.vat_amount if payment_method == "invoice" else Decimal("0.00"),
        deduction_amount_snapshot=item.deduction_amount if payment_method == "invoice" else (
            item.deduction_amount if payment_method == "self_employed" else Decimal("0.00")
        ),
        tax_source_snapshot="event_item" if payment_method in {"invoice", "self_employed"} else None,

        card_number=payload.card_number,

        manual_tax_mode=False,
        manual_tax_set_by_user_id=None,
        manual_tax_set_at=None,

        warning_over_remaining=warning_over_remaining,

        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(request)
    db.commit()
    db.refresh(request)
    return enrich_payment_request_read(request)


@router.patch("/payment-requests/{request_id}/status", response_model=PaymentRequestRead)
def update_payment_request_status(
    request_id: int,
    payload: PaymentRequestStatusUpdate,
    db: Session = Depends(get_db),
):
    request = db.get(PaymentRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Payment request not found")

    allowed_statuses = {
        "new",
        "to_pay",
        "paid",
        "cash_received",
        "rejected",
        "tax_check_needed",
    }
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    old_status = request.status
    new_status = payload.status

    request.status = new_status
    request.updated_at = datetime.utcnow()

    if new_status == "paid" and old_status != "paid":
        request.paid_at = datetime.utcnow()

        item = db.get(EventItem, request.event_item_id)
        if item is not None:
            item.paid_amount = item.paid_amount + request.amount_requested
            item.updated_at = datetime.utcnow()
            db.add(item)

    if new_status == "cash_received":
        request.cash_received_at = datetime.utcnow()

    if new_status == "rejected":
        request.rejected_at = datetime.utcnow()

    db.add(request)
    db.commit()
    db.refresh(request)
    return enrich_payment_request_read(request)
