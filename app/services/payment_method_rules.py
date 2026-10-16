"""Payment-method fixation shared by website and Telegram."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.event_item import EventItem
from app.models.payment_request import PaymentRequest


def payment_method_label(method):
    return {"invoice":"По счету","cash":"Нал","card":"На карту","self_employed":"Самозанятый"}.get(method,method)


def active_payment_methods_for_item(db: Session, item_id: int) -> list[str]:
    return [
        str(method)
        for method in db.execute(
            select(PaymentRequest.payment_method)
            .where(
                PaymentRequest.event_item_id == int(item_id),
                PaymentRequest.status.notin_(["cancelled", "rejected"]),
                PaymentRequest.money_status != "cancelled",
            )
            .order_by(PaymentRequest.id.desc())
        ).scalars().all()
        if method
    ]


def validate_payment_method_lock(db: Session, item: EventItem, payment_method: str) -> None:
    if item.item_type in {"coordinator", "manager_salary"}:
        if payment_method not in {"cash", "card", "self_employed"}:
            raise HTTPException(
                status_code=400,
                detail="Для Координатора и ЗП менеджера доступны Нал, На карту и Самозанятый",
            )
        return

    active_methods = active_payment_methods_for_item(db, item.id)
    if active_methods:
        non_simple = next((method for method in active_methods if method not in {"cash", "card"}), None)
        if non_simple and payment_method != non_simple:
            raise HTTPException(
                status_code=409,
                detail=f"Способ оплаты уже закреплён за этой позицией: {payment_method_label(non_simple)}",
            )
        if non_simple is None and payment_method not in {"cash", "card"}:
            raise HTTPException(
                status_code=409,
                detail="По позиции уже есть заявки Нал/На карту. Можно выбирать только между этими двумя способами",
            )


def allowed_payment_methods(db: Session, item: EventItem) -> list[str]:
    if item.item_type in {"coordinator", "manager_salary"}:
        return ["cash", "card", "self_employed"]
    active = active_payment_methods_for_item(db, item.id)
    fixed = next((method for method in active if method not in {"cash", "card"}), None)
    if fixed:
        return [fixed]
    return ["cash", "card"] if active else ["cash", "card", "self_employed", "invoice"]
