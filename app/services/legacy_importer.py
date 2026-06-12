from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contractor import Contractor
from app.models.department import Department
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.event_share import EventShare
from app.models.monthly_plan import MonthlyPlan
from app.models.payment_request import PaymentRequest
from app.models.telegram_message import TelegramMessage
from app.models.user import User


@dataclass
class ImportStats:
    dry_run: bool = True
    users_created: int = 0
    users_updated: int = 0
    departments_created: int = 0
    plans_created: int = 0
    plans_updated: int = 0
    events_created: int = 0
    events_updated: int = 0
    event_items_created: int = 0
    event_items_updated: int = 0
    event_shares_created: int = 0
    payment_requests_created: int = 0
    payment_requests_updated: int = 0
    telegram_messages_created: int = 0
    contractors_created: int = 0
    contractors_updated: int = 0
    skipped_payments_without_event: int = 0
    skipped_payments_without_item: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__


MONTHS_RU = {
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,
}


def sheet_rows(data: dict[str, Any], name: str) -> list[dict[str, Any]]:
    return list(((data.get("sheets") or {}).get(name) or {}).get("rows") or [])


def cell_value(value: Any) -> Any:
    if isinstance(value, dict) and value.get("type") == "date":
        return value.get("value") or value.get("display") or ""
    return value


def text(value: Any) -> str:
    value = cell_value(value)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Да" if value else ""
    return str(value).strip()


def money(value: Any) -> Decimal:
    value = cell_value(value)
    if value is None or value == "":
        return Decimal("0.00")
    if isinstance(value, bool):
        return Decimal("0.00")
    try:
        return Decimal(str(value).replace(" ", "").replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def number(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    result = money(value)
    return result if result is not None else default


def parse_dt(value: Any) -> datetime | None:
    raw = cell_value(value)
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw.replace(tzinfo=None)
    if isinstance(raw, date):
        return datetime(raw.year, raw.month, raw.day)
    s = str(raw).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=None)
    except Exception:
        return None


def parse_date(value: Any) -> date | None:
    dt = parse_dt(value)
    if dt:
        # Apps Script export uses UTC but source dates are Asia/Almaty; for date-only fields
        # this still gives the intended calendar date in exported values.
        return dt.date()
    s = text(value)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def event_id_date(legacy_event_id: str) -> datetime | None:
    match = re.search(r"EVT-(\d{8})-(\d{6})", legacy_event_id or "")
    if not match:
        return None
    try:
        return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
    except Exception:
        return None


def payment_id_date(legacy_payment_id: str) -> datetime | None:
    match = re.search(r"PAY-(\d{8})-(\d{6})", legacy_payment_id or "")
    if not match:
        return None
    try:
        return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
    except Exception:
        return None


def month_start_from_legacy(value: Any) -> date | None:
    s = text(value)
    parts = s.split()
    if len(parts) < 2:
        return None
    month = MONTHS_RU.get(parts[0].lower())
    try:
        year = int(parts[1])
    except Exception:
        return None
    if not month:
        return None
    return date(year, month, 1)


def role_map(value: Any) -> str:
    v = text(value).lower()
    if "админ" in v:
        return "admin"
    if "глав" in v or "руковод" in v:
        return "department_head"
    if "бух" in v:
        return "accountant"
    return "manager"


def event_status_map(value: Any) -> str:
    v = text(value).lower()
    if "провер" in v:
        return "review"
    if "доработ" in v:
        return "revision"
    if "прин" in v:
        return "accepted"
    if "заверш" in v or "архив" in v:
        return "completed"
    if "отмен" in v or "отклон" in v:
        return "cancelled"
    return "draft"


def client_type_map(value: Any) -> str:
    v = text(value).lower()
    if "оур" in v and "без" in v:
        return "our_no_vat"
    if "упрощ" in v:
        return "simplified"
    if v == "нал" or "нал" == v:
        return "cash"
    return "ip_contrast_event"


def payment_method_map(value: Any) -> str | None:
    v = text(value).lower()
    if not v:
        return None
    if "самоз" in v:
        return "self_employed"
    if "счет" in v or "счёт" in v:
        return "invoice"
    if "карт" in v:
        return "card"
    if "нал" in v:
        return "cash"
    return None


def payment_status_map(row: dict[str, Any]) -> str:
    # Legacy UI had two practical buckets for open requests:
    # "Новая" and "На оплату" both mean "active / awaiting admin action".
    # Legacy "Отклонено" and "Отменено" are also the same business state
    # for the new system during migration: cancelled.
    source = text(row.get("Статус оплаты")) or text(row.get("Статус"))
    v = source.lower()
    if "оплач" in v or "деньги" in v:
        return "paid"
    if "отмен" in v or "отклон" in v:
        return "cancelled"
    if "на оплат" in v or "нов" in v:
        return "new"
    return "new"


def money_status_map(row: dict[str, Any], payment_status: str) -> str:
    source = text(row.get("Статус денег")) or text(row.get("Статус"))
    v = source.lower().replace("ё", "е")
    if "деньги в кассе" in v:
        return "cash_received"
    if payment_status in {"rejected", "cancelled"}:
        return "cancelled"
    return "waiting_money"


def tax_status_map(value: Any) -> str | None:
    v = text(value).lower()
    if not v:
        return None
    if "самоз" in v:
        return "self_employed"
    if "ндс" in v and ("без" not in v and "не" not in v):
        return "our_vat"
    if "без ндс" in v:
        return "our_no_vat"
    if "упрощ" in v:
        return "simplified"
    if "снр" in v:
        return "snr"
    if "не найден" in v or "не провер" in v:
        return "not_found"
    return text(value)


def vat_status_map(value: Any) -> str | None:
    v = text(value).lower()
    if not v:
        return None
    if "платель" in v or "с ндс" in v or v in {"да", "true"}:
        return "vat_payer"
    if "без" in v or "не" in v or v in {"нет", "false"}:
        return "no_vat"
    return text(value)


def boolish(value: Any) -> bool:
    v = text(value).lower()
    return v in {"true", "1", "да", "yes", "y"}


def get_or_create_department(db: Session, name: str, stats: ImportStats) -> Department:
    dep_name = name or "Санжар"
    dep = db.execute(select(Department).where(Department.name == dep_name)).scalar_one_or_none()
    if dep is None:
        dep = Department(name=dep_name, is_active=True)
        db.add(dep)
        db.flush()
        stats.departments_created += 1
    return dep


def get_or_create_user(db: Session, row: dict[str, Any], stats: ImportStats) -> User:
    legacy_user_id = text(row.get("User ID"))
    user = None
    if legacy_user_id:
        user = db.execute(select(User).where(User.legacy_user_id == legacy_user_id)).scalar_one_or_none()
    if user is None:
        name = text(row.get("Имя")) or "Без имени"
        phone = text(row.get("Телефон")) or None
        user = db.execute(select(User).where(User.name == name, User.phone == phone)).scalar_one_or_none()

    dep = get_or_create_department(db, text(row.get("Отдел")) or "Санжар", stats)
    is_new = user is None
    if is_new:
        user = User(name=text(row.get("Имя")) or "Без имени")
        stats.users_created += 1
    else:
        stats.users_updated += 1

    user.legacy_user_id = legacy_user_id or user.legacy_user_id
    user.legacy_pin_hash = text(row.get("PIN Hash")) or user.legacy_pin_hash
    user.pin_hash = user.pin_hash or None
    user.department_id = dep.id
    user.name = text(row.get("Имя")) or user.name
    user.phone = text(row.get("Телефон")) or user.phone
    user.telegram_id = text(row.get("Telegram ID")) or user.telegram_id
    user.telegram_username = text(row.get("Telegram Username")) or user.telegram_username
    user.role = role_map(row.get("Роль"))
    user.is_active = text(row.get("Статус")).lower() != "удален"
    user.auth_source = "legacy_apps_script"
    user.created_at = parse_dt(row.get("Дата регистрации")) or user.created_at or datetime.utcnow()
    user.updated_at = parse_dt(row.get("Обновлен")) or datetime.utcnow()
    db.add(user)
    db.flush()
    return user


def upsert_monthly_plans(db: Session, data: dict[str, Any], stats: ImportStats):
    for row in sheet_rows(data, "Цели"):
        month = month_start_from_legacy(row.get("Месяц"))
        if not month:
            continue
        plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month)).scalar_one_or_none()
        is_new = plan is None
        if is_new:
            plan = MonthlyPlan(month=month, company_plan_amount=money(row.get("Цель")))
            stats.plans_created += 1
        else:
            plan.company_plan_amount = money(row.get("Цель"))
            stats.plans_updated += 1
        plan.sanzhar_share_percent = Decimal("66.67")
        plan.raufal_share_percent = Decimal("33.33")
        plan.manager_personal_plan_percent = Decimal("12.50")
        db.add(plan)


def item_key(event_legacy_id: str, order: Any, fallback_index: int) -> str:
    order_text = text(order) or str(fallback_index)
    return f"{event_legacy_id}|{order_text}"


def build_user_maps(db: Session) -> tuple[dict[str, User], dict[str, User]]:
    users = db.execute(select(User)).scalars().all()
    by_legacy = {u.legacy_user_id: u for u in users if u.legacy_user_id}
    by_name = {u.name.lower(): u for u in users if u.name}
    return by_legacy, by_name


def event_closed_by_customer_money(data: dict[str, Any]) -> set[str]:
    closed = set()
    for row in sheet_rows(data, "Оплаты_заказчиков"):
        if text(row.get("Закрыто 100%")):
            eid = text(row.get("Event ID"))
            if eid:
                closed.add(eid)
    return closed


def event_cash_by_requests(data: dict[str, Any]) -> set[str]:
    active_by_event: dict[str, list[str]] = {}
    for row in sheet_rows(data, "Заявки_на_оплату"):
        eid = text(row.get("Event ID"))
        if not eid:
            continue
        st = payment_status_map(row)
        if st in {"rejected", "cancelled"}:
            continue
        active_by_event.setdefault(eid, []).append(money_status_map(row, st))
    return {eid for eid, statuses in active_by_event.items() if statuses and all(s == "cash_received" for s in statuses)}


def upsert_events(db: Session, data: dict[str, Any], stats: ImportStats) -> dict[str, Event]:
    by_legacy_user, by_name_user = build_user_maps(db)
    closed_events = event_closed_by_customer_money(data) | event_cash_by_requests(data)
    result: dict[str, Event] = {}
    for row in sheet_rows(data, "Черновики_ивентов"):
        legacy_event_id = text(row.get("Event ID"))
        if not legacy_event_id:
            continue
        user = by_legacy_user.get(text(row.get("User ID"))) or by_name_user.get(text(row.get("Менеджер")).lower())
        if user is None:
            # Create a minimal user if the event references a manager missing from Users.
            dep = get_or_create_department(db, text(row.get("Отдел")) or "Санжар", stats)
            user = User(
                legacy_user_id=text(row.get("User ID")) or None,
                name=text(row.get("Менеджер")) or "Без имени",
                department_id=dep.id,
                role="manager",
                is_active=True,
                auth_source="legacy_apps_script",
            )
            db.add(user)
            db.flush()
            by_legacy_user[user.legacy_user_id] = user
            by_name_user[user.name.lower()] = user
            stats.users_created += 1
        dep = get_or_create_department(db, text(row.get("Отдел")) or (user.department.name if user.department else "Санжар"), stats)
        event = db.execute(select(Event).where(Event.legacy_event_id == legacy_event_id)).scalar_one_or_none()
        is_new = event is None
        if is_new:
            event = Event(legacy_event_id=legacy_event_id)
            stats.events_created += 1
        else:
            stats.events_updated += 1
        event.client_name = text(row.get("Название заказчика")) or "—"
        event.title = text(row.get("Название мероприятия")) or event.client_name or "Мероприятие"
        event.event_date = parse_date(row.get("Дата мероприятия")) or date.today()
        event.department_id = dep.id
        event.manager_id = user.id
        event.status = event_status_map(row.get("Статус"))
        event.money_status = "cash_received" if legacy_event_id in closed_events else "waiting_money"
        event.client_calc_type = client_type_map(row.get("Тип расчета"))
        event.manager_percent = Decimal("21.00")
        event.agency_commission_amount = money(row.get("Агентская %"))
        event.agency_commission_spread_enabled = "false"
        event.simplified_bank_tax_percent = money(row.get("Налог %")) if event.client_calc_type == "simplified" else None
        event.created_at = parse_dt(row.get("Создан")) or parse_dt(row.get("Дата создания")) or event_id_date(legacy_event_id) or datetime.utcnow()
        event.updated_at = parse_dt(row.get("Обновлен")) or datetime.utcnow()
        db.add(event)
        db.flush()
        result[legacy_event_id] = event
    return result


def upsert_shares(db: Session, data: dict[str, Any], event_map: dict[str, Event], stats: ImportStats):
    by_legacy_user, by_name_user = build_user_maps(db)
    # Clear shares for imported legacy events; they are fully reconstructed from export.
    event_ids = [event.id for event in event_map.values()]
    if event_ids:
        for share in db.execute(select(EventShare).where(EventShare.event_id.in_(event_ids))).scalars().all():
            db.delete(share)
        db.flush()
    for row in sheet_rows(data, "Черновики_ивентов"):
        legacy_event_id = text(row.get("Event ID"))
        event = event_map.get(legacy_event_id)
        if not event:
            continue
        co_user_id = text(row.get("Соавтор User ID"))
        co_name = text(row.get("Соавтор"))
        main_percent = money(row.get("Доля основного менеджера"))
        co_percent = money(row.get("Доля соавтора"))
        if not co_user_id and not co_name:
            continue
        main_user = db.get(User, event.manager_id)
        co_user = by_legacy_user.get(co_user_id) or by_name_user.get(co_name.lower())
        if main_user and main_percent > 0:
            db.add(EventShare(event_id=event.id, user_id=main_user.id, share_percent=main_percent))
            stats.event_shares_created += 1
        if co_user and co_percent > 0:
            db.add(EventShare(event_id=event.id, user_id=co_user.id, share_percent=co_percent))
            stats.event_shares_created += 1


def upsert_items(db: Session, data: dict[str, Any], event_map: dict[str, Event], stats: ImportStats) -> dict[str, EventItem]:
    result: dict[str, EventItem] = {}
    grouped_index: dict[str, int] = {}
    for row in sheet_rows(data, "Позиции_ивентов"):
        legacy_event_id = text(row.get("Event ID"))
        event = event_map.get(legacy_event_id)
        if not event:
            continue
        grouped_index[legacy_event_id] = grouped_index.get(legacy_event_id, 0) + 1
        key = item_key(legacy_event_id, row.get("№"), grouped_index[legacy_event_id])
        item = db.execute(select(EventItem).where(EventItem.legacy_item_key == key)).scalar_one_or_none()
        is_new = item is None
        if is_new:
            item = EventItem(legacy_item_key=key, event_id=event.id)
            stats.event_items_created += 1
        else:
            stats.event_items_updated += 1
        order_num = int(money(row.get("№")) or grouped_index[legacy_event_id])
        position = text(row.get("Позиция")) or "Позиция"
        is_coord = boolish(row.get("Координатор")) or order_num == 1 or position.lower() == "координатор"
        is_salary = "зп" in position.lower() and "менедж" in position.lower()
        item.item_type = "manager_salary" if is_salary else ("coordinator" if is_coord else "regular")
        item.external_name = position
        item.external_price = money(row.get("Смета"))
        item.external_quantity = Decimal("1.00")
        item.external_days = Decimal("1.00")
        item.external_amount = money(row.get("Смета"))
        item.external_note = text(row.get("Примечание")) or None
        item.amount_fact = money(row.get("Факт"))
        item.paid_amount = money(row.get("Оплачено"))
        item.payment_method = payment_method_map(row.get("Способ оплаты")) or ("cash" if is_coord else None)
        item.iin_bin = re.sub(r"\D", "", text(row.get("БИН/ИИН"))) or None
        item.iin_bin_locked = bool(item.iin_bin)
        item.tax_check_status = tax_status_map(row.get("Режим") or row.get("Налоговый режим"))
        item.vat_amount = money(row.get("НДС"))
        item.deduction_amount = money(row.get("Вычеты"))
        contractor_name = text(row.get("Название подрядчика")) or text(row.get("Контрагент"))
        note = text(row.get("Примечание"))
        item.internal_note = note or (f"Подрядчик: {contractor_name}" if contractor_name else None)
        item.sort_order = order_num
        item.is_deleted = False
        item.updated_at = datetime.utcnow()
        db.add(item)
        db.flush()
        result[key] = item
    return result


def ensure_item_for_payment(db: Session, row: dict[str, Any], event: Event, stats: ImportStats) -> EventItem:
    legacy_event_id = text(row.get("Event ID"))
    order_raw = row.get("№ позиции")
    key = item_key(legacy_event_id, order_raw, 0)
    item = db.execute(select(EventItem).where(EventItem.legacy_item_key == key)).scalar_one_or_none()
    if item:
        return item
    position = text(row.get("Позиция")) or "Доппозиция"
    order_num = int(money(order_raw) or 900000)
    item = EventItem(
        legacy_item_key=key,
        event_id=event.id,
        item_type="manager_salary" if ("зп" in position.lower() and "менедж" in position.lower()) else ("coordinator" if position.lower() == "координатор" else "regular"),
        external_name=position,
        external_price=money(row.get("Сумма по смете")),
        external_quantity=Decimal("1.00"),
        external_days=Decimal("1.00"),
        external_amount=money(row.get("Сумма по смете")),
        external_note=None,
        amount_fact=money(row.get("Сумма по смете")) if money(row.get("Сумма по смете")) > 0 else money(row.get("Сумма заявки")),
        paid_amount=Decimal("0.00"),
        payment_method=payment_method_map(row.get("Способ оплаты заявки")),
        iin_bin=re.sub(r"\D", "", text(row.get("БИН/ИИН"))) or None,
        iin_bin_locked=bool(text(row.get("БИН/ИИН"))),
        tax_check_status=tax_status_map(row.get("КГД режим")),
        vat_amount=Decimal("0.00"),
        deduction_amount=Decimal("0.00"),
        internal_note=None,
        sort_order=order_num,
        is_deleted=False,
    )
    db.add(item)
    db.flush()
    stats.event_items_created += 1
    return item


def upsert_contractor_from_payment(db: Session, row: dict[str, Any], stats: ImportStats) -> Contractor | None:
    iin_bin = re.sub(r"\D", "", text(row.get("БИН/ИИН")))
    if not iin_bin:
        return None
    contractor = db.execute(select(Contractor).where(Contractor.iin_bin == iin_bin)).scalar_one_or_none()
    is_new = contractor is None
    if is_new:
        contractor = Contractor(iin_bin=iin_bin)
        stats.contractors_created += 1
    else:
        stats.contractors_updated += 1
    contractor.name = text(row.get("КГД название")) or text(row.get("Подрядчик")) or contractor.name
    contractor.tax_status = tax_status_map(row.get("КГД режим")) or contractor.tax_status
    contractor.vat_status = vat_status_map(row.get("КГД НДС статус")) or contractor.vat_status
    contractor.source = "legacy_import"
    contractor.last_checked_at = parse_dt(row.get("КГД проверено дата")) or contractor.last_checked_at
    contractor.is_active = True
    db.add(contractor)
    db.flush()
    return contractor


def upsert_payment_requests(db: Session, data: dict[str, Any], event_map: dict[str, Event], stats: ImportStats):
    for row in sheet_rows(data, "Заявки_на_оплату"):
        legacy_payment_id = text(row.get("Payment ID"))
        legacy_event_id = text(row.get("Event ID"))
        if not legacy_payment_id:
            continue
        event = event_map.get(legacy_event_id) or db.execute(select(Event).where(Event.legacy_event_id == legacy_event_id)).scalar_one_or_none()
        if not event:
            stats.skipped_payments_without_event += 1
            continue
        item = ensure_item_for_payment(db, row, event, stats)
        if not item:
            stats.skipped_payments_without_item += 1
            continue
        user = db.execute(select(User).where(User.legacy_user_id == text(row.get("User ID")))).scalar_one_or_none() or db.get(User, event.manager_id)
        payment = db.execute(select(PaymentRequest).where(PaymentRequest.legacy_payment_id == legacy_payment_id)).scalar_one_or_none()
        is_new = payment is None
        if is_new:
            payment = PaymentRequest(legacy_payment_id=legacy_payment_id, event_id=event.id, event_item_id=item.id, created_by_user_id=user.id)
            stats.payment_requests_created += 1
        else:
            stats.payment_requests_updated += 1
        method = payment_method_map(row.get("Способ оплаты заявки")) or item.payment_method or "cash"
        status = payment_status_map(row)
        money_status = money_status_map(row, status)
        contractor = upsert_contractor_from_payment(db, row, stats) if method == "invoice" else None
        payment.event_id = event.id
        payment.event_item_id = item.id
        payment.created_by_user_id = user.id
        payment.amount_requested = money(row.get("Сумма заявки"))
        payment.payment_method = method
        payment.status = status
        payment.money_status = money_status
        payment.comment = text(row.get("Комментарий менеджера")) or None
        payment.item_name_snapshot = text(row.get("Позиция")) or item.external_name
        payment.item_amount_plan_snapshot = money(row.get("Сумма по смете"))
        payment.item_amount_fact_snapshot = item.amount_fact
        payment.item_paid_amount_snapshot = money(row.get("Уже оплачено на момент заявки"))
        payment.item_remaining_snapshot = money(row.get("Остаток на момент заявки"))
        payment.contractor_id = contractor.id if contractor else None
        payment.contractor_name_snapshot = text(row.get("КГД название")) or text(row.get("Подрядчик")) or None
        payment.iin_bin_snapshot = re.sub(r"\D", "", text(row.get("БИН/ИИН"))) or None
        payment.tax_status_snapshot = tax_status_map(row.get("КГД режим"))
        payment.vat_status_snapshot = vat_status_map(row.get("КГД НДС статус"))
        payment.vat_amount_snapshot = Decimal("0.00")
        payment.deduction_amount_snapshot = Decimal("0.00")
        payment.tax_source_snapshot = "legacy_import" if (payment.tax_status_snapshot or payment.iin_bin_snapshot) else None
        payment.card_number = text(row.get("Номер карты")) or None
        payment.warning_over_remaining = payment.amount_requested > payment.item_remaining_snapshot and payment.item_remaining_snapshot >= 0
        payment.created_at = parse_dt(row.get("Дата заявки")) or payment_id_date(legacy_payment_id) or datetime.utcnow()
        payment.updated_at = parse_dt(row.get("Обновлен")) or datetime.utcnow()
        payment.paid_at = parse_dt(row.get("Дата статуса оплаты")) or (parse_dt(row.get("Дата решения")) if status == "paid" else None)
        payment.cash_received_at = parse_dt(row.get("Дата статуса денег")) if money_status == "cash_received" else None
        payment.rejected_at = parse_dt(row.get("Дата решения")) if status in {"rejected", "cancelled"} else None
        db.add(payment)
        db.flush()
        upsert_legacy_telegram_messages(db, payment, row, user, stats)


def upsert_legacy_telegram_messages(db: Session, payment: PaymentRequest, row: dict[str, Any], user: User, stats: ImportStats):
    message_specs = [
        ("Telegram Admin Message ID", "admin_payment_card", None),
        ("Telegram Manager Message ID", "manager_payment_card", user.id),
        ("Telegram Tatyana Message ID", "tatyana_payment_card", None),
    ]
    for col, message_type, recipient_user_id in message_specs:
        msg_id = text(row.get(col))
        if not msg_id:
            continue
        exists = db.execute(
            select(TelegramMessage).where(
                TelegramMessage.payment_request_id == payment.id,
                TelegramMessage.message_type == message_type,
                TelegramMessage.message_id == msg_id,
            )
        ).scalar_one_or_none()
        if exists:
            continue
        db.add(
            TelegramMessage(
                payment_request_id=payment.id,
                chat_id="legacy_unknown",
                message_id=msg_id,
                message_type=message_type,
                recipient_user_id=recipient_user_id,
                status="deleted" if payment.status in {"paid", "rejected", "cancelled"} and payment.money_status in {"cash_received", "cancelled"} else "legacy",
                created_at=parse_dt(row.get("Telegram Notified At")) or payment.created_at,
                updated_at=parse_dt(row.get("Telegram Status Synced At")) or payment.updated_at,
            )
        )
        stats.telegram_messages_created += 1



def validate_legacy_data(data: dict[str, Any]) -> dict[str, Any]:
    """Fast validation for browser dry-run.

    It intentionally does not touch PostgreSQL: Railway can return an upstream
    timeout when the dry run executes the whole import transaction and then
    rolls it back. This validation only reads the JSON structure, counts rows,
    checks required sheets/columns, and previews the mapped volume.
    """
    sheets = data.get("sheets") or {}
    required = {
        "Пользователи": ["User ID", "Имя", "Отдел"],
        "Черновики_ивентов": ["Event ID", "User ID", "Менеджер", "Дата мероприятия"],
        "Позиции_ивентов": ["Event ID", "№", "Позиция"],
        "Заявки_на_оплату": ["Payment ID", "Event ID", "Статус оплаты", "Статус денег"],
    }
    warnings: list[str] = []
    errors: list[str] = []
    sheet_counts: dict[str, int] = {}

    version = data.get("version")
    if version != "contrast_legacy_export_v1":
        warnings.append(f"Неожиданная версия экспорта: {version}")

    for name, columns in required.items():
        sheet = sheets.get(name) or {}
        rows = list(sheet.get("rows") or [])
        headers = set(sheet.get("headers") or [])
        sheet_counts[name] = len(rows)
        if name not in sheets:
            errors.append(f"Нет обязательного листа: {name}")
            continue
        for col in columns:
            if col not in headers:
                warnings.append(f"Лист {name}: нет колонки {col}")

    for name, sheet in sheets.items():
        sheet_counts[name] = len((sheet or {}).get("rows") or [])

    events = sheet_rows(data, "Черновики_ивентов")
    items = sheet_rows(data, "Позиции_ивентов")
    payments = sheet_rows(data, "Заявки_на_оплату")
    users = sheet_rows(data, "Пользователи")

    event_ids = {text(r.get("Event ID")) for r in events if text(r.get("Event ID"))}
    item_event_ids = {text(r.get("Event ID")) for r in items if text(r.get("Event ID"))}
    payment_event_ids = {text(r.get("Event ID")) for r in payments if text(r.get("Event ID"))}

    missing_item_events = sorted(list(item_event_ids - event_ids))[:20]
    missing_payment_events = sorted(list(payment_event_ids - event_ids))[:20]
    if missing_item_events:
        warnings.append(f"Есть позиции без мероприятия: {len(item_event_ids - event_ids)}. Примеры: {', '.join(missing_item_events)}")
    if missing_payment_events:
        warnings.append(f"Есть заявки без мероприятия: {len(payment_event_ids - event_ids)}. Примеры: {', '.join(missing_payment_events)}")

    status_counts: dict[str, int] = {}
    money_status_counts: dict[str, int] = {}
    for row in payments:
        st = payment_status_map(row)
        ms = money_status_map(row, st)
        status_counts[st] = status_counts.get(st, 0) + 1
        money_status_counts[ms] = money_status_counts.get(ms, 0) + 1

    return {
        "valid": not errors,
        "version": version,
        "exported_at": data.get("exportedAt"),
        "spreadsheet_name": data.get("spreadsheetName"),
        "timezone": data.get("timezone"),
        "sheets_count": len(sheets),
        "total_rows": sum(sheet_counts.values()),
        "sheet_counts": sheet_counts,
        "planned_import": {
            "users": len(users),
            "events": len(events),
            "event_items": len(items),
            "payment_requests": len(payments),
            "monthly_plans": len(sheet_rows(data, "Цели")),
            "customer_payments_archive_rows": len(sheet_rows(data, "Оплаты_заказчиков")),
        },
        "payment_status_counts": status_counts,
        "money_status_counts": money_status_counts,
        "errors": errors,
        "warnings": warnings[:80],
        "note": "Это быстрая сухая проверка структуры JSON без записи в PostgreSQL. Боевой импорт запускается отдельно.",
    }




def legacy_event_map_for_ids(db: Session, legacy_event_ids: set[str]) -> dict[str, Event]:
    ids = {str(x).strip() for x in legacy_event_ids if str(x or '').strip()}
    if not ids:
        return {}
    rows = db.execute(select(Event).where(Event.legacy_event_id.in_(ids))).scalars().all()
    return {event.legacy_event_id: event for event in rows if event.legacy_event_id}


def legacy_event_map_for_all(db: Session, data: dict[str, Any]) -> dict[str, Event]:
    ids = {text(row.get("Event ID")) for row in sheet_rows(data, "Черновики_ивентов") if text(row.get("Event ID"))}
    return legacy_event_map_for_ids(db, ids)


def data_with_sheet_rows(data: dict[str, Any], sheet_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a shallow legacy export clone with one sheet narrowed to a row slice.

    This lets the old full-sheet upsert helpers be reused safely in small
    Railway-friendly batches without changing their mapping logic.
    """
    copy = dict(data or {})
    sheets = dict((data or {}).get("sheets") or {})
    sheet = dict(sheets.get(sheet_name) or {})
    sheet["rows"] = list(rows or [])
    sheet["lastRow"] = len(rows or []) + 1 if rows else 1
    sheets[sheet_name] = sheet
    copy["sheets"] = sheets
    return copy


def import_legacy_data_step(
    db: Session,
    data: dict[str, Any],
    step: str,
    offset: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    """Run one small production import step and commit it.

    The browser calls this repeatedly. Each step is idempotent: existing legacy
    IDs are updated, not duplicated. This avoids Railway upstream timeout on one
    big HTTP request.
    """
    step = (step or "").strip().lower()
    offset = max(int(offset or 0), 0)
    limit = max(min(int(limit or 100), 500), 1)
    stats = ImportStats(dry_run=False)

    try:
        if step == "core":
            get_or_create_department(db, "Санжар", stats)
            get_or_create_department(db, "Рауфаль", stats)
            for row in sheet_rows(data, "Пользователи"):
                get_or_create_user(db, row, stats)
            upsert_monthly_plans(db, data, stats)
            db.commit()
            return {
                "step": step,
                "done": True,
                "next_offset": 0,
                "total": len(sheet_rows(data, "Пользователи")) + len(sheet_rows(data, "Цели")),
                "stats": stats.as_dict(),
            }

        if step == "events":
            rows_all = sheet_rows(data, "Черновики_ивентов")
            rows = rows_all[offset:offset + limit]
            scoped = data_with_sheet_rows(data, "Черновики_ивентов", rows)
            upsert_events(db, scoped, stats)
            db.commit()
            next_offset = offset + len(rows)
            return {
                "step": step,
                "done": next_offset >= len(rows_all),
                "next_offset": next_offset,
                "total": len(rows_all),
                "processed": len(rows),
                "stats": stats.as_dict(),
            }

        if step == "shares":
            event_map = legacy_event_map_for_all(db, data)
            upsert_shares(db, data, event_map, stats)
            db.commit()
            return {
                "step": step,
                "done": True,
                "next_offset": 0,
                "total": len(event_map),
                "stats": stats.as_dict(),
            }

        if step == "items":
            rows_all = sheet_rows(data, "Позиции_ивентов")
            rows = rows_all[offset:offset + limit]
            ids = {text(row.get("Event ID")) for row in rows if text(row.get("Event ID"))}
            event_map = legacy_event_map_for_ids(db, ids)
            scoped = data_with_sheet_rows(data, "Позиции_ивентов", rows)
            upsert_items(db, scoped, event_map, stats)
            db.commit()
            next_offset = offset + len(rows)
            return {
                "step": step,
                "done": next_offset >= len(rows_all),
                "next_offset": next_offset,
                "total": len(rows_all),
                "processed": len(rows),
                "stats": stats.as_dict(),
            }

        if step == "payments":
            rows_all = sheet_rows(data, "Заявки_на_оплату")
            rows = rows_all[offset:offset + limit]
            ids = {text(row.get("Event ID")) for row in rows if text(row.get("Event ID"))}
            event_map = legacy_event_map_for_ids(db, ids)
            scoped = data_with_sheet_rows(data, "Заявки_на_оплату", rows)
            upsert_payment_requests(db, scoped, event_map, stats)
            db.commit()
            next_offset = offset + len(rows)
            return {
                "step": step,
                "done": next_offset >= len(rows_all),
                "next_offset": next_offset,
                "total": len(rows_all),
                "processed": len(rows),
                "stats": stats.as_dict(),
            }

        if step == "final":
            result = validate_legacy_data(data)
            imported = {
                "users_with_legacy_id": db.execute(select(User).where(User.legacy_user_id.is_not(None))).scalars().all(),
                "events_with_legacy_id": db.execute(select(Event).where(Event.legacy_event_id.is_not(None))).scalars().all(),
                "items_with_legacy_key": db.execute(select(EventItem).where(EventItem.legacy_item_key.is_not(None))).scalars().all(),
                "payments_with_legacy_id": db.execute(select(PaymentRequest).where(PaymentRequest.legacy_payment_id.is_not(None))).scalars().all(),
            }
            return {
                "step": step,
                "done": True,
                "next_offset": 0,
                "validation": result,
                "imported_counts": {key: len(value) for key, value in imported.items()},
                "note": "Финальная проверка только читает базу и JSON. Запись не выполнялась.",
            }

        raise ValueError(f"Unknown legacy import step: {step}")
    except Exception:
        db.rollback()
        raise

def import_legacy_data(db: Session, data: dict[str, Any], dry_run: bool = True) -> dict[str, Any]:
    stats = ImportStats(dry_run=dry_run)
    if data.get("version") != "contrast_legacy_export_v1":
        stats.warnings.append(f"Неожиданная версия экспорта: {data.get('version')}")

    for name in ["Пользователи", "Черновики_ивентов", "Позиции_ивентов", "Заявки_на_оплату"]:
        if name not in (data.get("sheets") or {}):
            stats.warnings.append(f"В экспорте нет листа: {name}")

    try:
        get_or_create_department(db, "Санжар", stats)
        get_or_create_department(db, "Рауфаль", stats)
        for row in sheet_rows(data, "Пользователи"):
            get_or_create_user(db, row, stats)
        upsert_monthly_plans(db, data, stats)
        event_map = upsert_events(db, data, stats)
        upsert_shares(db, data, event_map, stats)
        upsert_items(db, data, event_map, stats)
        upsert_payment_requests(db, data, event_map, stats)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise

    return stats.as_dict()


def load_legacy_json_file(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
