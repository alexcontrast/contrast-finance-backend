from __future__ import annotations

from collections import defaultdict
from html import unescape
from io import BytesIO
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
import requests
from pypdf import PdfReader
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.r1_profile import R1_CUSTOMER_PROFILE
from app.models.event import Event
from app.models.payment_request import PaymentRequest
from app.models.self_employed_accounting import SelfEmployedAccounting
from app.models.self_employed_accounting_request import SelfEmployedAccountingRequest
from app.models.user import User
from app.schemas.self_employed_accounting import (
    SelfEmployedAccountingAttachCreate,
    SelfEmployedAccountingGroupCreate,
    SelfEmployedAccountingMemberRead,
    SelfEmployedAccountingRead,
    SelfEmployedAccountingUpdate,
    SelfEmployedReceiptImportRead,
    SelfEmployedReceiptQrResolveCreate,
    SelfEmployedReceiptQrResolveRead,
    R1CustomerProfileRead,
)
from app.services.auth import get_current_user


router = APIRouter(prefix="/accounting/self-employed", tags=["self_employed_accounting"])

MAX_RECEIPT_BYTES = 10 * 1024 * 1024
ALLOWED_RECEIPT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
}
INACTIVE_REQUEST_STATUSES = {"cancelled", "rejected"}

KGD_RECEIPT_HOST = "esb.kgd.gov.kz"
KGD_RECEIPT_PATH = "/taxpay-check-core/get-check-report"
KGD_RECEIPT_TIMEOUT = (5, 15)


def canonical_esalyq_qr(value: str | None) -> str | None:
    """Return a stable KGD receipt URL or reject unrelated QR payloads.

    We intentionally only allow the exact public e-Salyq receipt endpoint. This
    keeps the server-side fetch from becoming an SSRF primitive when QR content
    comes from an uploaded image.
    """
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https" or (parsed.hostname or "").lower() != KGD_RECEIPT_HOST:
        raise HTTPException(status_code=400, detail="QR не относится к официальному чеку e-Salyq Business")
    if parsed.path.rstrip("/") != KGD_RECEIPT_PATH:
        raise HTTPException(status_code=400, detail="QR содержит неизвестную ссылку e-Salyq")
    params = parse_qs(parsed.query, keep_blank_values=False)
    check_id = (params.get("check_id") or [None])[0]
    ip_reg_id = (params.get("ip_reg_id") or [None])[0]
    if not check_id or not ip_reg_id or not str(check_id).isdigit() or not str(ip_reg_id).isdigit():
        raise HTTPException(status_code=400, detail="В QR не найдены идентификаторы чека e-Salyq")
    query = urlencode({"check_id": str(check_id), "ip_reg_id": str(ip_reg_id)})
    return f"https://{KGD_RECEIPT_HOST}{KGD_RECEIPT_PATH}?{query}"


def _strip_html_to_text(source: str) -> str:
    source = re.sub(r"(?is)<(?:script|style)[^>]*>.*?</(?:script|style)>", " ", source or "")
    source = re.sub(r"(?i)<(?:br|/p|/div|/tr|/td|/li|/h[1-6])[^>]*>", "\n", source)
    source = re.sub(r"(?s)<[^>]+>", " ", source)
    source = unescape(source)
    source = source.replace("\xa0", " ").replace("\r", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in source.split("\n")]
    return "\n".join(line for line in lines if line)


_RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
    "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}


def _parse_report_datetime(text: str) -> datetime | None:
    lower = str(text or "").lower()
    match = re.search(
        r"(?:от\s*)?(\d{1,2})\s+([а-яё]+)\s+(20\d{2})(?:\s*г(?:ода)?[.,]?)?\s*[,\-]?\s*(\d{1,2}):(\d{2})",
        lower,
        re.I,
    )
    if match:
        month = _RU_MONTHS.get(match.group(2))
        if month:
            return datetime(int(match.group(3)), month, int(match.group(1)), int(match.group(4)), int(match.group(5)))
    match = re.search(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](20\d{2})[^\d]{0,10}(\d{1,2}):(\d{2})", lower)
    if match:
        return datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), int(match.group(4)), int(match.group(5)))
    return None


def _money_from_text(value: str | None) -> Decimal | None:
    if not value:
        return None
    raw = re.sub(r"[^0-9,.-]", "", str(value)).replace(",", ".")
    try:
        return Decimal(raw).quantize(Decimal("0.01")) if raw else None
    except InvalidOperation:
        return None


def _parse_esalyq_report_text(raw_text: str) -> dict:
    """Parse the official KGD report text, not pixels from the uploaded image."""
    text = str(raw_text or "").replace("\xa0", " ").replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    joined = "\n".join(lines)
    result: dict = {}

    receipt = re.search(r"(?:чек|receipt)\s*[№N#]?\s*([0-9]{4,24})", joined, re.I)
    if receipt:
        result["receipt_number"] = receipt.group(1)

    dt = _parse_report_datetime(joined)
    if dt:
        result["receipt_datetime"] = dt

    iin_matches = re.findall(r"(?:ИИН|IIN|ЖСН)[^0-9]{0,20}((?:\d[\s-]?){12})", joined, re.I)
    for candidate in iin_matches:
        digits = re.sub(r"\D", "", candidate)
        if len(digits) == 12 and digits != str(R1_CUSTOMER_PROFILE.get("bin_iin") or ""):
            result["iin"] = digits
            break

    total = re.search(r"(?:Итого|Total)[^0-9]{0,30}([0-9][0-9\s.,]{0,18})\s*(?:₸|тг|тенге|T\b)", joined, re.I)
    if total:
        amount = _money_from_text(total.group(1).replace(" ", ""))
        if amount is not None:
            result["receipt_amount"] = amount

    def looks_like_name(line: str) -> bool:
        clean = re.sub(r"\s+", " ", line or "").strip(" •·")
        if not clean or re.search(r"режим|налогооблож|самозанят|БИН|BIN|ИП\b|ТОО\b|чек|итого|плат[её]ж|наличн|безналичн|банк|Кбе|ИИК|HSBK|₸|тг", clean, re.I):
            return False
        words = clean.split()
        letters = len(re.findall(r"[A-Za-zА-Яа-яЁё]", clean))
        return 2 <= len(words) <= 5 and letters >= 8

    iin_line_index = next((i for i, line in enumerate(lines) if re.search(r"(?:ИИН|IIN|ЖСН)", line, re.I)), -1)
    if iin_line_index >= 0:
        indices = list(range(iin_line_index + 1, min(len(lines), iin_line_index + 5)))
        indices += list(range(iin_line_index - 1, max(-1, iin_line_index - 5), -1))
        for idx in indices:
            candidate = re.sub(r"^[^A-Za-zА-Яа-яЁё]+|[^A-Za-zА-Яа-яЁё .'-]+$", "", lines[idx]).strip()
            if looks_like_name(candidate):
                result["contractor_full_name"] = candidate
                break

    total_index = next((i for i, line in enumerate(lines) if re.search(r"^(?:итого|total)\b", line, re.I)), -1)
    payment_index = next((i for i, line in enumerate(lines) if re.search(r"безналичн|наличн|текущ(?:ий)?\s+плат[её]ж|способ\s+оплаты", line, re.I)), -1)
    if payment_index >= 0:
        end = total_index if total_index > payment_index else min(len(lines), payment_index + 8)
        candidates = lines[payment_index + 1:end]
    elif total_index > 0:
        candidates = lines[max(0, total_index - 6):total_index]
    else:
        candidates = []
    service_lines = []
    for line in candidates:
        line = re.sub(r"\s+[0-9][0-9\s.,]{0,18}\s*(?:₸|тг|тенге|T\b)\s*$", "", line, flags=re.I)
        line = re.sub(r"\s+", " ", line).strip()
        if re.search(r"(?:ИИН|IIN|ЖСН|БИН|BIN|чек|receipt|итого|режим\s+налогооблож|самозанят|ИП\b)", line, re.I):
            continue
        if len(re.findall(r"[A-Za-zА-Яа-яЁё]", line)) >= 3:
            service_lines.append(line)
    if service_lines:
        result["service_name"] = " ".join(service_lines).strip()

    return result


def _flatten_json(value, prefix: str = "") -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_json(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_flatten_json(child, f"{prefix}[{index}]"))
    else:
        rows.append((prefix.lower(), value))
    return rows


def _parse_esalyq_json(payload: object) -> dict:
    rows = _flatten_json(payload)
    result: dict = {}

    def first_value(key_fragments: tuple[str, ...], reject_fragments: tuple[str, ...] = ()):
        for path, value in rows:
            if value in {None, ""}:
                continue
            if all(fragment in path for fragment in key_fragments) and not any(fragment in path for fragment in reject_fragments):
                return value
        return None

    receipt_number = (
        first_value(("check", "number"))
        or first_value(("receipt", "number"))
        or first_value(("check", "num"))
    )
    if receipt_number is not None:
        digits = re.sub(r"\D", "", str(receipt_number))
        if digits:
            result["receipt_number"] = digits

    iin_candidates = []
    for path, value in rows:
        if "iin" not in path and "iinbin" not in path and "bin_iin" not in path:
            continue
        digits = re.sub(r"\D", "", str(value or ""))
        if len(digits) == 12 and digits != str(R1_CUSTOMER_PROFILE.get("bin_iin") or ""):
            priority = 0 if any(token in path for token in ("seller", "executor", "taxpayer", "individual", "person", "ip")) else 1
            iin_candidates.append((priority, digits))
    if iin_candidates:
        result["iin"] = sorted(iin_candidates, key=lambda item: item[0])[0][1]

    name = (
        first_value(("seller", "name"))
        or first_value(("executor", "name"))
        or first_value(("taxpayer", "name"))
        or first_value(("full", "name"), ("customer", "buyer"))
        or first_value(("fio",), ("customer", "buyer"))
    )
    if name:
        cleaned = clean_text(str(name), 255)
        if cleaned and "Contrast Event" not in cleaned:
            result["contractor_full_name"] = cleaned

    amount = (
        first_value(("total", "amount"))
        or first_value(("total", "sum"))
        or first_value(("check", "amount"))
        or first_value(("receipt", "amount"))
    )
    if amount is not None:
        parsed_amount = _money_from_text(str(amount))
        if parsed_amount is not None:
            result["receipt_amount"] = parsed_amount

    dt_value = (
        first_value(("check", "date"))
        or first_value(("receipt", "date"))
        or first_value(("create", "date"))
        or first_value(("date", "time"))
    )
    if dt_value:
        try:
            result["receipt_datetime"] = clean_datetime(str(dt_value))
        except HTTPException:
            parsed_dt = _parse_report_datetime(str(dt_value))
            if parsed_dt:
                result["receipt_datetime"] = parsed_dt

    service = (
        first_value(("service", "name"))
        or first_value(("item", "name"))
        or first_value(("product", "name"))
        or first_value(("goods", "name"))
        or first_value(("description",))
    )
    if service:
        result["service_name"] = clean_text(str(service))

    # JSON reports often contain human-readable labels too. Feeding a flattened
    # representation through the text parser covers variants without hardcoding
    # every historical backend key name.
    flattened_text = "\n".join(f"{path}: {value}" for path, value in rows if value not in {None, ""})
    text_result = _parse_esalyq_report_text(flattened_text)
    for key, value in text_result.items():
        result.setdefault(key, value)
    return result


def _kgd_response_payload(response: requests.Response) -> tuple[dict, str]:
    content_type = (response.headers.get("content-type") or "").lower()
    raw = response.content or b""
    if "json" in content_type:
        payload = response.json()
        return _parse_esalyq_json(payload), json.dumps(payload, ensure_ascii=False)
    if "pdf" in content_type or raw.startswith(b"%PDF"):
        try:
            reader = PdfReader(BytesIO(raw))
            text = "\n".join((page.extract_text() or "") for page in reader.pages[:3])
        except Exception as exc:
            raise HTTPException(status_code=502, detail="КГД вернул PDF чека, но его не удалось прочитать") from exc
        return _parse_esalyq_report_text(text), text
    encoding = response.encoding or "utf-8"
    decoded = raw.decode(encoding, errors="replace")
    text = _strip_html_to_text(decoded) if "html" in content_type or "<html" in decoded[:500].lower() else decoded
    return _parse_esalyq_report_text(text), text


def resolve_esalyq_qr(qr_payload: str) -> dict:
    canonical = canonical_esalyq_qr(qr_payload)
    if not canonical:
        raise HTTPException(status_code=400, detail="QR чека не найден")
    try:
        response = requests.get(
            canonical,
            timeout=KGD_RECEIPT_TIMEOUT,
            allow_redirects=True,
            headers={
                "User-Agent": "ContrastFinance/0.5.82 (+e-Salyq receipt verification)",
                "Accept": "application/json,text/html,application/pdf,text/plain;q=0.9,*/*;q=0.5",
            },
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Не удалось получить чек из КГД по QR. Попробуйте позже") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"КГД не отдал чек по QR (HTTP {response.status_code})")
    # Refuse redirects away from the trusted KGD host.
    final = urlparse(response.url)
    if (final.hostname or "").lower() != KGD_RECEIPT_HOST:
        raise HTTPException(status_code=502, detail="КГД перенаправил QR на неизвестный адрес")
    parsed, raw_text = _kgd_response_payload(response)
    useful = [
        parsed.get("contractor_full_name"), parsed.get("iin"), parsed.get("receipt_number"),
        parsed.get("receipt_datetime"), parsed.get("service_name"), parsed.get("receipt_amount"),
    ]
    count = sum(value not in {None, ""} for value in useful)
    if count < 2:
        raise HTTPException(status_code=502, detail="QR действителен, но формат ответа КГД пока не удалось разобрать")
    parsed["qr_payload"] = canonical
    parsed["parse_confidence"] = Decimal("100.00") if count >= 5 else Decimal("90.00")
    parsed["source_text"] = raw_text[:50000]
    return parsed


def _duplicate_receipt_id(
    db: Session,
    *,
    exclude_id: int | None = None,
    qr_payload: str | None = None,
    receipt_number: str | None = None,
    iin: str | None = None,
) -> int | None:
    canonical_qr = None
    if qr_payload:
        try:
            canonical_qr = canonical_esalyq_qr(qr_payload)
        except HTTPException:
            canonical_qr = str(qr_payload).strip()[:10000]
    if canonical_qr:
        query = select(SelfEmployedAccounting.id).where(SelfEmployedAccounting.qr_payload == canonical_qr)
        if exclude_id is not None:
            query = query.where(SelfEmployedAccounting.id != int(exclude_id))
        duplicate = db.execute(query.limit(1)).scalar_one_or_none()
        if duplicate is not None:
            return int(duplicate)
    number = clean_text(receipt_number, 80)
    normalized_iin = re.sub(r"\D", "", str(iin or ""))
    if number and len(re.sub(r"\D", "", number)) >= 6 and len(normalized_iin) == 12:
        query = select(SelfEmployedAccounting.id).where(
            SelfEmployedAccounting.receipt_number == number,
            SelfEmployedAccounting.iin == normalized_iin,
        )
        if exclude_id is not None:
            query = query.where(SelfEmployedAccounting.id != int(exclude_id))
        duplicate = db.execute(query.limit(1)).scalar_one_or_none()
        if duplicate is not None:
            return int(duplicate)
    return None


def assert_receipt_metadata_unique(
    db: Session,
    *,
    exclude_id: int | None = None,
    qr_payload: str | None = None,
    receipt_number: str | None = None,
    iin: str | None = None,
) -> None:
    duplicate = _duplicate_receipt_id(
        db,
        exclude_id=exclude_id,
        qr_payload=qr_payload,
        receipt_number=receipt_number,
        iin=iin,
    )
    if duplicate is not None:
        raise HTTPException(status_code=409, detail=f"Этот чек уже загружен (строка #{duplicate})")


def require_accounting_access(user: User) -> None:
    if user.role not in {"admin", "accountant"}:
        raise HTTPException(status_code=403, detail="Бухгалтерия доступна только администратору и бухгалтеру")


def clean_text(value: str | None, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).replace("\x00", " ").split()).strip()
    if not cleaned:
        return None
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def clean_iin(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return None
    if len(digits) != 12:
        raise HTTPException(status_code=400, detail="ИИН должен содержать 12 цифр")
    return digits


def clean_decimal(value: str | Decimal | None) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).replace(" ", "").replace(",", ".")
    try:
        result = Decimal(raw).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Некорректная сумма чека") from exc
    if result < 0:
        raise HTTPException(status_code=400, detail="Сумма чека не может быть отрицательной")
    return result


def clean_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректная дата чека") from exc


def is_active_request(request: PaymentRequest, event: Event, *, require_visible: bool = True) -> bool:
    return (
        request.payment_method == "self_employed"
        and request.status not in INACTIVE_REQUEST_STATUSES
        and getattr(request, "money_status", None) != "cancelled"
        and event.status != "cancelled"
        and (not require_visible or bool(getattr(request, "self_employed_accounting_visible", False)))
    )


def get_request_or_404(
    db: Session,
    request_id: int,
    *,
    require_active: bool = True,
    require_visible: bool = True,
) -> tuple[PaymentRequest, Event]:
    row = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id == int(request_id))
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    request, event = row
    if request.payment_method != "self_employed":
        raise HTTPException(status_code=409, detail="Эта заявка не относится к Самозанятым")
    if require_visible and not getattr(request, "self_employed_accounting_visible", False):
        raise HTTPException(status_code=409, detail="Эта историческая заявка не участвует в новой бухгалтерии")
    if require_active and not is_active_request(request, event, require_visible=require_visible):
        raise HTTPException(status_code=409, detail="Отменённая заявка не участвует в бухгалтерии")
    return request, event


def find_record_for_request(db: Session, request_id: int) -> SelfEmployedAccounting | None:
    # Since 0015 membership is the source of truth. Do not fall back to the old
    # payment_request_id anchor: detaching a request from a receipt must stay detached.
    return db.execute(
        select(SelfEmployedAccounting)
        .join(
            SelfEmployedAccountingRequest,
            SelfEmployedAccountingRequest.accounting_id == SelfEmployedAccounting.id,
        )
        .where(SelfEmployedAccountingRequest.payment_request_id == int(request_id))
    ).scalar_one_or_none()


def get_record_or_404(db: Session, accounting_id: int, *, lock: bool = False) -> SelfEmployedAccounting:
    query = select(SelfEmployedAccounting).where(SelfEmployedAccounting.id == int(accounting_id))
    if lock:
        query = query.with_for_update()
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Бухгалтерская строка не найдена")
    return record


def get_or_create_record(db: Session, request_id: int) -> SelfEmployedAccounting:
    record = find_record_for_request(db, request_id)
    if record is not None:
        return db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id == record.id)
            .with_for_update()
        ).scalar_one()

    record = SelfEmployedAccounting(
        payment_request_id=int(request_id),
        parse_status="empty",
        act_status="not_created",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(record)
    db.flush()
    db.add(
        SelfEmployedAccountingRequest(
            accounting_id=record.id,
            payment_request_id=int(request_id),
            created_at=datetime.utcnow(),
        )
    )
    db.flush()
    return record


def create_standalone_record(db: Session) -> SelfEmployedAccounting:
    record = SelfEmployedAccounting(
        payment_request_id=None,
        parse_status="empty",
        act_status="not_created",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(record)
    db.flush()
    return record


def record_has_business_data(record: SelfEmployedAccounting) -> bool:
    return bool(
        record.receipt_filename
        or record.receipt_sha256
        or record.contractor_full_name
        or record.iin
        or record.receipt_number
        or record.receipt_datetime
        or record.service_name
        or record.receipt_amount is not None
        or record.qr_payload
        or record.ocr_text
        or record.parse_status not in {None, "", "empty"}
        or record.confirmed_at
        or record.act_status not in {None, "", "not_created"}
    )


def _same_or_summary(values: list[str | None], summary: str) -> str | None:
    clean = [str(value).strip() for value in values if value and str(value).strip()]
    unique = list(dict.fromkeys(clean))
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return summary


def _surname_key(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    letters = "".join(ch if ch.isalpha() or ch in "-'" else " " for ch in text.casefold())
    tokens = [token.strip("-'") for token in letters.split() if len(token.strip("-'")) >= 2]
    return tokens[0] if tokens else None


def _visible_active_member_query():
    return (
        select(PaymentRequest, Event, User.name)
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(User, User.id == Event.manager_id)
        .where(
            PaymentRequest.payment_method == "self_employed",
            PaymentRequest.self_employed_accounting_visible.is_(True),
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
    )


def _members_for_record(db: Session, accounting_id: int) -> list[tuple[PaymentRequest, Event, str | None]]:
    member_ids = db.execute(
        select(SelfEmployedAccountingRequest.payment_request_id).where(
            SelfEmployedAccountingRequest.accounting_id == int(accounting_id)
        )
    ).scalars().all()
    if not member_ids:
        return []
    return list(
        db.execute(
            _visible_active_member_query().where(PaymentRequest.id.in_(member_ids))
        ).all()
    )


def _member_rows(members: list[tuple[PaymentRequest, Event, str | None]]) -> list[SelfEmployedAccountingMemberRead]:
    return [
        SelfEmployedAccountingMemberRead(
            payment_request_id=request.id,
            event_id=event.id,
            event_title=event.title,
            event_date=event.event_date,
            client_name=event.client_name,
            manager_name=manager_name,
            request_created_at=request.created_at,
            request_status=request.status,
            money_status=getattr(request, "money_status", "waiting_money"),
            request_amount=request.amount_requested,
            item_name=request.item_name_snapshot,
            request_contractor_name=request.contractor_name_snapshot,
            request_iin=request.iin_bin_snapshot,
            request_comment=request.comment,
        )
        for request, event, manager_name in members
    ]


def _receipt_fields(record: SelfEmployedAccounting | None) -> dict:
    return {
        "receipt_filename": record.receipt_filename if record else None,
        "receipt_content_type": record.receipt_content_type if record else None,
        "receipt_size": record.receipt_size if record else None,
        "receipt_sha256": record.receipt_sha256 if record else None,
        "receipt_uploaded_at": record.receipt_uploaded_at if record else None,
        "has_receipt": bool(record and record.receipt_filename and record.receipt_size),
        "contractor_full_name": record.contractor_full_name if record else None,
        "iin": record.iin if record else None,
        "receipt_number": record.receipt_number if record else None,
        "receipt_datetime": record.receipt_datetime if record else None,
        "service_name": record.service_name if record else None,
        "receipt_amount": record.receipt_amount if record else None,
        "qr_payload": record.qr_payload if record else None,
        "ocr_text": record.ocr_text if record else None,
        "parse_confidence": record.parse_confidence if record else None,
        "parse_status": record.parse_status if record else "empty",
        "confirmed_at": record.confirmed_at if record else None,
        "act_status": record.act_status if record else "not_created",
    }


def build_row(
    members: list[tuple[PaymentRequest, Event, str | None]],
    record: SelfEmployedAccounting | None,
) -> SelfEmployedAccountingRead:
    if not members:
        if record is None:
            raise ValueError("Standalone accounting row requires a record")
        return SelfEmployedAccountingRead(
            row_key=f"accounting:{record.id}",
            row_kind="receipt",
            is_receipt_only=True,
            payment_request_id=None,
            payment_request_ids=[],
            request_count=0,
            accounting_id=record.id,
            is_grouped=False,
            members=[],
            request_amount=Decimal("0.00"),
            request_status="unlinked",
            money_status=None,
            request_created_at=record.receipt_uploaded_at or record.created_at,
            **_receipt_fields(record),
        )

    members = sorted(members, key=lambda item: (item[0].created_at, item[0].id))
    anchor_request, anchor_event, _ = members[0]
    total = sum((Decimal(item[0].amount_requested) for item in members), Decimal("0.00"))
    request_ids = [item[0].id for item in members]
    request_statuses = [item[0].status for item in members]
    money_statuses = [getattr(item[0], "money_status", "waiting_money") for item in members]
    item_names = [request.item_name_snapshot for request, _, _ in members]
    comments = [request.comment for request, _, _ in members]
    contractor_names = [request.contractor_name_snapshot for request, _, _ in members]

    return SelfEmployedAccountingRead(
        row_key=f"accounting:{record.id}" if record else f"request:{anchor_request.id}",
        row_kind="request",
        is_receipt_only=False,
        payment_request_id=anchor_request.id,
        payment_request_ids=request_ids,
        request_count=len(request_ids),
        accounting_id=record.id if record else None,
        is_grouped=len(request_ids) > 1,
        members=_member_rows(members),
        event_id=anchor_event.id,
        event_title=_same_or_summary(
            [event.title for _, event, _ in members],
            f"{len(set(event.id for _, event, _ in members))} мероприятий",
        ),
        event_date=min((event.event_date for _, event, _ in members if event.event_date), default=None),
        client_name=_same_or_summary([event.client_name for _, event, _ in members], "Несколько клиентов"),
        manager_name=_same_or_summary([manager for _, _, manager in members], "Несколько менеджеров"),
        request_created_at=max(request.created_at for request, _, _ in members),
        request_status=request_statuses[0] if len(set(request_statuses)) == 1 else "mixed",
        money_status=money_statuses[0] if len(set(money_statuses)) == 1 else "mixed",
        request_amount=total,
        item_name=" + ".join(dict.fromkeys(name for name in item_names if name)) or None,
        request_contractor_name=_same_or_summary(contractor_names, "Самозанятый"),
        request_iin=_same_or_summary([request.iin_bin_snapshot for request, _, _ in members], ""),
        request_comment=" · ".join(dict.fromkeys(comment for comment in comments if comment)) or None,
        **_receipt_fields(record),
    )


def load_accounting_row(db: Session, accounting_id: int) -> SelfEmployedAccountingRead:
    record = get_record_or_404(db, accounting_id)
    return build_row(_members_for_record(db, record.id), record)


def load_group_row(db: Session, request_id: int) -> SelfEmployedAccountingRead:
    request, _ = get_request_or_404(db, request_id)
    record = find_record_for_request(db, request.id)
    if record is None:
        member = db.execute(_visible_active_member_query().where(PaymentRequest.id == request.id)).one_or_none()
        if member is None:
            raise HTTPException(status_code=404, detail="Заявка не найдена в бухгалтерии")
        return build_row([member], None)
    return load_accounting_row(db, record.id)


def _contractor_identity(requests: list[PaymentRequest]) -> tuple[str | None, str | None]:
    iins = {
        "".join(ch for ch in str(request.iin_bin_snapshot or "") if ch.isdigit())
        for request in requests
        if request.iin_bin_snapshot
    }
    iins.discard("")
    if len(iins) > 1:
        raise HTTPException(status_code=409, detail="Нельзя объединить заявки разных самозанятых: ИИН не совпадает")

    names = {
        " ".join(str(request.contractor_name_snapshot or "").lower().split())
        for request in requests
        if request.contractor_name_snapshot
    }
    names.discard("")
    if not iins and len(names) > 1:
        raise HTTPException(status_code=409, detail="Нельзя объединить заявки разных самозанятых: ФИО не совпадает")
    return (next(iter(iins), None), next(iter(names), None))


def _row_matches_accounting_month(
    row: SelfEmployedAccountingRead,
    month_bounds: tuple[date, date],
) -> bool:
    start, end = month_bounds
    if row.has_receipt and row.receipt_datetime:
        return start <= row.receipt_datetime.date() < end
    if row.has_receipt and not row.receipt_datetime:
        return bool(row.event_date and start <= row.event_date < end)
    return bool(row.event_date and start <= row.event_date < end)


def _month_bounds(month: str) -> tuple[date, date]:
    try:
        year_part, month_part = month.split("-")[:2]
        year_num = int(year_part)
        month_num = int(month_part)
        if not 1 <= month_num <= 12:
            raise ValueError
    except Exception as exc:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM") from exc
    start = date(year_num, month_num, 1)
    end = date(year_num + 1, 1, 1) if month_num == 12 else date(year_num, month_num + 1, 1)
    return start, end


@router.get("/r1/customer-profile", response_model=R1CustomerProfileRead)
def get_r1_customer_profile(
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    return R1CustomerProfileRead(**R1_CUSTOMER_PROFILE)


@router.get("", response_model=list[SelfEmployedAccountingRead])
def list_self_employed_accounting(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)

    query = (
        select(
            PaymentRequest,
            Event,
            User.name,
            SelfEmployedAccountingRequest.accounting_id,
            SelfEmployedAccounting,
        )
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(User, User.id == Event.manager_id)
        .outerjoin(
            SelfEmployedAccountingRequest,
            SelfEmployedAccountingRequest.payment_request_id == PaymentRequest.id,
        )
        .outerjoin(
            SelfEmployedAccounting,
            SelfEmployedAccounting.id == SelfEmployedAccountingRequest.accounting_id,
        )
        .where(
            PaymentRequest.payment_method == "self_employed",
            PaymentRequest.self_employed_accounting_visible.is_(True),
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
    )

    # Do not filter request-backed rows by the event date in SQL. Once a receipt
    # exists, accounting belongs to the month printed on that receipt, even when
    # the event/request lives in another month. We therefore build rows first and
    # apply the accounting-month rule below.
    month_bounds = _month_bounds(month) if month else None

    rows = db.execute(query).all()
    grouped_members: dict[tuple[str, int], list[tuple[PaymentRequest, Event, str | None]]] = defaultdict(list)
    records: dict[tuple[str, int], SelfEmployedAccounting | None] = {}
    for request, event, manager_name, accounting_id, record in rows:
        key = ("accounting", int(accounting_id)) if accounting_id is not None else ("request", int(request.id))
        grouped_members[key].append((request, event, manager_name))
        records[key] = record

    result = [build_row(members, records.get(key)) for key, members in grouped_members.items()]

    if month_bounds:
        # A real e-Salyq receipt date is the source of truth for accounting
        # period. Rows still waiting for a receipt remain discoverable by event
        # month so the accountant can attach the future receipt.
        result = [row for row in result if _row_matches_accounting_month(row, month_bounds)]

    # Receipt-first workflow: imported checks can exist before a request is found.
    no_members = ~exists(
        select(SelfEmployedAccountingRequest.id).where(
            SelfEmployedAccountingRequest.accounting_id == SelfEmployedAccounting.id
        )
    )
    standalone_query = select(SelfEmployedAccounting).where(
        no_members,
        SelfEmployedAccounting.receipt_filename.is_not(None),
    )
    standalone_records = db.execute(standalone_query).scalars().all()
    for record in standalone_records:
        if month_bounds:
            # Standalone imported receipts are distributed strictly by the issue
            # date read from the receipt. If OCR did not read a date yet, keep the
            # row in the month of upload until it is corrected manually.
            probe = record.receipt_datetime or record.receipt_uploaded_at or record.created_at
            if probe and not (month_bounds[0] <= probe.date() < month_bounds[1]):
                continue
        result.append(build_row([], record))

    def sort_key(row: SelfEmployedAccountingRead):
        probe = row.receipt_datetime or row.request_created_at or row.receipt_uploaded_at or datetime.min
        return (probe, row.accounting_id or 0, row.payment_request_id or 0)

    result.sort(key=sort_key, reverse=True)
    return result


@router.post("/groups", response_model=SelfEmployedAccountingRead)
def group_self_employed_requests(
    payload: SelfEmployedAccountingGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Legacy checkbox grouping remains available to old clients; drag/drop is preferred."""
    require_accounting_access(current_user)
    requested_ids = list(dict.fromkeys(int(value) for value in payload.request_ids))
    if len(requested_ids) < 2:
        raise HTTPException(status_code=400, detail="Выберите минимум две заявки")

    selected_rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(requested_ids))
    ).all()
    if len(selected_rows) != len(requested_ids):
        raise HTTPException(status_code=404, detail="Одна из выбранных заявок не найдена")
    for request, event in selected_rows:
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Заявка №{request.id} не участвует в новой бухгалтерии")

    existing_links = db.execute(
        select(SelfEmployedAccountingRequest).where(
            SelfEmployedAccountingRequest.payment_request_id.in_(requested_ids)
        )
    ).scalars().all()
    source_group_ids = sorted({link.accounting_id for link in existing_links})
    all_request_ids = set(requested_ids)
    if source_group_ids:
        all_request_ids.update(
            db.execute(
                select(SelfEmployedAccountingRequest.payment_request_id).where(
                    SelfEmployedAccountingRequest.accounting_id.in_(source_group_ids)
                )
            ).scalars().all()
        )

    all_rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(sorted(all_request_ids)))
    ).all()
    for request, event in all_rows:
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Группа содержит неактивную заявку №{request.id}")
    _contractor_identity([request for request, _ in all_rows])

    source_records = []
    if source_group_ids:
        source_records = db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id.in_(source_group_ids))
            .with_for_update()
        ).scalars().all()

    meaningful = [record for record in source_records if record_has_business_data(record)]
    if len(meaningful) > 1:
        raise HTTPException(status_code=409, detail="Нельзя объединить строки, у которых уже есть разные чеки")
    destination = meaningful[0] if meaningful else (source_records[0] if source_records else None)
    if destination is not None and destination.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя менять состав строки после формирования АВР")
    if destination is None:
        destination = SelfEmployedAccounting(
            payment_request_id=requested_ids[0],
            parse_status="empty",
            act_status="not_created",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(destination)
        db.flush()

    if source_group_ids:
        links = db.execute(
            select(SelfEmployedAccountingRequest).where(
                SelfEmployedAccountingRequest.accounting_id.in_(source_group_ids)
            )
        ).scalars().all()
        for link in links:
            link.accounting_id = destination.id
            db.add(link)

    linked = set(
        db.execute(
            select(SelfEmployedAccountingRequest.payment_request_id).where(
                SelfEmployedAccountingRequest.accounting_id == destination.id
            )
        ).scalars().all()
    )
    for request_id in sorted(all_request_ids):
        if request_id not in linked:
            db.add(SelfEmployedAccountingRequest(accounting_id=destination.id, payment_request_id=request_id))
    db.flush()
    for record in source_records:
        if record.id != destination.id:
            db.delete(record)
    if record_has_business_data(destination):
        if destination.receipt_filename and destination.parse_status == "reviewed":
            destination.parse_status = "parsed"
        destination.confirmed_at = None
        destination.confirmed_by_user_id = None
    destination.updated_at = datetime.utcnow()
    db.add(destination)
    db.commit()
    return load_accounting_row(db, destination.id)


@router.post("/groups/{request_id}/split")
def split_self_employed_group(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    get_request_or_404(db, request_id)
    record = find_record_for_request(db, request_id)
    if record is None:
        return {"ok": True, "split": 0}
    member_ids = db.execute(
        select(SelfEmployedAccountingRequest.payment_request_id).where(
            SelfEmployedAccountingRequest.accounting_id == record.id
        )
    ).scalars().all()
    if len(member_ids) <= 1:
        return {"ok": True, "split": 0}
    if record_has_business_data(record):
        raise HTTPException(status_code=409, detail="Строку с чеком разъединяйте кнопками «Отвязать» у заявок")
    count = len(member_ids)
    db.delete(record)
    db.commit()
    return {"ok": True, "split": count}


def _save_receipt_binary(
    db: Session,
    record: SelfEmployedAccounting,
    *,
    content: bytes,
    filename: str,
    content_type: str,
    current_user: User,
) -> None:
    digest = sha256(content).hexdigest()
    duplicate = db.execute(
        select(SelfEmployedAccounting.id).where(
            SelfEmployedAccounting.receipt_sha256 == digest,
            SelfEmployedAccounting.id != record.id,
        ).limit(1)
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail=f"Этот файл чека уже загружен (строка #{duplicate})")
    record.receipt_filename = Path(filename or "receipt").name[:255]
    record.receipt_content_type = content_type
    record.receipt_size = len(content)
    record.receipt_sha256 = digest
    record.receipt_data = content
    record.receipt_uploaded_at = datetime.utcnow()
    record.receipt_uploaded_by_user_id = current_user.id
    record.parse_status = "uploaded"
    record.confirmed_at = None
    record.confirmed_by_user_id = None
    record.updated_at = datetime.utcnow()


def _apply_import_metadata(
    record: SelfEmployedAccounting,
    *,
    contractor_full_name: str | None,
    iin: str | None,
    receipt_number: str | None,
    receipt_datetime: str | None,
    service_name: str | None,
    receipt_amount: str | None,
    qr_payload: str | None,
    ocr_text: str | None,
    parse_confidence: str | None,
) -> None:
    record.contractor_full_name = clean_text(contractor_full_name, 255)
    record.iin = clean_iin(iin)
    record.receipt_number = clean_text(receipt_number, 80)
    record.receipt_datetime = clean_datetime(receipt_datetime)
    record.service_name = clean_text(service_name)
    record.receipt_amount = clean_decimal(receipt_amount)
    record.qr_payload = canonical_esalyq_qr(qr_payload) if qr_payload else None
    record.ocr_text = str(ocr_text)[:50000] if ocr_text else None
    if parse_confidence not in {None, ""}:
        try:
            confidence = Decimal(str(parse_confidence))
        except InvalidOperation:
            confidence = Decimal("0")
        record.parse_confidence = max(Decimal("0"), min(Decimal("100"), confidence))
    if any([
        record.contractor_full_name,
        record.iin,
        record.receipt_number,
        record.receipt_datetime,
        record.service_name,
        record.receipt_amount is not None,
        record.qr_payload,
        record.ocr_text,
    ]):
        record.parse_status = "parsed"


def _unreceipted_candidate_groups(db: Session) -> list[tuple[list[PaymentRequest], SelfEmployedAccounting | None]]:
    rows = db.execute(
        select(PaymentRequest, Event, SelfEmployedAccountingRequest.accounting_id, SelfEmployedAccounting)
        .join(Event, Event.id == PaymentRequest.event_id)
        .outerjoin(
            SelfEmployedAccountingRequest,
            SelfEmployedAccountingRequest.payment_request_id == PaymentRequest.id,
        )
        .outerjoin(SelfEmployedAccounting, SelfEmployedAccounting.id == SelfEmployedAccountingRequest.accounting_id)
        .where(
            PaymentRequest.payment_method == "self_employed",
            PaymentRequest.self_employed_accounting_visible.is_(True),
            PaymentRequest.status.notin_(list(INACTIVE_REQUEST_STATUSES)),
            PaymentRequest.money_status != "cancelled",
            Event.status != "cancelled",
        )
    ).all()
    grouped: dict[tuple[str, int], list[PaymentRequest]] = defaultdict(list)
    records: dict[tuple[str, int], SelfEmployedAccounting | None] = {}
    for request, _event, accounting_id, record in rows:
        key = ("accounting", int(accounting_id)) if accounting_id is not None else ("request", int(request.id))
        grouped[key].append(request)
        records[key] = record
    result = []
    for key, requests in grouped.items():
        record = records.get(key)
        if record and record.receipt_filename:
            continue
        result.append((requests, record))
    return result


def _auto_match_receipt(
    db: Session,
    contractor_full_name: str | None,
    receipt_amount: Decimal | None,
) -> tuple[SelfEmployedAccounting | None, str, list[int]]:
    surname = _surname_key(contractor_full_name)
    if not surname or receipt_amount is None:
        return None, "unmatched", []

    matches: list[tuple[list[PaymentRequest], SelfEmployedAccounting | None]] = []
    for requests, record in _unreceipted_candidate_groups(db):
        total = sum((Decimal(request.amount_requested) for request in requests), Decimal("0.00")).quantize(Decimal("0.01"))
        if total != receipt_amount:
            continue
        request_surnames = {_surname_key(request.contractor_name_snapshot) for request in requests}
        request_surnames.discard(None)
        if surname in request_surnames:
            matches.append((requests, record))

    if len(matches) != 1:
        return None, "ambiguous" if len(matches) > 1 else "unmatched", []

    requests, record = matches[0]
    if record is None:
        record = get_or_create_record(db, requests[0].id)
    return record, "matched", [request.id for request in requests]


@router.post("/receipts/resolve-qr", response_model=SelfEmployedReceiptQrResolveRead)
def resolve_self_employed_receipt_qr(
    payload: SelfEmployedReceiptQrResolveCreate,
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    parsed = resolve_esalyq_qr(payload.qr_payload)
    return SelfEmployedReceiptQrResolveRead(
        contractor_full_name=parsed.get("contractor_full_name"),
        iin=parsed.get("iin"),
        receipt_number=parsed.get("receipt_number"),
        receipt_datetime=parsed.get("receipt_datetime"),
        service_name=parsed.get("service_name"),
        receipt_amount=parsed.get("receipt_amount"),
        qr_payload=parsed["qr_payload"],
        parse_confidence=parsed.get("parse_confidence", Decimal("100.00")),
        source="kgd_qr",
        message="Данные получены из официального чека КГД по QR",
    )


@router.post("/receipts/import", response_model=SelfEmployedReceiptImportRead)
async def import_self_employed_receipt(
    file: UploadFile = File(...),
    contractor_full_name: str | None = Form(default=None),
    iin: str | None = Form(default=None),
    receipt_number: str | None = Form(default=None),
    receipt_datetime: str | None = Form(default=None),
    service_name: str | None = Form(default=None),
    receipt_amount: str | None = Form(default=None),
    qr_payload: str | None = Form(default=None),
    ocr_text: str | None = Form(default=None),
    parse_confidence: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    content_type = (file.content_type or "").lower().split(";", 1)[0].strip()
    if content_type not in ALLOWED_RECEIPT_TYPES:
        raise HTTPException(status_code=400, detail="Поддерживаются JPG, PNG, WEBP и PDF")
    content = await file.read(MAX_RECEIPT_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(content) > MAX_RECEIPT_BYTES:
        raise HTTPException(status_code=413, detail="Чек слишком большой. Максимум 10 МБ")

    qr_error: str | None = None
    if qr_payload:
        # QR is the source of truth. The browser only decodes the QR image; the
        # backend then fetches the official KGD receipt report and overwrites
        # any OCR fallback values with the verified data.
        try:
            official = resolve_esalyq_qr(qr_payload)
            contractor_full_name = official.get("contractor_full_name") or contractor_full_name
            iin = official.get("iin") or iin
            receipt_number = official.get("receipt_number") or receipt_number
            official_dt = official.get("receipt_datetime")
            receipt_datetime = official_dt.isoformat() if isinstance(official_dt, datetime) else (official_dt or receipt_datetime)
            service_name = official.get("service_name") or service_name
            official_amount = official.get("receipt_amount")
            receipt_amount = str(official_amount) if official_amount is not None else receipt_amount
            qr_payload = official.get("qr_payload") or qr_payload
            parse_confidence = str(official.get("parse_confidence", Decimal("100.00")))
            # Keep the official KGD report text only as diagnostics. It is not OCR.
            ocr_text = official.get("source_text") or ocr_text
        except HTTPException as exc:
            qr_payload = canonical_esalyq_qr(qr_payload)
            qr_error = str(exc.detail)

    assert_receipt_metadata_unique(
        db,
        qr_payload=qr_payload,
        receipt_number=receipt_number,
        iin=iin,
    )

    normalized_amount = clean_decimal(receipt_amount)
    record, match_status, matched_ids = _auto_match_receipt(db, contractor_full_name, normalized_amount)
    if record is None:
        record = create_standalone_record(db)

    _save_receipt_binary(
        db,
        record,
        content=content,
        filename=file.filename or "receipt",
        content_type=content_type,
        current_user=current_user,
    )
    _apply_import_metadata(
        record,
        contractor_full_name=contractor_full_name,
        iin=iin,
        receipt_number=receipt_number,
        receipt_datetime=receipt_datetime,
        service_name=service_name,
        receipt_amount=receipt_amount,
        qr_payload=qr_payload,
        ocr_text=ocr_text,
        parse_confidence=parse_confidence,
    )
    if qr_error:
        record.parse_status = "uploaded"
    db.add(record)
    db.commit()

    if qr_error:
        message = f"Чек сохранён, QR найден, но данные КГД не получены: {qr_error}"
    elif match_status == "matched":
        message = f"Чек проверен по QR КГД и автоматически привязан к заявке{'м' if len(matched_ids) > 1 else ''} №" + ", №".join(str(i) for i in matched_ids)
    elif match_status == "ambiguous":
        message = "Чек проверен по QR КГД. Есть несколько заявок с такой фамилией и суммой — оставлен отдельной строкой"
    else:
        message = "Чек проверен по QR КГД. Точного совпадения фамилии и суммы нет — создан отдельной строкой" if qr_payload else "QR не найден: чек создан отдельной строкой по резервному распознаванию"
    return SelfEmployedReceiptImportRead(
        row=load_accounting_row(db, record.id),
        match_status=match_status,
        matched_request_ids=matched_ids,
        message=message,
    )


@router.post("/receipts/{accounting_id}/attach", response_model=SelfEmployedAccountingRead)
def attach_requests_to_receipt(
    accounting_id: int,
    payload: SelfEmployedAccountingAttachCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    target = get_record_or_404(db, accounting_id, lock=True)
    if not target.receipt_filename:
        raise HTTPException(status_code=409, detail="Перетаскивать заявки можно только на строку с чеком")
    if target.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя менять состав после формирования АВР")

    request_ids = list(dict.fromkeys(int(value) for value in payload.request_ids))
    rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(request_ids))
    ).all()
    if len(rows) != len(request_ids):
        raise HTTPException(status_code=404, detail="Одна из заявок не найдена")
    for request, event in rows:
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Заявка №{request.id} не участвует в новой бухгалтерии")

    source_ids: set[int] = set()
    for request_id in request_ids:
        source = find_record_for_request(db, request_id)
        if source is None or source.id == target.id:
            continue
        source = get_record_or_404(db, source.id, lock=True)
        if source.receipt_filename:
            raise HTTPException(status_code=409, detail="Нельзя перетащить строку, у которой уже есть другой чек")
        if source.act_status not in {None, "", "not_created"}:
            raise HTTPException(status_code=409, detail="Нельзя переносить заявку после формирования АВР")
        source_ids.add(source.id)

    # Move all members of a source request group, not only its anchor row.
    expanded_request_ids = set(request_ids)
    if source_ids:
        expanded_request_ids.update(
            db.execute(
                select(SelfEmployedAccountingRequest.payment_request_id).where(
                    SelfEmployedAccountingRequest.accounting_id.in_(source_ids)
                )
            ).scalars().all()
        )

    expanded_rows = db.execute(
        select(PaymentRequest, Event)
        .join(Event, Event.id == PaymentRequest.event_id)
        .where(PaymentRequest.id.in_(sorted(expanded_request_ids)))
    ).all()
    for request, event in expanded_rows:
        if not is_active_request(request, event):
            raise HTTPException(status_code=409, detail=f"Группа содержит неактивную заявку №{request.id}")

    links = db.execute(
        select(SelfEmployedAccountingRequest).where(
            SelfEmployedAccountingRequest.payment_request_id.in_(sorted(expanded_request_ids))
        )
    ).scalars().all()
    linked_ids = {link.payment_request_id for link in links}
    for link in links:
        link.accounting_id = target.id
        db.add(link)
    for request_id in sorted(expanded_request_ids - linked_ids):
        db.add(SelfEmployedAccountingRequest(accounting_id=target.id, payment_request_id=request_id))
    db.flush()

    # Source rows without receipts become redundant after their requests moved.
    for source_id in source_ids:
        source = db.get(SelfEmployedAccounting, source_id)
        if source is not None:
            remaining = db.execute(
                select(SelfEmployedAccountingRequest.id).where(
                    SelfEmployedAccountingRequest.accounting_id == source_id
                ).limit(1)
            ).scalar_one_or_none()
            if remaining is None:
                db.delete(source)

    target.confirmed_at = None
    target.confirmed_by_user_id = None
    if target.parse_status == "reviewed":
        target.parse_status = "parsed"
    target.updated_at = datetime.utcnow()
    db.add(target)
    db.commit()
    return load_accounting_row(db, target.id)


@router.delete("/receipts/{accounting_id}/requests/{request_id}", response_model=SelfEmployedAccountingRead)
def detach_request_from_receipt(
    accounting_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    target = get_record_or_404(db, accounting_id, lock=True)
    get_request_or_404(db, request_id)
    if target.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя менять состав после формирования АВР")
    link = db.execute(
        select(SelfEmployedAccountingRequest).where(
            SelfEmployedAccountingRequest.accounting_id == target.id,
            SelfEmployedAccountingRequest.payment_request_id == int(request_id),
        )
    ).scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Эта заявка не привязана к чеку")
    db.delete(link)
    # payment_request_id is only a legacy anchor from 0014. Membership is the
    # source of truth now; clear the anchor when that request is detached so the
    # request can later receive a different receipt without hitting the old
    # unique constraint.
    if target.payment_request_id == int(request_id):
        target.payment_request_id = None
    target.confirmed_at = None
    target.confirmed_by_user_id = None
    if target.parse_status == "reviewed":
        target.parse_status = "parsed"
    target.updated_at = datetime.utcnow()
    db.add(target)
    db.commit()
    return load_accounting_row(db, target.id)


@router.delete("/receipts/{accounting_id}")
def delete_accounting_receipt(
    accounting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    target = get_record_or_404(db, accounting_id, lock=True)
    if target.act_status not in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Нельзя удалить чек после формирования АВР")
    member_ids = list(
        db.execute(
            select(SelfEmployedAccountingRequest.payment_request_id).where(
                SelfEmployedAccountingRequest.accounting_id == target.id
            )
        ).scalars().all()
    )
    # Deleting the accounting object removes the receipt and its membership links.
    # Active payment requests themselves are untouched and immediately reappear as
    # separate rows waiting for a new receipt. Standalone bad receipts simply vanish.
    db.delete(target)
    db.commit()
    return {"ok": True, "released_request_ids": member_ids}


@router.post("/{request_id}/receipt", response_model=SelfEmployedAccountingRead)
async def upload_self_employed_receipt(
    request_id: int,
    file: UploadFile = File(...),
    contractor_full_name: str | None = Form(default=None),
    iin: str | None = Form(default=None),
    receipt_number: str | None = Form(default=None),
    receipt_datetime: str | None = Form(default=None),
    service_name: str | None = Form(default=None),
    receipt_amount: str | None = Form(default=None),
    qr_payload: str | None = Form(default=None),
    ocr_text: str | None = Form(default=None),
    parse_confidence: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    get_request_or_404(db, request_id)
    content_type = (file.content_type or "").lower().split(";", 1)[0].strip()
    if content_type not in ALLOWED_RECEIPT_TYPES:
        raise HTTPException(status_code=400, detail="Поддерживаются JPG, PNG, WEBP и PDF")
    content = await file.read(MAX_RECEIPT_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(content) > MAX_RECEIPT_BYTES:
        raise HTTPException(status_code=413, detail="Чек слишком большой. Максимум 10 МБ")

    qr_error: str | None = None
    if qr_payload:
        try:
            official = resolve_esalyq_qr(qr_payload)
            contractor_full_name = official.get("contractor_full_name") or contractor_full_name
            iin = official.get("iin") or iin
            receipt_number = official.get("receipt_number") or receipt_number
            official_dt = official.get("receipt_datetime")
            receipt_datetime = official_dt.isoformat() if isinstance(official_dt, datetime) else (official_dt or receipt_datetime)
            service_name = official.get("service_name") or service_name
            official_amount = official.get("receipt_amount")
            receipt_amount = str(official_amount) if official_amount is not None else receipt_amount
            qr_payload = official.get("qr_payload") or qr_payload
            parse_confidence = str(official.get("parse_confidence", Decimal("100.00")))
            ocr_text = official.get("source_text") or ocr_text
        except HTTPException as exc:
            qr_payload = canonical_esalyq_qr(qr_payload)
            qr_error = str(exc.detail)

    record = get_or_create_record(db, request_id)
    assert_receipt_metadata_unique(
        db,
        exclude_id=record.id,
        qr_payload=qr_payload,
        receipt_number=receipt_number,
        iin=iin,
    )
    _save_receipt_binary(
        db,
        record,
        content=content,
        filename=file.filename or "receipt",
        content_type=content_type,
        current_user=current_user,
    )
    _apply_import_metadata(
        record,
        contractor_full_name=contractor_full_name,
        iin=iin,
        receipt_number=receipt_number,
        receipt_datetime=receipt_datetime,
        service_name=service_name,
        receipt_amount=receipt_amount,
        qr_payload=qr_payload,
        ocr_text=ocr_text,
        parse_confidence=parse_confidence,
    )
    if qr_error and record.parse_status == "parsed" and not any((contractor_full_name, iin, receipt_number, receipt_datetime, service_name, receipt_amount)):
        record.parse_status = "uploaded"
    db.add(record)
    db.commit()
    return load_group_row(db, request_id)


def _update_record(record: SelfEmployedAccounting, payload: SelfEmployedAccountingUpdate, current_user: User) -> None:
    if payload.contractor_full_name is not None:
        record.contractor_full_name = clean_text(payload.contractor_full_name, 255)
    if payload.iin is not None:
        record.iin = clean_iin(payload.iin)
    if payload.receipt_number is not None:
        record.receipt_number = clean_text(payload.receipt_number, 80)
    if payload.receipt_datetime is not None:
        record.receipt_datetime = payload.receipt_datetime.replace(tzinfo=None)
    if payload.service_name is not None:
        record.service_name = clean_text(payload.service_name)
    if payload.receipt_amount is not None:
        record.receipt_amount = clean_decimal(payload.receipt_amount)
    if payload.qr_payload is not None:
        record.qr_payload = canonical_esalyq_qr(payload.qr_payload) if payload.qr_payload else None
    if payload.ocr_text is not None:
        record.ocr_text = str(payload.ocr_text)[:50000]
    if payload.parse_confidence is not None:
        confidence = Decimal(payload.parse_confidence)
        record.parse_confidence = max(Decimal("0"), min(Decimal("100"), confidence))

    if any(
        value is not None
        for value in (
            payload.contractor_full_name,
            payload.iin,
            payload.receipt_number,
            payload.receipt_datetime,
            payload.service_name,
            payload.receipt_amount,
            payload.qr_payload,
            payload.ocr_text,
            payload.parse_confidence,
        )
    ):
        record.parse_status = "reviewed" if payload.mark_confirmed else "parsed"

    if payload.mark_confirmed:
        missing = []
        if not record.contractor_full_name:
            missing.append("ФИО")
        if not record.iin:
            missing.append("ИИН")
        if record.receipt_amount is None:
            missing.append("сумма")
        if not record.service_name:
            missing.append("услуга")
        if missing:
            raise HTTPException(status_code=400, detail="Для подтверждения заполните: " + ", ".join(missing))
        record.parse_status = "reviewed"
        record.confirmed_at = datetime.utcnow()
        record.confirmed_by_user_id = current_user.id
    record.updated_at = datetime.utcnow()


@router.patch("/receipts/{accounting_id}", response_model=SelfEmployedAccountingRead)
def update_receipt_accounting(
    accounting_id: int,
    payload: SelfEmployedAccountingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    record = get_record_or_404(db, accounting_id, lock=True)
    assert_receipt_metadata_unique(
        db,
        exclude_id=record.id,
        qr_payload=payload.qr_payload,
        receipt_number=payload.receipt_number,
        iin=payload.iin,
    )
    _update_record(record, payload, current_user)
    db.add(record)
    db.commit()
    return load_accounting_row(db, record.id)


@router.patch("/{request_id}", response_model=SelfEmployedAccountingRead)
def update_self_employed_accounting(
    request_id: int,
    payload: SelfEmployedAccountingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    request, _ = get_request_or_404(db, request_id)
    record = get_or_create_record(db, request_id)
    assert_receipt_metadata_unique(
        db,
        exclude_id=record.id,
        qr_payload=payload.qr_payload,
        receipt_number=payload.receipt_number,
        iin=payload.iin,
    )
    _update_record(record, payload, current_user)
    db.add(record)
    db.commit()
    return load_group_row(db, request.id)


def _receipt_response(db: Session, record: SelfEmployedAccounting) -> Response:
    row = db.execute(
        select(
            SelfEmployedAccounting.receipt_data,
            SelfEmployedAccounting.receipt_filename,
            SelfEmployedAccounting.receipt_content_type,
        ).where(SelfEmployedAccounting.id == record.id)
    ).one_or_none()
    if row is None or row.receipt_data is None:
        raise HTTPException(status_code=404, detail="Чек не загружен")
    filename = Path(row.receipt_filename or "receipt").name.replace('"', "")
    ascii_name = "receipt" + (Path(filename).suffix or "")
    encoded_name = quote(filename, safe="")
    return Response(
        content=row.receipt_data,
        media_type=row.receipt_content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename={ascii_name}; filename*=UTF-8''{encoded_name}",
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/receipts/{accounting_id}/file")
def download_accounting_receipt_by_id(
    accounting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    return _receipt_response(db, get_record_or_404(db, accounting_id))


@router.get("/{request_id}/receipt")
def download_self_employed_receipt(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    get_request_or_404(db, request_id)
    record = find_record_for_request(db, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Чек не загружен")
    return _receipt_response(db, record)
