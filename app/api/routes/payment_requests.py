from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event_item import EventItem
from app.models.payment_request import PaymentRequest
from app.schemas.payment_request import (
    PaymentRequestCreate,
    PaymentRequestRead,
    PaymentRequestStatusUpdate,
)


router = APIRouter(tags=["payment_requests"])


def calculate_item_remaining(item: EventItem) -> Decimal:
    """
    Остаток:
    - если факт есть: Факт - Оплачено
    - если факта нет: Сумма по смете - Оплачено
    """
    base_amount = item.amount_fact if item.amount_fact is not None else item.external_amount
    return base_amount - item.paid_amount


@router.get("/payment-requests", response_model=list[PaymentRequestRead])
def list_payment_requests(db: Session = Depends(get_db)):
    result = db.execute(select(PaymentRequest).order_by(PaymentRequest.id.desc()))
    return result.scalars().all()


@router.get("/events/{event_id}/payment-requests", response_model=list[PaymentRequestRead])
def list_event_payment_requests(event_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        select(PaymentRequest)
        .where(PaymentRequest.event_id == event_id)
        .order_by(PaymentRequest.id.desc())
    )
    return result.scalars().all()


@router.post("/event-items/{item_id}/payment-requests", response_model=PaymentRequestRead)
def create_payment_request(
    item_id: int,
    payload: PaymentRequestCreate,
    created_by_user_id: int,
    db: Session = Depends(get_db),
):
    """
    Создаёт заявку по конкретной позиции.

    Пока без КГД:
    - берём snapshot позиции
    - считаем остаток
    - если сумма заявки больше остатка, ставим warning_over_remaining = true
    """
    item = db.get(EventItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Event item not found")

    payment_method = payload.payment_method or item.payment_method
    if not payment_method:
        raise HTTPException(status_code=400, detail="payment_method is required")

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
        iin_bin_snapshot=item.iin_bin,
        tax_status_snapshot=item.tax_check_status,
        vat_status_snapshot=None,
        vat_amount_snapshot=item.vat_amount,
        deduction_amount_snapshot=item.deduction_amount,
        tax_source_snapshot=None,

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
    return request


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
    return request
