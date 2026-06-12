"""
Contrast Finance Telegram bot for the new v0.40 site.

Port of the stable Apps Script bot mechanics to the new PostgreSQL backend.
Run as a separate Railway worker/process:
    python -m app.telegram_bot.main
"""

from __future__ import annotations

import asyncio
import html
import os
import re
import time
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import and_, extract, not_, or_, select
from sqlalchemy.orm import Session
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.contractor import Contractor
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.event_share import EventShare
from app.models.payment_request import PaymentRequest
from app.models.taxpayer_check import TaxpayerCheck
from app.models.telegram_message import TelegramMessage
from app.models.user import User
from app.services.auth import verify_pin
from app.services.event_calculator import calculate_event_summary_values, q
from app.services.kgd.client import check_taxpayer


BOT_VERSION = "CONTRAST_FINANCE_BOT_V0.40.19_NEW_SITE"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID") or os.getenv("ADMIN_CHAT_ID") or "0")
TATYANA_CHAT_ID = int(os.getenv("TELEGRAM_TATYANA_CHAT_ID") or os.getenv("TATYANA_CHAT_ID") or "0")
TATYANA_ENABLED = str(os.getenv("TELEGRAM_TATYANA_ENABLED") or "false").strip().lower() in {"1", "true", "yes", "on"}
POLL_SECONDS = int(os.getenv("TELEGRAM_POLL_SECONDS") or os.getenv("POLL_SITE_REQUESTS_SECONDS") or "20")
POLL_BATCH_LIMIT = int(os.getenv("TELEGRAM_POLL_BATCH_LIMIT") or os.getenv("BOT_POLL_BATCH_LIMIT") or "10")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name) or "").strip() or default)
    except Exception:
        return default


# Telegram should not surface old legacy/test events in the payment flow.
# By default managers see events from the current calendar year and later.
# If an import/migration needs another year temporarily, set TELEGRAM_MIN_EVENT_YEAR.
TELEGRAM_MIN_EVENT_YEAR = env_int("TELEGRAM_MIN_EVENT_YEAR", date.today().year)
TELEGRAM_DIRTY_MARKER_AT = datetime(2000, 1, 1)

# Prevent Telegram spam after Railway redeploys. By default the bot publishes
# only payment requests created after this worker started. Old active requests
# without saved Telegram message rows are not sent again automatically.
BOT_STARTED_AT = datetime.utcnow()
TELEGRAM_PUBLISH_EXISTING_REQUESTS_ON_START = env_bool("TELEGRAM_PUBLISH_EXISTING_REQUESTS_ON_START", False)

(
    BIND_PHONE,
    BIND_PIN,
    CHOOSE_MONTH,
    CHOOSE_EVENT,
    CHOOSE_ITEM,
    EXTRA_POSITION_NAME,
    PAYMENT_METHOD,
    BIN_IIN,
    AMOUNT,
    CARD_NUMBER,
    COMMENT,
) = range(11)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["Новая заявка"], ["Мои заявки", "Привязать аккаунт"], ["Отменить"]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

PAYMENT_METHODS = ["По счету", "Самозанятый", "На карту", "Нал"]
EXTRA_ITEM_ID = "extra"
SALARY_ITEM_ID = "salary"
FLOW_CLEANUP_KEY = "payment_flow_message_ids"
BOUND_USER_CACHE: Dict[str, Dict[str, Any]] = {}
BOUND_USER_CACHE_TTL_SECONDS = 24 * 60 * 60
RECENTLY_PUBLISHED: Dict[str, float] = {}
RECENTLY_PUBLISHED_TTL_SECONDS = 10 * 60

RU_MONTHS = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


@contextmanager
def db_session():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_env() -> None:
    missing = []
    if not BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not ADMIN_CHAT_ID:
        missing.append("TELEGRAM_ADMIN_CHAT_ID")
    if missing:
        raise RuntimeError("Не заданы переменные окружения: " + ", ".join(missing))


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def money(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def fmt_money(value: Any) -> str:
    try:
        n = int(round(float(value or 0)))
    except Exception:
        n = 0
    return f"{n:,}".replace(",", " ") + " ₸"


def short(text: Any, limit: int = 42) -> str:
    value = str(text or "").strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def clean_digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def clean_bin_iin(value: Any) -> str:
    return clean_digits(value)


def normalize_phone(raw: str) -> Optional[str]:
    digits = clean_digits(raw)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) != 11 or not digits.startswith("7"):
        return None
    return digits


def format_phone(digits: str) -> str:
    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


def money_number(raw: str) -> Optional[int]:
    text = (raw or "").lower().strip()
    text = text.replace("₸", "").replace("kzt", "").replace("тенге", "").replace("тг", "")
    text = text.replace("\u00a0", " ").strip()
    if re.fullmatch(r"\d+", text):
        digits = text
    elif re.fullmatch(r"\d{1,3}([ .,]\d{3})+", text):
        digits = re.sub(r"[ .,]", "", text)
    else:
        return None
    amount = int(digits)
    return amount if amount > 0 else None


def format_card_number(value: Any) -> str:
    digits = clean_digits(value)
    if len(digits) == 16:
        return " ".join(digits[i:i + 4] for i in range(0, 16, 4))
    return str(value or "").strip()


def month_label(month: date) -> str:
    return f"{RU_MONTHS.get(month.month, month.month)} {month.year}"


def month_key_from_event_date(value: date) -> str:
    return f"{int(value.year):04d}-{int(value.month):02d}"


def parse_month_key(key: str) -> date:
    year, month = [int(part) for part in str(key).split("-")[:2]]
    return date(year, month, 1)


def payment_method_code(label: str | None) -> str | None:
    aliases = {
        "по счету": "invoice",
        "по счёту": "invoice",
        "invoice": "invoice",
        "самозанятый": "self_employed",
        "self_employed": "self_employed",
        "на карту": "card",
        "card": "card",
        "нал": "cash",
        "налик": "cash",
        "cash": "cash",
    }
    key = str(label or "").strip().lower()
    return aliases.get(key)


def payment_method_label(code: str | None) -> str:
    return {
        "invoice": "По счету",
        "self_employed": "Самозанятый",
        "card": "На карту",
        "cash": "Нал",
    }.get(str(code or ""), str(code or ""))


def tax_status_label(status: str | None) -> str:
    return {
        "our_vat": "ОУР с НДС",
        "our_no_vat": "ОУР без НДС",
        "simplified": "Упрощенка",
        "snr": "СНР",
        "self_employed": "Самозанятый",
        "not_found": "Не проверен",
    }.get(str(status or ""), str(status or ""))


def payment_status_label(status: str | None) -> str:
    status = str(status or "new")
    if status in {"new", "to_pay", "tax_check_needed"}:
        return "🕒 На оплату"
    if status == "paid":
        return "✅ Оплачено"
    if status == "rejected":
        return "❌ Отклонено"
    if status == "cancelled":
        return "❌ Отменено"
    return status


def money_status_label(status: str | None) -> str:
    status = str(status or "waiting_money")
    if status == "cash_received":
        return "✅ Деньги в кассе"
    if status == "cancelled":
        return ""
    return "💰 Ждём деньги"


def is_terminal_for_admin_manager(request: PaymentRequest) -> bool:
    # В новой системе статус оплаты подрядчику и статус денег клиента живут отдельно.
    # Карточку нельзя удалять только потому, что деньги уже в кассе: если оплата
    # подрядчику ещё new/to_pay, админу всё ещё нужно обработать заявку.
    # Но отмена/отклонение заявки — всегда финальное состояние для Telegram,
    # даже если money_status до этого уже был cash_received.
    payment_status = str(getattr(request, "status", "") or "").strip()
    money_status = str(getattr(request, "money_status", "") or "").strip()
    return bool(
        payment_status in {"rejected", "cancelled"}
        or money_status == "cancelled"
        or (payment_status == "paid" and money_status == "cash_received")
    )


def is_active_for_manager(request: PaymentRequest) -> bool:
    return request.status in {"new", "to_pay", "paid", "tax_check_needed"} and not is_terminal_for_admin_manager(request)


def should_notify_tatyana(request: PaymentRequest) -> bool:
    return bool(
        TATYANA_ENABLED
        and TATYANA_CHAT_ID
        and request.payment_method in {"invoice", "self_employed"}
    )


def looks_like_card_number(value: Any) -> bool:
    return len(clean_digits(value)) == 16


def comment_has_surname(value: Any) -> bool:
    words = [word.strip(" ,.;:!?()[]{}") for word in str(value or "").split()]
    return any(len(word) >= 2 and any(ch.isalpha() for ch in word) for word in words)


def get_user_by_telegram_id(db: Session, telegram_id: Any) -> Optional[User]:
    return db.execute(
        select(User).where(
            User.telegram_id == str(telegram_id),
            User.role == "manager",
            User.is_active == True,  # noqa: E712
        )
    ).scalars().first()


def get_cached_bound_user(telegram_id: Any) -> Optional[Dict[str, Any]]:
    key = str(telegram_id or "").strip()
    item = BOUND_USER_CACHE.get(key)
    if not item:
        return None
    if time.time() - float(item.get("ts", 0)) > BOUND_USER_CACHE_TTL_SECONDS:
        BOUND_USER_CACHE.pop(key, None)
        return None
    return item.get("user")


def set_cached_bound_user(user: User) -> None:
    if not user.telegram_id:
        return
    BOUND_USER_CACHE[str(user.telegram_id)] = {
        "ts": time.time(),
        "user": {"id": user.id, "name": user.name, "department_id": user.department_id},
    }


def bind_user_by_phone_pin(db: Session, telegram_user, phone_digits: str, pin: str) -> User:
    users = db.execute(
        select(User).where(
            User.role == "manager",
            User.is_active == True,  # noqa: E712
        )
    ).scalars().all()
    user = next((u for u in users if normalize_phone(u.phone or "") == phone_digits), None)
    if user is None or not verify_pin(user, pin):
        raise RuntimeError("Неверный телефон или PIN")
    user.telegram_id = str(telegram_user.id)
    user.telegram_username = telegram_user.username or user.telegram_username
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    set_cached_bound_user(user)
    return user


def ensure_manager_from_telegram(telegram_id: Any) -> Optional[User]:
    with db_session() as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if user:
            set_cached_bound_user(user)
        return user


def bot_min_event_date() -> date:
    year = TELEGRAM_MIN_EVENT_YEAR or date.today().year
    return date(max(2000, int(year)), 1, 1)


def manager_event_query(db: Session, user: User, month: date | None = None):
    shared_event_ids = select(EventShare.event_id).where(EventShare.user_id == user.id)
    query = select(Event).where(
        or_(Event.manager_id == user.id, Event.id.in_(shared_event_ids)),
        Event.status != "cancelled",
        Event.event_date >= bot_min_event_date(),
    )
    if month is not None:
        query = query.where(
            extract("year", Event.event_date) == month.year,
            extract("month", Event.event_date) == month.month,
        )
    return query.order_by(Event.event_date, Event.id)


def load_manager_flow(telegram_id: Any) -> Dict[str, Any]:
    with db_session() as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if user is None:
            raise RuntimeError("Аккаунт Telegram не привязан к менеджеру")
        events = db.execute(manager_event_query(db, user)).scalars().unique().all()
        months_map: Dict[str, List[Dict[str, Any]]] = {}
        for event in events:
            key = month_key_from_event_date(event.event_date)
            months_map.setdefault(key, []).append({
                "eventId": event.id,
                "eventDate": event.event_date.strftime("%d-%m-%Y"),
                "customerName": event.client_name,
                "eventName": event.title,
                "status": event.status,
                "moneyStatus": event.money_status,
            })
        month_keys = sorted(months_map.keys())
        return {
            "months": [month_label(parse_month_key(key)) for key in month_keys],
            "monthKeys": month_keys,
            "eventsByMonth": {month_label(parse_month_key(key)): value for key, value in months_map.items()},
        }



ACTIVE_PAYMENT_STATUSES_FOR_LOCK = {"new", "to_pay", "paid", "tax_check_needed"}


def active_payment_requests_for_item(db: Session, item_id: int) -> List[PaymentRequest]:
    """Requests that still lock payment method for an item.

    Telegram must mirror the site: a method is fixed only after a real active
    payment request exists, or for invoice after BIN/IIN was checked and locked.
    A draft self-employed value on the item alone is not a hard lock.
    """
    if not item_id:
        return []
    return db.execute(
        select(PaymentRequest)
        .where(
            PaymentRequest.event_item_id == int(item_id),
            PaymentRequest.status.in_(list(ACTIVE_PAYMENT_STATUSES_FOR_LOCK)),
            PaymentRequest.money_status != "cancelled",
        )
        .order_by(PaymentRequest.id.desc())
    ).scalars().all()


def item_has_locked_invoice_payment(item: EventItem) -> bool:
    return bool(item and item.iin_bin and item.iin_bin_locked)


def fixed_payment_method_for_item(db: Session, item: EventItem | None, is_salary: bool = False) -> Optional[str]:
    if item is None:
        return None
    if is_salary:
        return None
    if item.item_type == "coordinator":
        return "cash"

    active_request = active_payment_requests_for_item(db, int(item.id))[0:1]
    if active_request:
        return active_request[0].payment_method

    if item_has_locked_invoice_payment(item):
        return "invoice"

    return None


def payment_method_locked_for_item(db: Session, item: EventItem | None, is_salary: bool = False) -> bool:
    return fixed_payment_method_for_item(db, item, is_salary=is_salary) is not None


def self_employed_surname_from_note(note: Any) -> str:
    text = str(note or "").strip()
    match = re.search(r"Самозанятый\s*:\s*(.+)", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def self_employed_surname_from_item(item: EventItem | None) -> str:
    return self_employed_surname_from_note(getattr(item, "internal_note", None))


def self_employed_surname_from_bot_item(item: Dict[str, Any] | None) -> str:
    if not item:
        return ""
    return str(item.get("selfEmployedSurname") or "").strip() or self_employed_surname_from_note(item.get("internalNote"))


def contractor_name_for_invoice(db: Session, item: EventItem | None) -> str:
    if item is None or not item.iin_bin:
        return ""

    contractor = db.execute(
        select(Contractor)
        .where(Contractor.iin_bin == item.iin_bin)
        .order_by(Contractor.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if contractor and contractor.name:
        return str(contractor.name).strip()

    check = db.execute(
        select(TaxpayerCheck)
        .where(TaxpayerCheck.iin_bin == item.iin_bin)
        .order_by(TaxpayerCheck.checked_at.desc(), TaxpayerCheck.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return str(getattr(check, "name_result", None) or "").strip()

def event_items_for_bot(db: Session, event: Event) -> List[Dict[str, Any]]:
    items = db.execute(
        select(EventItem)
        .where(EventItem.event_id == event.id, EventItem.is_deleted == False)  # noqa: E712
        .order_by(EventItem.sort_order, EventItem.id)
    ).scalars().all()
    rows: List[Dict[str, Any]] = []
    for item in items:
        if item.item_type == "manager_salary":
            continue
        base_amount = item.amount_fact if item.amount_fact is not None else item.external_amount
        fixed_method = fixed_payment_method_for_item(db, item)
        rows.append({
            "itemId": str(item.id),
            "positionName": item.external_name,
            "budgetAmount": str(base_amount or 0),
            "paidAmount": str(item.paid_amount or 0),
            "paymentMethod": item.payment_method,
            "fixedPaymentMethod": fixed_method,
            "paymentMethodLocked": bool(fixed_method),
            "iinBin": item.iin_bin,
            "iinBinLocked": bool(item.iin_bin_locked),
            "taxCheckStatus": item.tax_check_status,
            "internalNote": item.internal_note,
            "selfEmployedSurname": self_employed_surname_from_item(item),
            "isManagerSalary": False,
        })

    summary = calculate_event_summary_values(event, items)
    manager_salary = money(summary.get("manager_salary"))
    if manager_salary > 0:
        paid_salary = money(summary.get("manager_salary_paid"))
        rows.append({
            "itemId": SALARY_ITEM_ID,
            "positionName": "ЗП менеджера",
            "budgetAmount": str(manager_salary),
            "paidAmount": str(paid_salary),
            "paymentMethod": None,
            "fixedPaymentMethod": None,
            "paymentMethodLocked": False,
            "isManagerSalary": True,
        })
    return rows


def load_items_data(telegram_id: Any, event_id: Any) -> Dict[str, Any]:
    with db_session() as db:
        user = get_user_by_telegram_id(db, telegram_id)
        event = db.get(Event, int(event_id))
        if user is None or event is None:
            raise RuntimeError("Мероприятие не найдено")
        shared = db.execute(select(EventShare).where(EventShare.event_id == event.id, EventShare.user_id == user.id)).scalar_one_or_none()
        if event.manager_id != user.id and shared is None:
            raise RuntimeError("Нет доступа к мероприятию")
        return {"overview": event_items_for_bot(db, event), "allowExtraPosition": True}


def calculate_tax_values(amount_base: Decimal, tax_status: str) -> tuple[Decimal, Decimal]:
    settings = get_settings()
    if amount_base is None:
        amount_base = Decimal("0.00")
    if tax_status == "our_vat":
        amount_without_vat = amount_base / (Decimal("1.00") + settings.VAT_RATE)
        vat = amount_base - amount_without_vat
        deduction = amount_without_vat * settings.CONTRACTOR_DEDUCTION_RATE
        return vat.quantize(Decimal("0.01")), deduction.quantize(Decimal("0.01"))
    if tax_status in {"our_no_vat", "self_employed"}:
        return Decimal("0.00"), (amount_base * settings.CONTRACTOR_DEDUCTION_RATE).quantize(Decimal("0.01"))
    return Decimal("0.00"), Decimal("0.00")


def upsert_contractor(db: Session, iin_bin: str, tax_status: str, vat: Decimal, deduction: Decimal, source: str, name: str | None) -> Contractor:
    contractor = db.execute(select(Contractor).where(Contractor.iin_bin == iin_bin)).scalars().first()
    if contractor is None:
        contractor = Contractor(
            iin_bin=iin_bin,
            name=name,
            tax_status=tax_status,
            vat_status="vat" if tax_status == "our_vat" else "no_vat",
            vat_amount=vat,
            deduction_amount=deduction,
            source=source,
            last_checked_at=datetime.utcnow(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    else:
        contractor.name = name or contractor.name
        contractor.tax_status = tax_status
        contractor.vat_status = "vat" if tax_status == "our_vat" else "no_vat"
        contractor.vat_amount = vat
        contractor.deduction_amount = deduction
        contractor.source = source
        contractor.last_checked_at = datetime.utcnow()
        contractor.updated_at = datetime.utcnow()
    db.add(contractor)
    db.flush()
    return contractor


def write_taxpayer_check(db: Session, contractor: Contractor | None, iin_bin: str, tax_status: str, source: str, message: str, raw_response: dict | None) -> None:
    db.add(TaxpayerCheck(
        contractor_id=contractor.id if contractor else None,
        iin_bin=iin_bin,
        name_result=contractor.name if contractor else None,
        tax_status_result=tax_status,
        vat_status_result="vat" if tax_status == "our_vat" else "no_vat",
        status="success" if tax_status != "not_found" else "not_found",
        source=source,
        raw_response_json=raw_response,
        error_message=None if tax_status != "not_found" else message,
        checked_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    ))


def apply_invoice_tax_to_item(db: Session, item: EventItem, iin_bin: str) -> Dict[str, Any]:
    result = check_taxpayer(iin_bin)
    base = item.amount_fact if item.amount_fact is not None else item.external_amount
    vat, deduction = calculate_tax_values(money(base), result.tax_status)
    contractor = None
    if result.tax_status != "not_found":
        contractor = upsert_contractor(
            db,
            result.iin_bin,
            result.tax_status,
            vat,
            deduction,
            result.source,
            result.contractor_name,
        )
        item.iin_bin_locked = True
    else:
        item.iin_bin_locked = False
        vat = Decimal("0.00")
        deduction = Decimal("0.00")
    item.iin_bin = result.iin_bin
    item.payment_method = "invoice"
    item.tax_check_status = result.tax_status
    item.vat_amount = vat
    item.deduction_amount = deduction
    item.updated_at = datetime.utcnow()
    db.add(item)
    write_taxpayer_check(db, contractor, result.iin_bin, result.tax_status, result.source, result.message, result.raw_response)
    return {
        "iin_bin": result.iin_bin,
        "contractor_name": result.contractor_name,
        "tax_status": result.tax_status,
        "message": result.message,
        "source": result.source,
    }


def create_extra_item(db: Session, event: Event, name: str, amount: Decimal, method: str) -> EventItem:
    max_order = db.execute(
        select(EventItem.sort_order).where(EventItem.event_id == event.id).order_by(EventItem.sort_order.desc())
    ).scalars().first()
    item = EventItem(
        event_id=event.id,
        item_type="regular",
        external_name=name,
        # Доппозиция из заявки — это фактический расход, а не строка клиентской сметы.
        external_price=Decimal("0.00"),
        external_quantity=Decimal("1.00"),
        external_days=Decimal("1.00"),
        external_amount=Decimal("0.00"),
        external_note=None,
        amount_fact=amount,
        paid_amount=Decimal("0.00"),
        payment_method=method,
        iin_bin=None,
        iin_bin_locked=False,
        tax_check_status="self_employed" if method == "self_employed" else None,
        vat_amount=Decimal("0.00"),
        deduction_amount=(amount * get_settings().CONTRACTOR_DEDUCTION_RATE).quantize(Decimal("0.01")) if method == "self_employed" else Decimal("0.00"),
        internal_note="Добавлено из Telegram-бота",
        sort_order=int(max_order or 0) + 10,
        is_deleted=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    db.flush()
    return item


def get_or_create_salary_item(db: Session, event: Event, amount: Decimal) -> EventItem:
    item = db.execute(
        select(EventItem).where(
            EventItem.event_id == event.id,
            EventItem.item_type == "manager_salary",
            EventItem.is_deleted == False,  # noqa: E712
        ).order_by(EventItem.id)
    ).scalars().first()
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
            amount_fact=q(amount),
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
    else:
        item.amount_fact = q(amount)
        item.updated_at = datetime.utcnow()
    db.add(item)
    db.flush()
    return item


def remaining_for_item(item: EventItem) -> Decimal:
    base = item.amount_fact if item.amount_fact is not None else item.external_amount
    return money(base) - money(item.paid_amount)


def validate_bot_request(item: EventItem, method: str, amount: Decimal, card_number: str | None, comment: str | None) -> None:
    if method == "invoice":
        if not item.iin_bin or not item.iin_bin_locked or not item.tax_check_status or item.tax_check_status == "not_found":
            raise RuntimeError("Для По счету нужен проверенный BIN/ИИН. Проверь БИН/ИИН ещё раз или выбери другой способ.")
    if method == "card" and not looks_like_card_number(card_number):
        raise RuntimeError("Для На карту нужен номер карты из 16 цифр")
    if method == "self_employed" and not (comment_has_surname(comment) or self_employed_surname_from_item(item)):
        raise RuntimeError("Для Самозанятого фамилия обязательна в комментарии")
    if method not in {"invoice", "card", "cash", "self_employed"}:
        raise RuntimeError("Некорректный способ оплаты")
    if amount <= 0:
        raise RuntimeError("Сумма должна быть больше 0")


def create_payment_request_from_bot(telegram_id: Any, payload: Dict[str, Any]) -> PaymentRequest:
    with db_session() as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if user is None:
            raise RuntimeError("Аккаунт Telegram не привязан к менеджеру")
        event = db.get(Event, int(payload["event_id"]))
        if event is None:
            raise RuntimeError("Мероприятие не найдено")
        shared = db.execute(select(EventShare).where(EventShare.event_id == event.id, EventShare.user_id == user.id)).scalar_one_or_none()
        if event.manager_id != user.id and shared is None:
            raise RuntimeError("Нет доступа к мероприятию")

        method = payment_method_code(payload.get("payment_method"))
        if method is None:
            raise RuntimeError("Выбери способ оплаты")
        amount = money(payload.get("amount"))
        item_token = str(payload.get("item_id") or "")
        comment = str(payload.get("comment") or "").strip() or None

        if item_token == EXTRA_ITEM_ID:
            item = create_extra_item(db, event, str(payload.get("new_position_name") or "Допрасход").strip(), amount, method)
            if method == "invoice":
                apply_invoice_tax_to_item(db, item, str(payload.get("bin_iin") or ""))
            elif method == "self_employed" and comment_has_surname(comment):
                item.internal_note = f"Самозанятый: {comment}"
                db.add(item)
                db.flush()
        elif item_token == SALARY_ITEM_ID:
            if method not in {"card", "cash"}:
                raise RuntimeError("ЗП менеджера можно оформить только На карту или Нал")
            items = db.execute(
                select(EventItem).where(EventItem.event_id == event.id, EventItem.is_deleted == False)  # noqa: E712
            ).scalars().all()
            summary = calculate_event_summary_values(event, items)
            item = get_or_create_salary_item(db, event, money(summary.get("manager_salary")))
            item.payment_method = method
            db.add(item)
        else:
            item = db.get(EventItem, int(item_token))
            if item is None or item.event_id != event.id or item.is_deleted:
                raise RuntimeError("Позиция не найдена")

            fixed_method = fixed_payment_method_for_item(db, item)
            if fixed_method and method != fixed_method:
                raise RuntimeError(f"Способ оплаты уже закреплён за этой позицией: {payment_method_label(fixed_method)}")
            method = fixed_method or method

            item.payment_method = method
            if method == "invoice":
                if payload.get("bin_iin"):
                    apply_invoice_tax_to_item(db, item, str(payload.get("bin_iin")))
                elif not item_has_locked_invoice_payment(item):
                    raise RuntimeError("Для По счету сначала проверь БИН/ИИН")
            elif method == "self_employed":
                base = item.amount_fact if item.amount_fact is not None else item.external_amount
                item.tax_check_status = "self_employed"
                item.iin_bin = None
                item.iin_bin_locked = False
                item.vat_amount = Decimal("0.00")
                item.deduction_amount = (money(base) * get_settings().CONTRACTOR_DEDUCTION_RATE).quantize(Decimal("0.01"))
                if comment_has_surname(comment):
                    item.internal_note = f"Самозанятый: {comment}"
            elif method in {"card", "cash"}:
                item.iin_bin = None
                item.iin_bin_locked = False
                item.tax_check_status = None
                item.vat_amount = Decimal("0.00")
                item.deduction_amount = Decimal("0.00")
            item.updated_at = datetime.utcnow()
            db.add(item)
            db.flush()

        card_number = clean_digits(payload.get("card_number")) if method == "card" else None
        validate_bot_request(item, method, amount, card_number, comment)
        remaining = remaining_for_item(item)

        request = PaymentRequest(
            event_id=event.id,
            event_item_id=item.id,
            created_by_user_id=user.id,
            amount_requested=amount,
            payment_method=method,
            status="new",
            money_status=getattr(event, "money_status", "waiting_money"),
            comment=comment,
            item_name_snapshot=item.external_name,
            item_amount_plan_snapshot=item.external_amount,
            item_amount_fact_snapshot=item.amount_fact,
            item_paid_amount_snapshot=item.paid_amount,
            item_remaining_snapshot=remaining,
            contractor_id=(
                db.execute(select(Contractor.id).where(Contractor.iin_bin == item.iin_bin).limit(1)).scalar_one_or_none()
                if method == "invoice" and item.iin_bin else None
            ),
            contractor_name_snapshot=(
                contractor_name_for_invoice(db, item) if method == "invoice"
                else ((comment or self_employed_surname_from_item(item)) if method == "self_employed" else None)
            ),
            iin_bin_snapshot=item.iin_bin if method == "invoice" else None,
            tax_status_snapshot=item.tax_check_status if method == "invoice" else ("self_employed" if method == "self_employed" else None),
            vat_status_snapshot="vat" if item.tax_check_status == "our_vat" else ("no_vat" if method in {"invoice", "self_employed"} else None),
            vat_amount_snapshot=item.vat_amount if method == "invoice" else Decimal("0.00"),
            deduction_amount_snapshot=item.deduction_amount if method in {"invoice", "self_employed"} else Decimal("0.00"),
            tax_source_snapshot="event_item" if method in {"invoice", "self_employed"} else None,
            card_number=card_number,
            manual_tax_mode=False,
            warning_over_remaining=amount > remaining,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request


def request_dict_for_card(request: PaymentRequest, db: Session) -> Dict[str, Any]:
    event = db.get(Event, request.event_id)
    manager = db.get(User, event.manager_id) if event and event.manager_id else None
    item = db.get(EventItem, request.event_item_id) if request.event_item_id else None
    contractor_name = request.contractor_name_snapshot
    if request.payment_method == "invoice" and not contractor_name:
        contractor_name = contractor_name_for_invoice(db, item)
    return {
        "paymentId": request.id,
        "managerName": manager.name if manager else "",
        "telegramId": manager.telegram_id if manager else "",
        "customerName": event.client_name if event else "",
        "eventName": event.title if event else "",
        "eventDate": event.event_date.strftime("%d-%m-%Y") if event and event.event_date else "",
        "positionName": request.item_name_snapshot,
        "contractorName": contractor_name,
        "requestPaymentType": payment_method_label(request.payment_method),
        "cardNumber": request.card_number,
        "iinBin": request.iin_bin_snapshot,
        "taxStatus": request.tax_status_snapshot,
        "taxStatusLabel": tax_status_label(request.tax_status_snapshot),
        "requestAmount": request.amount_requested,
        "managerComment": request.comment,
        "status": request.status,
        "paymentStatusLabel": payment_status_label(request.status),
        "moneyStatus": request.money_status,
        "moneyStatusLabel": money_status_label(request.money_status),
        "warningOverRemaining": request.warning_over_remaining,
    }


def payment_text_from_request(request: PaymentRequest, title: str = "🧾 Заявка на оплату") -> str:
    with db_session() as db:
        req = db.get(PaymentRequest, int(request.id))
        if req is None:
            return f"{esc(title)}\n\nЗаявка #{esc(request.id)} не найдена"
        data = request_dict_for_card(req, db)
    card_line = f"\nКарта: <code>{esc(format_card_number(data.get('cardNumber')))}</code>" if data.get("cardNumber") else ""
    tax_line = f"\nНалоговый режим: <b>{esc(data.get('taxStatusLabel'))}</b>" if data.get("taxStatusLabel") else ""
    contractor = data.get("contractorName") or ""
    comment_line = f"\nКомментарий: {esc(data.get('managerComment'))}" if data.get("managerComment") else ""
    money_line = f"\nСтатус денег: <b>{esc(data.get('moneyStatusLabel'))}</b>" if data.get("moneyStatusLabel") else ""
    warning_line = "\n⚠️ Сумма больше остатка по позиции" if data.get("warningOverRemaining") else ""
    return (
        f"{esc(title)}\n\n"
        f"№: <b>{esc(data.get('paymentId'))}</b>\n"
        f"Менеджер: <b>{esc(data.get('managerName'))}</b>\n"
        f"Заказчик: {esc(data.get('customerName'))}\n"
        f"Мероприятие: {esc(data.get('eventName'))}\n"
        f"Дата: {esc(data.get('eventDate'))}\n\n"
        f"Позиция: <b>{esc(data.get('positionName'))}</b>\n"
        f"Подрядчик: {esc(contractor)}\n"
        f"Способ оплаты: {esc(data.get('requestPaymentType'))}{card_line}{tax_line}\n"
        f"Сумма заявки: <b>{fmt_money(data.get('requestAmount'))}</b>{comment_line}{warning_line}\n\n"
        f"Статус оплаты: <b>{esc(data.get('paymentStatusLabel'))}</b>"
        f"{money_line}"
    )


def admin_keyboard(request: PaymentRequest) -> Optional[InlineKeyboardMarkup]:
    if request.status in {"new", "to_pay", "tax_check_needed"}:
        return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Оплачено", callback_data=f"admin:paid:{request.id}"), InlineKeyboardButton("❌ Отклонить", callback_data=f"admin:reject:{request.id}")]])
    if request.status == "paid" and request.money_status != "cash_received":
        return InlineKeyboardMarkup([[InlineKeyboardButton("💰 Деньги в кассе", callback_data=f"admin:cashin:{request.id}")]])
    return None


def manager_keyboard(request: PaymentRequest) -> Optional[InlineKeyboardMarkup]:
    if request.status in {"new", "to_pay", "tax_check_needed"}:
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отменить заявку", callback_data=f"manager:cancel:{request.id}")]])
    return None


def month_keyboard(months: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(months), 2):
        rows.append([InlineKeyboardButton(month, callback_data=f"month:{i + j}") for j, month in enumerate(months[i:i + 2])])
    return InlineKeyboardMarkup(rows)


def events_keyboard(events: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = []
    for idx, event in enumerate(events):
        label = f"{event.get('eventDate', '')} · {short(event.get('customerName') or event.get('eventName'), 34)}"
        rows.append([InlineKeyboardButton(label, callback_data=f"event:{idx}")])
    rows.append([InlineKeyboardButton("← Назад к месяцам", callback_data="back:months")])
    return InlineKeyboardMarkup(rows)


def items_keyboard(items: List[Dict[str, Any]], allow_extra: bool) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        item_id = str(item.get("itemId"))
        paid = fmt_money(item.get("paidAmount"))
        base = fmt_money(item.get("budgetAmount"))
        amount_label = "21%" if item.get("isManagerSalary") else "факт"
        label = f"{short(item.get('positionName'), 28)} · {amount_label} {base} · оплачено {paid}"
        rows.append([InlineKeyboardButton(label, callback_data=f"item:{item_id}")])
    if allow_extra:
        rows.append([InlineKeyboardButton("+ Добавить позицию", callback_data=f"item:{EXTRA_ITEM_ID}")])
    rows.append([InlineKeyboardButton("← Назад к мероприятиям", callback_data="back:events")])
    return InlineKeyboardMarkup(rows)


def payment_method_keyboard(is_salary: bool = False, fixed_method: str | None = None) -> InlineKeyboardMarkup:
    if fixed_method:
        methods = [payment_method_label(fixed_method)]
    else:
        methods = ["На карту", "Нал"] if is_salary else PAYMENT_METHODS
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"paymethod:{label}")] for label in methods])


def remember_recently_published(payment_id: Any) -> None:
    if payment_id:
        RECENTLY_PUBLISHED[str(payment_id)] = time.time()


def is_recently_published(payment_id: Any) -> bool:
    now = time.time()
    for key, ts in list(RECENTLY_PUBLISHED.items()):
        if now - ts > RECENTLY_PUBLISHED_TTL_SECONDS:
            RECENTLY_PUBLISHED.pop(key, None)
    ts = RECENTLY_PUBLISHED.get(str(payment_id or ""))
    return bool(ts and now - ts <= RECENTLY_PUBLISHED_TTL_SECONDS)


def save_message(db: Session, request_id: int, chat_id: Any, message_id: Any, message_type: str, recipient_user_id: int | None = None) -> None:
    if not chat_id or not message_id:
        return
    db.add(TelegramMessage(
        payment_request_id=request_id,
        chat_id=str(chat_id),
        message_id=str(message_id),
        message_type=message_type,
        recipient_user_id=recipient_user_id,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ))


def active_messages(db: Session, request_id: int, message_type: str | None = None) -> List[TelegramMessage]:
    query = select(TelegramMessage).where(
        TelegramMessage.payment_request_id == request_id,
        TelegramMessage.status == "active",
    )
    if message_type:
        query = query.where(TelegramMessage.message_type == message_type)
    return db.execute(query).scalars().all()


async def safe_delete(bot, message: TelegramMessage) -> bool:
    try:
        await bot.delete_message(chat_id=int(message.chat_id), message_id=int(message.message_id))
        return True
    except Exception as err:
        err_text = str(err)
        # If the message is already gone, Telegram returns an error, but for our
        # sync flow this is still a successful deletion: the user no longer sees it.
        already_gone = "not found" in err_text.lower() or "message to delete not found" in err_text.lower()
        with db_session() as db:
            msg = db.get(TelegramMessage, message.id)
            if msg:
                if already_gone:
                    msg.status = "deleted"
                    msg.deleted_at = datetime.utcnow()
                    msg.error_message = None
                else:
                    msg.status = "failed"
                    msg.error_message = err_text
                msg.updated_at = datetime.utcnow()
                db.add(msg)
                db.commit()
        return already_gone


async def safe_delete_raw(bot, chat_id: Any, message_id: Any) -> bool:
    if not chat_id or not message_id:
        return False
    try:
        await bot.delete_message(chat_id=int(chat_id), message_id=int(message_id))
        return True
    except Exception as err:
        err_text = str(err).lower()
        return "not found" in err_text or "message to delete not found" in err_text


async def safe_edit(bot, message: TelegramMessage, request: PaymentRequest, title: str, is_admin: bool = False, is_manager: bool = False) -> bool:
    try:
        await bot.edit_message_text(
            chat_id=int(message.chat_id),
            message_id=int(message.message_id),
            text=payment_text_from_request(request, title),
            parse_mode="HTML",
            reply_markup=admin_keyboard(request) if is_admin else (manager_keyboard(request) if is_manager else None),
        )
        with db_session() as db:
            msg = db.get(TelegramMessage, message.id)
            if msg:
                msg.status = "active"
                msg.error_message = None
                msg.updated_at = datetime.utcnow()
                db.add(msg)
                db.commit()
        return True
    except Exception as err:
        # Telegram raises "message is not modified" when the card already has the same
        # status/text. Treat it as a successful sync and move this message to the end
        # of the polling queue, otherwise the bot keeps syncing the same old cards.
        err_text = str(err)
        if "not modified" in err_text.lower():
            with db_session() as db:
                msg = db.get(TelegramMessage, message.id)
                if msg:
                    msg.status = "active"
                    msg.error_message = None
                    msg.updated_at = datetime.utcnow()
                    db.add(msg)
                    db.commit()
            return True
        with db_session() as db:
            msg = db.get(TelegramMessage, message.id)
            if msg:
                msg.status = "failed"
                msg.error_message = str(err)
                msg.updated_at = datetime.utcnow()
                db.add(msg)
                db.commit()
        return False


async def sync_tatyana_message(bot, request: PaymentRequest, title: str) -> None:
    if not should_notify_tatyana(request):
        return
    with db_session() as db:
        req = db.get(PaymentRequest, int(request.id))
        if req is None:
            return
        messages = active_messages(db, req.id, "tatyana_payment_card")
    edited = False
    for message in messages:
        edited = (await safe_edit(bot, message, request, title, is_admin=False, is_manager=False)) or edited
    if edited:
        return
    msg = await bot.send_message(chat_id=TATYANA_CHAT_ID, text=payment_text_from_request(request, title), parse_mode="HTML", reply_markup=None)
    with db_session() as db:
        save_message(db, request.id, TATYANA_CHAT_ID, msg.message_id, "tatyana_payment_card", None)
        db.commit()


async def publish_created_request_cards(bot, manager_chat_id: Any, request_id: int, title_for_manager: str = "🧾 Заявка создана") -> None:
    with db_session() as db:
        request = db.get(PaymentRequest, request_id)
        if request is None:
            return
        creator = db.get(User, request.created_by_user_id)
        manager_tg = manager_chat_id or (creator.telegram_id if creator else None)
    manager_msg = None
    if manager_tg:
        manager_msg = await bot.send_message(
            chat_id=int(manager_tg),
            text=payment_text_from_request(request, title_for_manager),
            parse_mode="HTML",
            reply_markup=manager_keyboard(request),
        )
    admin_msg = await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=payment_text_from_request(request, "🧾 Новая заявка на оплату"),
        parse_mode="HTML",
        reply_markup=admin_keyboard(request),
    )
    await sync_tatyana_message(bot, request, "🧾 Новая заявка по счету")
    with db_session() as db:
        req = db.get(PaymentRequest, request_id)
        if req is not None:
            save_message(db, req.id, ADMIN_CHAT_ID, admin_msg.message_id, "admin_payment_card", None)
            if manager_msg and manager_tg:
                save_message(db, req.id, manager_tg, manager_msg.message_id, "manager_payment_card", req.created_by_user_id)
            db.commit()
    remember_recently_published(request_id)


async def delete_admin_manager_cards(bot, request: PaymentRequest, extra_messages: Optional[List[tuple[Any, Any]]] = None) -> None:
    with db_session() as db:
        messages = active_messages(db, request.id)
        admin_manager_messages = [m for m in messages if m.message_type in {"admin_payment_card", "manager_payment_card"}]
    known_pairs = {(str(m.chat_id), str(m.message_id)) for m in admin_manager_messages}
    for message in admin_manager_messages:
        deleted = await safe_delete(bot, message)
        if deleted:
            with db_session() as db:
                msg = db.get(TelegramMessage, message.id)
                if msg:
                    msg.status = "deleted"
                    msg.deleted_at = msg.deleted_at or datetime.utcnow()
                    msg.error_message = None
                    msg.updated_at = datetime.utcnow()
                    db.add(msg)
                    db.commit()

    # Some cards are produced by ad-hoc views such as “Мои заявки” and may not
    # exist in telegram_messages yet. Also, if a card was sent by an earlier bot
    # build before message-id persistence worked, the clicked message still must
    # disappear after cancellation/rejection.
    for chat_id, message_id in extra_messages or []:
        if not chat_id or not message_id:
            continue
        pair = (str(chat_id), str(message_id))
        if pair in known_pairs:
            continue
        await safe_delete_raw(bot, chat_id, message_id)


async def sync_request_cards(
    bot,
    request: PaymentRequest,
    title: str = "🧾 Заявка обновлена",
    extra_messages: Optional[List[tuple[Any, Any]]] = None,
) -> None:
    if is_terminal_for_admin_manager(request):
        await delete_admin_manager_cards(bot, request, extra_messages=extra_messages)
        await sync_tatyana_message(bot, request, "🧾 Заявка по счету обновлена")
        return
    with db_session() as db:
        messages = active_messages(db, request.id)
    for message in messages:
        if message.message_type == "admin_payment_card":
            await safe_edit(bot, message, request, title, is_admin=True)
        elif message.message_type == "manager_payment_card":
            await safe_edit(bot, message, request, "🔔 Статус заявки обновлён", is_manager=True)
        elif message.message_type == "tatyana_payment_card":
            await safe_edit(bot, message, request, "🧾 Заявка по счету обновлена")
    await sync_tatyana_message(bot, request, "🧾 Заявка по счету обновлена")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return ConversationHandler.END
    cached = get_cached_bound_user(update.effective_user.id)
    if cached:
        await update.message.reply_text(f"✅ Аккаунт найден: {cached.get('name', 'менеджер')}\nГлавное меню:", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END
    user = ensure_manager_from_telegram(update.effective_user.id)
    if user:
        await update.message.reply_text(f"✅ Аккаунт найден: {user.name}\nГлавное меню:", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END
    await update.message.reply_text("Telegram пока не привязан к аккаунту менеджера.\nНажми «Привязать аккаунт» и введи телефон + PIN от сайта.", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


async def bind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text("Введи телефон как на сайте в формате +7 (___) ___-__-__:", reply_markup=ReplyKeyboardRemove())
    return BIND_PHONE


async def bind_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    digits = normalize_phone(update.message.text or "")
    if not digits:
        await update.message.reply_text("Телефон нужен в формате +7 (___) ___-__-__.\nНапример: +7 (701) 123-45-67")
        return BIND_PHONE
    context.user_data["bind_phone"] = digits
    await update.message.reply_text(f"Телефон: {format_phone(digits)}\nТеперь введи PIN от сайта:")
    return BIND_PIN


async def bind_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with db_session() as db:
            user = bind_user_by_phone_pin(db, update.effective_user, context.user_data.get("bind_phone"), update.message.text.strip())
        await update.message.reply_text(f"✅ Аккаунт привязан: {user.name}.\nГлавное меню:", reply_markup=MAIN_KEYBOARD)
    except Exception as err:
        await update.message.reply_text(f"Не получилось привязать аккаунт: {err}\n\nНажми «Привязать аккаунт» и попробуй ещё раз.", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


def reset_payment_flow_cleanup(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[FLOW_CLEANUP_KEY] = []


def track_message_id(context: ContextTypes.DEFAULT_TYPE, message_id: Any) -> None:
    if not message_id:
        return
    ids = context.user_data.setdefault(FLOW_CLEANUP_KEY, [])
    try:
        mid = int(message_id)
    except Exception:
        return
    if mid not in ids:
        ids.append(mid)


async def cleanup_flow_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: Any) -> None:
    ids = list(context.user_data.get(FLOW_CLEANUP_KEY, []) or [])
    context.user_data[FLOW_CLEANUP_KEY] = []
    for message_id in ids:
        try:
            await context.bot.delete_message(chat_id=int(chat_id), message_id=int(message_id))
        except Exception:
            pass


async def new_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return ConversationHandler.END
    reset_payment_flow_cleanup(context)
    track_message_id(context, update.message.message_id)
    user = ensure_manager_from_telegram(update.effective_user.id)
    if not user:
        await update.message.reply_text("Аккаунт Telegram ещё не привязан к сайту.\nНажми «Привязать аккаунт» и введи телефон + PIN от сайта.", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END
    try:
        msg = await update.message.reply_text("⏳ Загружаю мероприятия…")
        track_message_id(context, msg.message_id)
        flow = load_manager_flow(update.effective_user.id)
        months = flow.get("months", [])
        if not months:
            await msg.edit_text("У тебя пока нет мероприятий в базе.")
            await update.message.reply_text("Главное меню:", reply_markup=MAIN_KEYBOARD)
            return ConversationHandler.END
        context.user_data["months"] = months
        context.user_data["events_by_month"] = flow.get("eventsByMonth", {})
        await msg.edit_text("Выбери месяц мероприятия:", reply_markup=month_keyboard(months))
        return CHOOSE_MONTH
    except Exception as err:
        await update.message.reply_text(f"Не удалось загрузить мероприятия: {err}", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END


async def choose_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Открываю месяц…")
    if query.data == "back:months":
        months = context.user_data.get("months", [])
        await query.edit_message_text("Выбери месяц мероприятия:", reply_markup=month_keyboard(months))
        return CHOOSE_MONTH
    idx = int(query.data.replace("month:", ""))
    month = context.user_data.get("months", [])[idx]
    events = (context.user_data.get("events_by_month") or {}).get(month, [])
    context.user_data["events"] = events
    if not events:
        await query.edit_message_text("В этом месяце мероприятий нет.")
        return ConversationHandler.END
    await query.edit_message_text(f"Месяц: {month}\nВыбери мероприятие:", reply_markup=events_keyboard(events))
    return CHOOSE_EVENT


async def choose_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Загружаю позиции…")
    if query.data == "back:months":
        months = context.user_data.get("months", [])
        await query.edit_message_text("Выбери месяц мероприятия:", reply_markup=month_keyboard(months))
        return CHOOSE_MONTH
    idx = int(query.data.replace("event:", ""))
    event = context.user_data.get("events", [])[idx]
    context.user_data["selected_event"] = event
    await query.edit_message_text(f"{event.get('customerName')} · {event.get('eventName')}\nДата: {event.get('eventDate')}\n\n⏳ Загружаю позиции…")
    try:
        result = load_items_data(query.from_user.id, event.get("eventId"))
        context.user_data["items"] = result.get("overview", [])
        context.user_data["allow_extra"] = bool(result.get("allowExtraPosition"))
        await query.edit_message_text(
            f"{event.get('customerName')} · {event.get('eventName')}\nДата: {event.get('eventDate')}\n\nВыбери позицию для оплаты:",
            reply_markup=items_keyboard(context.user_data["items"], context.user_data["allow_extra"]),
        )
        return CHOOSE_ITEM
    except Exception as err:
        await query.edit_message_text(f"Не удалось загрузить позиции: {err}")
        return ConversationHandler.END


async def choose_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Открываю позицию…")
    if query.data == "back:events":
        await query.edit_message_text("Выбери мероприятие:", reply_markup=events_keyboard(context.user_data.get("events", [])))
        return CHOOSE_EVENT
    item_id = query.data.replace("item:", "")
    context.user_data["item_id"] = item_id
    if item_id == EXTRA_ITEM_ID:
        await query.edit_message_text("Введи название новой позиции-допрасхода:")
        return EXTRA_POSITION_NAME
    item = next((x for x in context.user_data.get("items", []) if str(x.get("itemId")) == item_id), None)
    context.user_data["selected_item"] = item or {}
    context.user_data.pop("new_position_name", None)
    is_salary = item_id == SALARY_ITEM_ID
    fixed_method = (item or {}).get("fixedPaymentMethod") if not is_salary else None
    fixed_hint = "\nСпособ оплаты уже закреплён за этой позицией." if fixed_method else ""
    await query.edit_message_text(
        f"Позиция: {item.get('positionName') if item else item_id}{fixed_hint}\n\nВыбери способ оплаты:",
        reply_markup=payment_method_keyboard(is_salary=is_salary, fixed_method=fixed_method),
    )
    return PAYMENT_METHOD


async def extra_position_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    track_message_id(context, update.message.message_id)
    if not name:
        msg = await update.message.reply_text("Название не должно быть пустым. Введи название новой позиции:")
        track_message_id(context, msg.message_id)
        return EXTRA_POSITION_NAME
    context.user_data["new_position_name"] = name
    msg = await update.message.reply_text("Выбери способ оплаты:", reply_markup=payment_method_keyboard())
    track_message_id(context, msg.message_id)
    return PAYMENT_METHOD


async def choose_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Выбран способ оплаты")
    method_label = query.data.replace("paymethod:", "")
    method = payment_method_code(method_label)

    selected_item = context.user_data.get("selected_item") or {}
    fixed_method = selected_item.get("fixedPaymentMethod")
    if fixed_method:
        if method != fixed_method:
            await query.answer("Способ оплаты уже закреплён за этой позицией.", show_alert=True)
            return PAYMENT_METHOD
        method_label = payment_method_label(fixed_method)
        method = fixed_method

    context.user_data["payment_method"] = method_label
    context.user_data.pop("bin_iin", None)
    context.user_data.pop("kgd_note", None)

    if method == "invoice":
        if fixed_method == "invoice" and selected_item.get("iinBin") and selected_item.get("iinBinLocked"):
            await query.edit_message_text("Способ оплаты По счету уже закреплён и БИН/ИИН проверен.\n\nВведи сумму заявки:")
            return AMOUNT
        await query.edit_message_text("Введи БИН/ИИН подрядчика. Ровно 12 цифр:")
        return BIN_IIN
    if method == "self_employed":
        await query.edit_message_text("Самозанятый: НДС 0, вычеты 10%.\n\nВведи сумму заявки:")
        return AMOUNT
    await query.edit_message_text("Введи сумму заявки:")
    return AMOUNT


async def get_bin_iin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_message_id(context, update.message.message_id)
    bin_iin = clean_bin_iin(update.message.text)
    if len(bin_iin) != 12:
        msg = await update.message.reply_text("БИН/ИИН должен состоять ровно из 12 цифр. Попробуй ещё раз:")
        track_message_id(context, msg.message_id)
        return BIN_IIN
    context.user_data["bin_iin"] = bin_iin
    msg = await update.message.reply_text("⏳ Проверю БИН/ИИН при отправке заявки. Теперь введи сумму заявки:")
    track_message_id(context, msg.message_id)
    return AMOUNT


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_message_id(context, update.message.message_id)
    amount = money_number(update.message.text)
    if not amount:
        msg = await update.message.reply_text("Сумма должна быть числом. Например: 250000 или 250 000")
        track_message_id(context, msg.message_id)
        return AMOUNT
    context.user_data["amount"] = amount
    method = payment_method_code(context.user_data.get("payment_method"))
    if method == "card":
        msg = await update.message.reply_text("Введи номер карты. Ровно 16 цифр, можно с пробелами:")
        track_message_id(context, msg.message_id)
        return CARD_NUMBER
    if method == "self_employed":
        surname = self_employed_surname_from_bot_item(context.user_data.get("selected_item") or {})
        if surname:
            context.user_data["comment"] = surname
            msg = await update.message.reply_text(f"Фамилия самозанятого уже указана: {surname}. Отправляю заявку…")
            track_message_id(context, msg.message_id)
            return await submit_payment_request_now(update, context)
        context.user_data["awaiting_self_employed_surname"] = True
        msg = await update.message.reply_text("Введи фамилию самозанятого:")
        track_message_id(context, msg.message_id)
        return COMMENT
    msg = await update.message.reply_text("Комментарий к заявке? Если комментария нет — напиши «-».")
    track_message_id(context, msg.message_id)
    return COMMENT


async def get_card_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_message_id(context, update.message.message_id)
    digits = clean_digits(update.message.text)
    if len(digits) != 16:
        msg = await update.message.reply_text("Номер карты должен содержать ровно 16 цифр. Попробуй ещё раз:")
        track_message_id(context, msg.message_id)
        return CARD_NUMBER
    context.user_data["card_number"] = digits
    msg = await update.message.reply_text("Комментарий к заявке? Если комментария нет — напиши «-».")
    track_message_id(context, msg.message_id)
    return COMMENT


async def get_comment_and_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_message_id(context, update.message.message_id)
    comment = (update.message.text or "").strip()
    if comment == "-":
        comment = ""

    method = payment_method_code(context.user_data.get("payment_method"))
    if method == "self_employed":
        existing_surname = self_employed_surname_from_bot_item(context.user_data.get("selected_item") or {})
        if not comment and existing_surname:
            comment = existing_surname
        if not comment_has_surname(comment):
            msg = await update.message.reply_text("Для Самозанятого нужна фамилия. Введи фамилию:")
            track_message_id(context, msg.message_id)
            return COMMENT

    context.user_data["comment"] = comment
    context.user_data.pop("awaiting_self_employed_surname", None)
    return await submit_payment_request_now(update, context)


async def submit_payment_request_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    progress_msg = await update.message.reply_text("⏳ Отправляю заявку…")
    track_message_id(context, progress_msg.message_id)
    event = context.user_data.get("selected_event", {})
    payload = {
        "event_id": event.get("eventId"),
        "item_id": context.user_data.get("item_id"),
        "amount": context.user_data.get("amount"),
        "payment_method": context.user_data.get("payment_method"),
        "card_number": context.user_data.get("card_number", ""),
        "comment": context.user_data.get("comment", ""),
        "new_position_name": context.user_data.get("new_position_name", ""),
        "bin_iin": context.user_data.get("bin_iin", ""),
    }
    try:
        request = await asyncio.to_thread(create_payment_request_from_bot, update.effective_user.id, payload)
        await progress_msg.edit_text("✅ Заявка создана")
        await publish_created_request_cards(context.bot, update.effective_user.id, request.id, "🧾 Заявка создана")
        await cleanup_flow_messages(context, update.effective_chat.id)
        await update.message.reply_text("Главное меню:", reply_markup=MAIN_KEYBOARD)
    except Exception as err:
        await progress_msg.edit_text("⚠️ Не удалось отправить заявку.")
        await update.message.reply_text(f"Не удалось отправить заявку: {err}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = ensure_manager_from_telegram(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала привяжи аккаунт кнопкой «Привязать аккаунт».")
        return
    progress_msg = await update.message.reply_text("⏳ Загружаю заявки…")
    try:
        with db_session() as db:
            reqs = db.execute(
                select(PaymentRequest)
                .where(PaymentRequest.created_by_user_id == user.id)
                .order_by(PaymentRequest.id.desc())
            ).scalars().all()
            active = [r for r in reqs if is_active_for_manager(r)][:10]
        if not active:
            await progress_msg.edit_text("Заявок пока нет.")
            await update.message.reply_text("Главное меню:", reply_markup=MAIN_KEYBOARD)
            return
        await progress_msg.edit_text(f"Найдено заявок: {len(active)}")
        for request in active:
            msg = await update.message.reply_html(payment_text_from_request(request), reply_markup=manager_keyboard(request))
            with db_session() as db:
                req = db.get(PaymentRequest, int(request.id))
                if req is not None:
                    save_message(db, req.id, update.effective_chat.id, msg.message_id, "manager_payment_card", req.created_by_user_id)
                    db.commit()
    except Exception as err:
        await progress_msg.edit_text("⚠️ Не удалось загрузить заявки.")
        await update.message.reply_text(f"Не удалось загрузить заявки: {err}")


def update_request_status_in_db(payment_id: int, action: str, actor: str) -> PaymentRequest:
    with db_session() as db:
        request = db.get(PaymentRequest, int(payment_id))
        if request is None:
            raise RuntimeError("Заявка не найдена")
        item = db.get(EventItem, request.event_item_id)
        event = db.get(Event, request.event_id)
        previous_status = request.status
        now = datetime.utcnow()
        if action == "paid":
            if request.status != "paid":
                request.status = "paid"
                request.paid_at = now
                if item is not None:
                    item.paid_amount = money(item.paid_amount) + money(request.amount_requested)
                    item.updated_at = now
                    db.add(item)
        elif action == "reject":
            request.status = "rejected"
            request.money_status = "cancelled"
            request.rejected_at = now
            if previous_status == "paid" and item is not None:
                item.paid_amount = max(Decimal("0.00"), money(item.paid_amount) - money(request.amount_requested))
                item.updated_at = now
                db.add(item)
        elif action == "cashin":
            # Индивидуальная кнопка Telegram «Деньги в кассе» относится только к этой заявке.
            # Она не должна помечать всё мероприятие и соседние заявки.
            # Массовая операция мероприятие -> все заявки выполняется только на сайте
            # через /events/{event_id}/cash-received.
            request.money_status = "cash_received"
            request.cash_received_at = now
        elif action == "cancel":
            if actor == "manager" and request.status == "paid":
                raise RuntimeError("Оплаченную заявку нельзя отменить менеджером")
            request.status = "rejected"
            request.money_status = "cancelled"
            request.rejected_at = now
        else:
            raise RuntimeError("Неизвестное действие")
        request.updated_at = now
        db.add(request)
        db.commit()
        db.refresh(request)
        return request


async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Обновляю статус…")
    if query.from_user.id != ADMIN_CHAT_ID:
        await query.answer("Эта кнопка только для админа.", show_alert=True)
        return
    _, action, payment_id = query.data.split(":", 2)
    try:
        await query.edit_message_reply_markup(reply_markup=None)
        request = await asyncio.to_thread(update_request_status_in_db, int(payment_id), action, "admin")
        await sync_request_cards(
            context.bot,
            request,
            "🧾 Заявка обновлена",
            extra_messages=[(query.message.chat_id, query.message.message_id)] if query.message else None,
        )
        await query.answer("Готово")
    except Exception as err:
        await query.answer(str(err), show_alert=True)


async def handle_manager_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Отменяю заявку…")
    _, action, payment_id = query.data.split(":", 2)
    if action != "cancel":
        return
    try:
        request = await asyncio.to_thread(update_request_status_in_db, int(payment_id), "cancel", "manager")
        await sync_request_cards(
            context.bot,
            request,
            "🧾 Заявка обновлена",
            extra_messages=[(query.message.chat_id, query.message.message_id)] if query.message else None,
        )
        await context.bot.send_message(chat_id=query.from_user.id, text="Заявка отменена.", reply_markup=MAIN_KEYBOARD)
    except Exception as err:
        try:
            await query.edit_message_text(f"Не удалось отменить заявку: {err}")
        except Exception:
            await query.answer(str(err), show_alert=True)


async def poll_site_requests(context: ContextTypes.DEFAULT_TYPE):
    with db_session() as db:
        subq = select(TelegramMessage.id).where(
            TelegramMessage.payment_request_id == PaymentRequest.id,
            TelegramMessage.message_type == "admin_payment_card",
            TelegramMessage.status == "active",
        ).exists()
        query = select(PaymentRequest).where(
            not_(subq),
            PaymentRequest.status.in_(["new", "to_pay", "tax_check_needed"]),
        )
        if not TELEGRAM_PUBLISH_EXISTING_REQUESTS_ON_START:
            query = query.where(PaymentRequest.created_at >= BOT_STARTED_AT)
        requests = db.execute(
            query.order_by(PaymentRequest.id.desc()).limit(POLL_BATCH_LIMIT)
        ).scalars().all()
        request_ids = [r.id for r in requests if not is_recently_published(r.id)]
    for request_id in request_ids:
        with db_session() as db:
            request = db.get(PaymentRequest, request_id)
            creator = db.get(User, request.created_by_user_id) if request else None
        if request is None:
            continue
        try:
            await publish_created_request_cards(context.bot, creator.telegram_id if creator else None, request.id, "🧾 Заявка создана на сайте")
        except Exception as err:
            print(f"poll_site_requests publish failed for {request_id}: {err}")


async def poll_status_updates(context: ContextTypes.DEFAULT_TYPE):
    with db_session() as db:
        messages = db.execute(
            select(TelegramMessage)
            .where(TelegramMessage.status == "active", TelegramMessage.payment_request_id.is_not(None))
            .order_by(TelegramMessage.updated_at.asc())
            .limit(POLL_BATCH_LIMIT * 3)
        ).scalars().all()
        request_ids = sorted({int(m.payment_request_id) for m in messages if m.payment_request_id})
        requests = [db.get(PaymentRequest, rid) for rid in request_ids]
    for request in requests:
        if request is None:
            continue
        try:
            await sync_request_cards(context.bot, request, "🧾 Заявка обновлена")
        except Exception as err:
            print(f"poll_status_updates failed for {request.id}: {err}")


async def bot_background_loop(application, worker, name: str, first: int, interval: int):
    await asyncio.sleep(max(0, first))
    while True:
        try:
            await worker(type("Context", (), {"bot": application.bot})())
        except Exception as err:
            print(f"{name} background error: {err}")
        await asyncio.sleep(max(5, interval))


async def post_init(application):
    application.create_task(bot_background_loop(application, poll_site_requests, "poll_site_requests", 10, POLL_SECONDS))
    application.create_task(bot_background_loop(application, poll_status_updates, "poll_status_updates", 15, POLL_SECONDS))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        track_message_id(context, update.message.message_id)
        await cleanup_flow_messages(context, update.effective_chat.id)
        await update.message.reply_text("Действие отменено.", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(f"BOT VERSION: {BOT_VERSION}\nSITE VERSION: {get_settings().VERSION}\nTATYANA_ENABLED: {TATYANA_ENABLED}")


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = ensure_manager_from_telegram(update.effective_user.id)
    if user:
        await update.message.reply_text(
            "WHOAMI ✅\n"
            f"BOT VERSION: {BOT_VERSION}\n"
            f"telegramId: {update.effective_user.id}\n"
            f"username: @{update.effective_user.username or ''}\n"
            f"manager: {user.name}\n"
            f"userId: {user.id}\n"
            f"department_id: {user.department_id}\n"
            f"role: {user.role}"
        )
    else:
        await update.message.reply_text(
            "WHOAMI ⚠️ USER NOT FOUND\n"
            f"BOT VERSION: {BOT_VERSION}\n"
            f"telegramId: {update.effective_user.id}\n"
            f"username: @{update.effective_user.username or ''}"
        )


def main():
    require_env()
    print("BOT VERSION:", BOT_VERSION)
    print("BOT STARTED AT:", BOT_STARTED_AT.isoformat())
    print("PUBLISH EXISTING REQUESTS ON START:", TELEGRAM_PUBLISH_EXISTING_REQUESTS_ON_START)
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    bind_conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.Regex("^(Привязать аккаунт|Зарегистрировать пользователя)$"), bind_start)],
        states={
            BIND_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_phone)],
            BIND_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_pin)],
        },
        fallbacks=[CommandHandler("start", start), CommandHandler("cancel", cancel), MessageHandler(filters.Regex("^Отменить$"), cancel)],
    )

    request_conversation = ConversationHandler(
        entry_points=[CommandHandler("new", new_request), MessageHandler(filters.Regex("^Новая заявка$"), new_request)],
        states={
            CHOOSE_MONTH: [CallbackQueryHandler(choose_month, pattern="^(month:|back:months)")],
            CHOOSE_EVENT: [CallbackQueryHandler(choose_event, pattern="^(event:|back:months)")],
            CHOOSE_ITEM: [CallbackQueryHandler(choose_item, pattern="^(item:|back:events)")],
            EXTRA_POSITION_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_position_name)],
            PAYMENT_METHOD: [CallbackQueryHandler(choose_payment_method, pattern="^paymethod:")],
            BIN_IIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bin_iin)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            CARD_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_card_number)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment_and_submit)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^Отменить$"), cancel),
            MessageHandler(filters.Regex("^(Привязать аккаунт|Зарегистрировать пользователя)$"), bind_start),
        ],
    )

    app.add_handler(CommandHandler("version", version))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(bind_conversation)
    app.add_handler(request_conversation)
    app.add_handler(MessageHandler(filters.Regex("^Мои заявки$"), my_requests))
    app.add_handler(MessageHandler(filters.Regex("^Отменить$"), cancel))
    app.add_handler(CallbackQueryHandler(handle_admin_action, pattern="^admin:"))
    app.add_handler(CallbackQueryHandler(handle_manager_action, pattern="^manager:"))
    app.add_handler(CommandHandler("cancel", cancel))

    app.run_polling()


if __name__ == "__main__":
    main()
