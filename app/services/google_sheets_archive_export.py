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
ARCHIVE_TZ = ZoneInfo("Asia/Qyzylorda")
ASTANA_TZ = ARCHIVE_TZ

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


def parse_year(year: int | str) -> int:
    try:
        parsed = int(year)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="year must be YYYY") from exc
    if parsed < 2000 or parsed > 2100:
        raise HTTPException(status_code=400, detail="year must be between 2000 and 2100")
    return parsed


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


def month_short_title(month_date: date) -> str:
    return MONTH_NAMES_RU.get(month_date.month, month_date.strftime("%B"))


def sheet_safe_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def requested_by_payload(current_admin: User | None) -> dict:
    if current_admin is None:
        return {"id": None, "name": "Автоэкспорт 00:00"}
    return {"id": current_admin.id, "name": current_admin.name}


def positive_int(value) -> int:
    return max(0, decimal_to_int(value))


def allocated_decimal(value: Decimal, percent: Decimal) -> Decimal:
    return money(value) * money(percent) / Decimal("100")


def user_department_name(user: User | None) -> str | None:
    if user is None or user.department is None:
        return None
    return user.department.name


def event_primary_department_name(event: Event, user_by_id: dict[int, User]) -> str:
    manager = user_by_id.get(event.manager_id) if event.manager_id else None
    return user_department_name(manager) or (event.department.name if event.department else "Без отдела")


def add_event_income_to_departments(
    department_income: dict[str, Decimal],
    event: Event,
    event_income: Decimal,
    user_by_id: dict[int, User],
) -> None:
    shares = list(event.shares or [])
    if not shares:
        department_name = event_primary_department_name(event, user_by_id)
        department_income[department_name] = department_income.get(department_name, Decimal("0.00")) + event_income
        return

    for share in shares:
        manager = user_by_id.get(share.user_id)
        department_name = user_department_name(manager)
        if not department_name:
            continue
        amount = allocated_decimal(event_income, money(share.share_percent))
        department_income[department_name] = department_income.get(department_name, Decimal("0.00")) + amount


def department_plan_amount(plan: MonthlyPlan | None, department_name: str) -> Decimal:
    if plan is None:
        return Decimal("0.00")
    if department_name == "Санжар":
        return q0(money(plan.company_plan_amount) * money(plan.sanzhar_share_percent) / Decimal("100"))
    if department_name == "Рауфаль":
        return q0(money(plan.company_plan_amount) * money(plan.raufal_share_percent) / Decimal("100"))
    return Decimal("0.00")


def split_monthly_expenses(expenses: list[MonthlyExpense], plan: MonthlyPlan | None) -> dict[str, Decimal]:
    sanzhar_percent = money(plan.sanzhar_share_percent) if plan is not None else Decimal("66.67")
    by_department = {"Санжар": Decimal("0.00"), "Рауфаль": Decimal("0.00")}

    for expense in expenses:
        amount = money(expense.amount)
        if expense.allocation_type == "default_split":
            sanzhar_amount = q0(amount * sanzhar_percent / Decimal("100"))
            raufal_amount = q0(amount - sanzhar_amount)
        else:
            sanzhar_amount = money(expense.sanzhar_amount)
            raufal_amount = money(expense.raufal_amount)

        by_department["Санжар"] += sanzhar_amount
        by_department["Рауфаль"] += raufal_amount

    return by_department


def department_head_percent(income: Decimal, plan_amount: Decimal) -> Decimal:
    return Decimal("15.00") if plan_amount > 0 and income >= plan_amount else Decimal("10.00")


def department_head_salary(income: Decimal, expenses: Decimal, percent: Decimal) -> Decimal:
    base = money(income) - money(expenses)
    if base <= 0:
        return Decimal("0.00")
    return q0(base * money(percent) / Decimal("100"))


def build_monthly_tax_totals(events_payload: list[dict]) -> dict:
    turnover = sum((money(row["summary"].get("turnover", 0)) for row in events_payload), Decimal("0.00"))
    client_vat = sum((money(row["summary"].get("client_vat", 0)) for row in events_payload), Decimal("0.00"))
    contractor_vat_credit = sum((money(row["summary"].get("contractor_vat_credit", 0)) for row in events_payload), Decimal("0.00"))
    contrast_event_tax_total = sum(
        (
            money(row["summary"].get("taxes_total", 0))
            for row in events_payload
            if row.get("client_calc_type_code") == "ip_contrast_event"
        ),
        Decimal("0.00"),
    )
    deductions_total = sum((money(row["summary"].get("deductions_total", 0)) for row in events_payload), Decimal("0.00"))
    company_income = sum((money(row["summary"].get("final_company_income", 0)) for row in events_payload), Decimal("0.00"))

    # Сводки показывают реальные суммы к уплате за месяц:
    # - НДС к уплате = клиентский НДС - все НДС-зачёты по подрядчикам за месяц.
    # - Налоги к уплате = налог только по ИП Contrast Event - все налоговые вычеты за месяц.
    #   Расходы по налогам ОУР без НДС и Упрощенки здесь не показываем как налог к уплате.
    vat_to_pay = q0(client_vat - contractor_vat_credit)
    tax_to_pay = q0(contrast_event_tax_total - deductions_total)

    return {
        "turnover": decimal_to_int(turnover),
        "client_vat": decimal_to_int(client_vat),
        "contractor_vat_credit": decimal_to_int(contractor_vat_credit),
        "vat_to_pay": positive_int(vat_to_pay),
        "contrast_event_tax_total": decimal_to_int(contrast_event_tax_total),
        "deductions_total": decimal_to_int(deductions_total),
        "tax_to_pay": positive_int(tax_to_pay),
        "company_income": decimal_to_int(company_income),
    }


def build_request_row(request: PaymentRequest) -> dict:
    event = request.event
    item = request.event_item
    manager_name = request.created_by_user.name if request.created_by_user else (event.manager.name if event and event.manager else "")
    return {
        "_sort_key": (request.created_at or datetime.min).isoformat(),
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
    }


def strip_sort_keys(rows: list[dict]) -> list[dict]:
    stripped = []
    for row in rows:
        copy = dict(row)
        copy.pop("_sort_key", None)
        stripped.append(copy)
    return stripped


def build_month_export_sections(db: Session, month_date: date) -> dict:
    started = perf_counter()
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
        .where(Event.status != "cancelled")
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
    manager_income: dict[str, int] = {}
    manager_salary: dict[str, int] = {}
    department_income_dec: dict[str, Decimal] = {}

    users = db.execute(select(User).options(selectinload(User.department))).scalars().all()
    user_by_id = {user.id: user for user in users}

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
            "taxes_total": decimal_to_int(summary_raw.get("taxes_total")),
            "deductions_total": decimal_to_int(summary_raw.get("deductions_total")),
            "manager_salary": decimal_to_int(summary_raw.get("manager_salary")),
            "manager_percent": decimal_to_float(summary_raw.get("manager_percent")),
            "final_company_income": decimal_to_int(summary_raw.get("final_company_income")),
        }

        manager_name = event.manager.name if event.manager else "Без менеджера"
        manager_income[manager_name] = manager_income.get(manager_name, 0) + summary["final_company_income"]
        manager_salary[manager_name] = manager_salary.get(manager_name, 0) + summary["manager_salary"]
        add_event_income_to_departments(department_income_dec, event, money(summary["final_company_income"]), user_by_id)

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
            "client_calc_type_code": event.client_calc_type,
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

    requests_rows = [build_request_row(request) for request in all_requests]
    requests_rows.sort(key=lambda row: row.get("_sort_key") or "", reverse=True)

    monthly_totals = build_monthly_tax_totals(events_payload)
    monthly_totals["plan"] = decimal_to_int(plan.company_plan_amount) if plan else 0
    monthly_totals["manager_personal_plan"] = (
        decimal_to_int(money(plan.company_plan_amount) * money(plan.manager_personal_plan_percent) / Decimal("100"))
        if plan
        else 0
    )
    monthly_totals["events_count"] = len(events_payload)

    base_expenses = sum((money(expense.amount) for expense in expenses), Decimal("0.00"))
    department_expenses = split_monthly_expenses(expenses, plan)
    department_income = {name: decimal_to_int(amount) for name, amount in sorted(department_income_dec.items())}
    department_plans = {
        "Санжар": decimal_to_int(department_plan_amount(plan, "Санжар")),
        "Рауфаль": decimal_to_int(department_plan_amount(plan, "Рауфаль")),
    }

    sanzhar_income = department_income_dec.get("Санжар", Decimal("0.00"))
    raufal_income = department_income_dec.get("Рауфаль", Decimal("0.00"))
    sanzhar_head_salary = department_head_salary(
        sanzhar_income,
        department_expenses.get("Санжар", Decimal("0.00")),
        department_head_percent(sanzhar_income, department_plan_amount(plan, "Санжар")),
    )
    raufal_head_salary = department_head_salary(
        raufal_income,
        department_expenses.get("Рауфаль", Decimal("0.00")),
        department_head_percent(raufal_income, department_plan_amount(plan, "Рауфаль")),
    )
    department_heads_salary = q0(sanzhar_head_salary + raufal_head_salary)
    expenses_with_heads = q0(base_expenses + department_heads_salary)

    monthly_totals["base_expenses"] = decimal_to_int(base_expenses)
    monthly_totals["department_heads_salary"] = decimal_to_int(department_heads_salary)
    monthly_totals["expenses"] = decimal_to_int(expenses_with_heads)
    monthly_totals["clean_income"] = monthly_totals["company_income"] - monthly_totals["expenses"]
    monthly_totals["income_after_expenses"] = monthly_totals["clean_income"]
    monthly_totals["remaining"] = monthly_totals["plan"] - monthly_totals["company_income"]

    logger.info(
        "PERF google-archive-month-sections month=%s events=%s requests=%s total=%.3fs",
        f"{year}-{month_num:02d}", len(events_payload), len(requests_rows), perf_counter() - started,
    )

    return {
        "month": f"{year}-{month_num:02d}",
        "month_date": month_date,
        "monthly": {
            "sheet_name": month_title(month_date),
            "summary": monthly_totals,
            "events": events_payload,
        },
        "payment_request_rows": requests_rows,
        "annual_month": {
            "month": f"{year}-{month_num:02d}",
            "title": month_short_title(month_date),
            **monthly_totals,
        },
        "manager_income": manager_income,
        "manager_salary": manager_salary,
        "department_income": department_income,
        "department_plans": department_plans,
    }


def build_annual_stats_sheet(year: int, month_sections: list[dict]) -> dict:
    months = [section["annual_month"] for section in month_sections]
    month_keys = [row["month"] for row in months]

    totals = {
        "plan": sum(row.get("plan", 0) for row in months),
        "events_count": sum(row.get("events_count", 0) for row in months),
        "turnover": sum(row.get("turnover", 0) for row in months),
        "vat_to_pay": sum(row.get("vat_to_pay", 0) for row in months),
        "tax_to_pay": sum(row.get("tax_to_pay", 0) for row in months),
        "company_income": sum(row.get("company_income", 0) for row in months),
        "base_expenses": sum(row.get("base_expenses", 0) for row in months),
        "department_heads_salary": sum(row.get("department_heads_salary", 0) for row in months),
        "expenses": sum(row.get("expenses", 0) for row in months),
        "clean_income": sum(row.get("clean_income", row.get("income_after_expenses", 0)) for row in months),
        "income_after_expenses": sum(row.get("clean_income", row.get("income_after_expenses", 0)) for row in months),
    }
    totals["remaining"] = totals["plan"] - totals["company_income"]

    department_names: set[str] = {"Санжар", "Рауфаль"}
    for section in month_sections:
        department_names.update(section.get("department_income", {}).keys())
        department_names.update(section.get("department_plans", {}).keys())

    department_rows = []
    for department_name in sorted(department_names):
        income_by_month = {}
        plan_by_month = {}
        for key, section in zip(month_keys, month_sections):
            income_by_month[key] = int(section.get("department_income", {}).get(department_name, 0))
            plan_by_month[key] = int(section.get("department_plans", {}).get(department_name, 0))
        department_rows.append({
            "department": department_name,
            "income_by_month": income_by_month,
            "plan_by_month": plan_by_month,
            "income_total": sum(income_by_month.values()),
            "plan_total": sum(plan_by_month.values()),
        })

    manager_names: set[str] = set()
    for section in month_sections:
        manager_names.update(section.get("manager_income", {}).keys())
        manager_names.update(section.get("manager_salary", {}).keys())

    manager_rows = []
    for manager_name in sorted(manager_names):
        income_by_month = {}
        salary_by_month = {}
        plan_by_month = {}
        for key, section in zip(month_keys, month_sections):
            annual_month = section.get("annual_month", {})
            income_by_month[key] = int(section.get("manager_income", {}).get(manager_name, 0))
            salary_by_month[key] = int(section.get("manager_salary", {}).get(manager_name, 0))
            plan_by_month[key] = int(annual_month.get("manager_personal_plan", 0))
        manager_rows.append({
            "manager": manager_name,
            "income_by_month": income_by_month,
            "salary_by_month": salary_by_month,
            "plan_by_month": plan_by_month,
            "income_total": sum(income_by_month.values()),
            "salary_total": sum(salary_by_month.values()),
            "plan_total": sum(plan_by_month.values()),
        })

    return {
        "sheet_name": "Годовая статистика",
        "year": year,
        "months": months,
        "totals": totals,
        "department_rows": department_rows,
        "manager_rows": manager_rows,
    }


def build_export_payload(db: Session, month: str, current_admin: User | None) -> dict:
    started = perf_counter()
    month_date = parse_month(month)
    sections = build_month_export_sections(db, month_date)

    payload = {
        "schema_version": "contrast_google_archive_v0.6.2",
        "export_type": "month",
        "generated_at": datetime.now(ASTANA_TZ).isoformat(),
        "requested_by": requested_by_payload(current_admin),
        "month": sections["month"],
        "month_title": month_title(month_date),
        "sheets": {
            "monthly": sections["monthly"],
            "payment_requests": {
                "sheet_name": "Заявки на оплату",
                "rows": strip_sort_keys(sections["payment_request_rows"]),
            },
        },
    }
    logger.info(
        "PERF google-archive-payload month=%s events=%s requests=%s total=%.3fs",
        payload["month"],
        len(sections["monthly"].get("events") or []),
        len(sections["payment_request_rows"]),
        perf_counter() - started,
    )
    return payload


def build_year_export_payload(db: Session, year: int | str, current_admin: User | None = None) -> dict:
    started = perf_counter()
    parsed_year = parse_year(year)
    month_sections = [build_month_export_sections(db, date(parsed_year, month_num, 1)) for month_num in range(1, 13)]

    request_rows: list[dict] = []
    for section in month_sections:
        request_rows.extend(section["payment_request_rows"])
    request_rows.sort(key=lambda row: row.get("_sort_key") or "", reverse=True)

    annual_stats = build_annual_stats_sheet(parsed_year, month_sections)
    monthly_sheets = [section["monthly"] for section in month_sections]
    events_count = sum(len(sheet.get("events") or []) for sheet in monthly_sheets)

    payload = {
        "schema_version": "contrast_google_archive_v0.6.2",
        "export_type": "year",
        "generated_at": datetime.now(ASTANA_TZ).isoformat(),
        "requested_by": requested_by_payload(current_admin),
        "year": parsed_year,
        "sheets": {
            "months": monthly_sheets,
            "payment_requests": {
                "sheet_name": "Заявки на оплату",
                "rows": strip_sort_keys(request_rows),
            },
            "annual_stats": annual_stats,
        },
    }
    logger.info(
        "PERF google-archive-year-payload year=%s months=%s events=%s requests=%s total=%.3fs",
        parsed_year, len(monthly_sheets), events_count, len(request_rows), perf_counter() - started,
    )
    return payload


def payload_updated_sheet_names(payload: dict) -> list[str]:
    sheets = payload.get("sheets") or {}
    names: list[str] = []
    if sheets.get("monthly"):
        names.append((sheets["monthly"] or {}).get("sheet_name") or "Месяц")
    if sheets.get("months"):
        names.extend([(sheet or {}).get("sheet_name") or "Месяц" for sheet in sheets.get("months") or []])
    if sheets.get("payment_requests"):
        names.append((sheets["payment_requests"] or {}).get("sheet_name") or "Заявки на оплату")
    if sheets.get("annual_stats"):
        names.append((sheets["annual_stats"] or {}).get("sheet_name") or "Годовая статистика")
    return names


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
    export_key = payload.get("month") or payload.get("year") or payload.get("export_type") or "archive"
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            raw = response.read().decode("utf-8")
            result = json.loads(raw) if raw else {"ok": True}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=502, detail=f"Google export webhook failed: HTTP {exc.code}: {text}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google export webhook failed: {exc}") from exc

    logger.info(
        "PERF google-archive-webhook export=%s total=%.3fs ok=%s",
        export_key, perf_counter() - started, result.get("ok"),
    )
    return {
        "ok": bool(result.get("ok", True)),
        "message": result.get("message") or "Выгрузка в Google Sheets завершена",
        "google_sheet_url": result.get("spreadsheet_url") or archive_url,
        "updated_sheets": result.get("updated_sheets") or payload_updated_sheet_names(payload),
    }
