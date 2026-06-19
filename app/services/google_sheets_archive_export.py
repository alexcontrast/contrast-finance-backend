from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from time import perf_counter
import logging

from fastapi import HTTPException
from sqlalchemy import extract, select
from sqlalchemy.orm import Session, selectinload

from app.models.event import Event
from app.models.event_item import EventItem
from app.models.monthly_expense import MonthlyExpense
from app.models.monthly_plan import MonthlyPlan
from app.models.payment_request import PaymentRequest
from app.models.user import User
from app.services.event_calculator import calculate_event_summary_values, money, q0

logger = logging.getLogger("contrast.performance")
ASTANA_TZ = ZoneInfo("Asia/Almaty")

MONTH_NAMES_RU = {
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

PAYMENT_METHOD_LABELS = {
    "invoice": "По счету",
    "card": "На карту",
    "cash": "Налик",
    "self_employed": "Самозанятый",
}

REQUEST_STATUS_LABELS = {
    "new": "Новая",
    "to_pay": "На оплату",
    "paid": "Оплачено",
    "rejected": "Отменено",
    "cancelled": "Отменено",
    "tax_check_needed": "Проверить КГД",
}

MONEY_STATUS_LABELS = {
    "waiting_money": "Ждём денег",
    "cash_received": "Деньги в кассе",
    "cancelled": "Отменено",
}

EVENT_STATUS_LABELS = {
    "draft": "Черновик",
    "review": "На проверке",
    "accepted": "Принято",
    "revision": "На доработке",
    "completed": "Завершено",
    "cancelled": "Отменено",
}

CLIENT_CALC_TYPE_LABELS = {
    "ip_contrast_event": "ИП Contrast Event",
    "our_no_vat": "ОУР без НДС",
    "simplified": "Упрощенка",
    "cash": "Нал",
}


def parse_month(month: str) -> date:
    try:
        parts = [int(part) for part in str(month).split("-")[:2]]
        return date(parts[0], parts[1], 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM") from exc


def decimal_to_int(value) -> int:
    return int(q0(money(value)))


def decimal_to_float(value) -> float:
    return float(money(value))


def iso_date(value: date | datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat()[:10]


def astana_datetime(value: datetime | None) -> str:
    if not value:
        return ""
    dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ASTANA_TZ).strftime("%d-%m-%Y %H:%M")


def month_title(month_date: date) -> str:
    return f"{MONTH_NAMES_RU.get(month_date.month, month_date.strftime('%B'))} {month_date.year}"


def sheet_safe_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def build_monthly_tax_totals(events_payload: list[dict]) -> dict:
    turnover = sum(row["summary"]["turnover"] for row in events_payload)
    vat_to_pay = sum(row["summary"]["vat_to_pay"] for row in events_payload)
    tax_to_pay = sum(row["summary"]["tax_to_pay"] for row in events_payload)
    return {
        "turnover": int(turnover),
        "vat_to_pay": int(vat_to_pay),
        "tax_to_pay": int(tax_to_pay),
    }


def build_export_payload(db: Session, month: str, current_admin: User) -> dict:
    started = perf_counter()
    month_date = parse_month(month)
    year = month_date.year
    month_num = month_date.month

    plan = db.execute(select(MonthlyPlan).where(MonthlyPlan.month == month_date)).scalar_one_or_none()
    expenses = db.execute(
        select(MonthlyExpense).where(
            extract("year", MonthlyExpense.month) == year,
            extract("month", MonthlyExpense.month) == month_num,
        )
    ).scalars().all()

    events = db.execute(
        select(Event)
        .where(extract("year", Event.event_date) == year)
        .where(extract("month", Event.event_date) == month_num)
        .options(
            selectinload(Event.manager),
            selectinload(Event.department),
            selectinload(Event.items),
            selectinload(Event.payment_requests).selectinload(PaymentRequest.created_by_user),
            selectinload(Event.payment_requests).selectinload(PaymentRequest.event_item),
            selectinload(Event.shares),
        )
        .order_by(Event.event_date.asc(), Event.id.asc())
    ).scalars().all()

    all_requests: list[PaymentRequest] = []
    events_payload: list[dict] = []

    for event in events:
        items = sorted(
            [item for item in list(event.items or []) if not item.is_deleted and item.item_type != "manager_salary"],
            key=lambda item: (item.sort_order or 0, item.id or 0),
        )
        summary_raw = calculate_event_summary_values(event, [item for item in list(event.items or []) if not item.is_deleted])
        summary = {
            "turnover": decimal_to_int(summary_raw.get("turnover_with_vat")),
            "external_total": decimal_to_int(summary_raw.get("external_total")),
            "fact_total": decimal_to_int(summary_raw.get("fact_total")),
            "paid_total": decimal_to_int(summary_raw.get("paid_total")),
            "vat_to_pay": decimal_to_int(summary_raw.get("vat_to_pay")),
            "client_vat": decimal_to_int(summary_raw.get("client_vat_amount")),
            "contractor_vat_credit": decimal_to_int(summary_raw.get("contractor_vat_credit")),
            "tax_to_pay": decimal_to_int(summary_raw.get("taxes_net")),
            "deductions_total": decimal_to_int(summary_raw.get("deductions_total")),
            "manager_salary": decimal_to_int(summary_raw.get("manager_salary")),
            "final_company_income": decimal_to_int(summary_raw.get("final_company_income")),
        }

        event_requests = list(event.payment_requests or [])
        all_requests.extend(event_requests)

        events_payload.append({
            "id": event.id,
            "date": iso_date(event.event_date),
            "created_at": astana_datetime(event.created_at),
            "manager": event.manager.name if event.manager else "",
            "department": event.department.name if event.department else "",
            "client": event.client_name,
            "title": event.title,
            "status": EVENT_STATUS_LABELS.get(event.status, event.status),
            "money_status": MONEY_STATUS_LABELS.get(event.money_status, event.money_status),
            "client_calc_type": CLIENT_CALC_TYPE_LABELS.get(event.client_calc_type, event.client_calc_type),
            "customer_paid": decimal_to_int(event.customer_paid_amount),
            "summary": summary,
            "items": [
                {
                    "name": item.external_name,
                    "external_amount": decimal_to_int(item.external_amount),
                    "fact_amount": decimal_to_int(item.amount_fact if item.amount_fact is not None else item.external_amount),
                    "paid_amount": decimal_to_int(item.paid_amount),
                    "vat_amount": decimal_to_int(item.vat_amount),
                    "deduction_amount": decimal_to_int(item.deduction_amount),
                    "payment_method": PAYMENT_METHOD_LABELS.get(item.payment_method, item.payment_method or ""),
                    "iin_bin": item.iin_bin or "",
                    "note": item.external_note or item.internal_note or "",
                }
                for item in items
            ],
        })

    requests_rows = []
    for request in sorted(all_requests, key=lambda item: (item.created_at or datetime.min), reverse=True):
        event = request.event
        item = request.event_item
        manager_name = request.created_by_user.name if request.created_by_user else (event.manager.name if event and event.manager else "")
        requests_rows.append({
            "event_date": iso_date(event.event_date if event else None),
            "created_at": astana_datetime(request.created_at),
            "manager": manager_name,
            "client": sheet_safe_text(event.client_name if event else ""),
            "event": sheet_safe_text(event.title if event else ""),
            "position": sheet_safe_text(request.item_name_snapshot or (item.external_name if item else "")),
            "amount": decimal_to_int(request.amount_requested),
            "payment_method": PAYMENT_METHOD_LABELS.get(request.payment_method, request.payment_method),
            "payment_status": REQUEST_STATUS_LABELS.get(request.status, request.status),
            "money_status": MONEY_STATUS_LABELS.get(request.money_status, request.money_status),
            "comment": sheet_safe_text(request.comment),
        })

    monthly_totals = build_monthly_tax_totals(events_payload)
    monthly_totals["plan"] = decimal_to_int(plan.company_plan_amount) if plan else 0
    monthly_totals["events_count"] = len(events_payload)
    monthly_totals["expenses"] = sum(decimal_to_int(expense.amount) for expense in expenses)

    payload = {
        "schema_version": "contrast_google_archive_v0.5.1",
        "generated_at": datetime.now(ASTANA_TZ).isoformat(),
        "requested_by": {"id": current_admin.id, "name": current_admin.name},
        "month": f"{year}-{month_num:02d}",
        "month_title": month_title(month_date),
        "sheets": {
            "monthly": {
                "sheet_name": month_title(month_date),
                "summary": monthly_totals,
                "events": events_payload,
            },
            "payment_requests": {
                "sheet_name": "Заявки на оплату",
                "rows": requests_rows,
            },
        },
    }
    logger.info(
        "PERF google-archive-payload month=%s events=%s requests=%s total=%.3fs",
        payload["month"], len(events_payload), len(requests_rows), perf_counter() - started,
    )
    return payload


def post_to_apps_script(payload: dict) -> dict:
    webhook_url = os.getenv("GOOGLE_SHEETS_EXPORT_WEBHOOK_URL") or os.getenv("GOOGLE_ARCHIVE_EXPORT_WEBHOOK_URL")
    token = os.getenv("GOOGLE_SHEETS_EXPORT_TOKEN") or os.getenv("GOOGLE_ARCHIVE_EXPORT_TOKEN")
    archive_url = os.getenv("GOOGLE_SHEETS_ARCHIVE_URL") or os.getenv("GOOGLE_ARCHIVE_SHEET_URL")

    if not webhook_url:
        raise HTTPException(
            status_code=400,
            detail=(
                "GOOGLE_SHEETS_EXPORT_WEBHOOK_URL is not configured. "
                "Deploy tools/google_sheets_export_webapp.gs as Apps Script Web App and put its URL into Railway secrets."
            ),
        )

    body = dict(payload)
    if token:
        body["token"] = token

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    started = perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            raw = response.read().decode("utf-8")
            result = json.loads(raw) if raw else {"ok": True}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=502, detail=f"Google export webhook failed: HTTP {exc.code}: {text}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google export webhook failed: {exc}") from exc

    logger.info(
        "PERF google-archive-webhook month=%s total=%.3fs ok=%s",
        payload.get("month"), perf_counter() - started, result.get("ok"),
    )
    return {
        "ok": bool(result.get("ok", True)),
        "message": result.get("message") or "Выгрузка в Google Sheets завершена",
        "google_sheet_url": result.get("spreadsheet_url") or archive_url,
        "updated_sheets": result.get("updated_sheets") or [],
    }
