from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
from html import unescape
from io import BytesIO
import json
import re
import unicodedata
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
from sqlalchemy.orm.attributes import set_committed_value

from app.db.session import get_db
from app.core.r1_profile import R1_CUSTOMER_PROFILE
from app.models.event import Event
from app.models.payment_request import PaymentRequest
from app.models.self_employed_accounting import SelfEmployedAccounting
from app.models.self_employed_accounting_request import SelfEmployedAccountingRequest
from app.models.self_employed_contact import SelfEmployedContact
from app.models.user import User
from app.schemas.self_employed_accounting import (
    SelfEmployedAccountingAttachCreate,
    SelfEmployedAccountingGroupCreate,
    SelfEmployedActPartyRead,
    SelfEmployedAccountingMemberRead,
    SelfEmployedAccountingRead,
    SelfEmployedAccountingUpdate,
    SelfEmployedReceiptImportRead,
    SelfEmployedReceiptQrResolveCreate,
    SelfEmployedReceiptQrResolveRead,
    SelfEmployedReceiptQrRefreshCreate,
    R1CustomerProfileRead,
)
from app.services.auth import get_current_user
from app.services.accounting_receipt_data_fix import (
    _extract_iin_from_text,
    _extract_json_iin,
    _extract_json_receipt_number,
    _extract_json_unicode_name,
    _extract_receipt_number_from_text,
    _extract_unicode_name_from_text,
    _find_json_receipt_datetime,
)
from app.services.r1_act_pdf import R1ActPayload, generate_r1_act_pdf


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
KASPI_RECEIPT_HOST = "receipt.kaspi.kz"
KASPI_RECEIPT_PATH = "/web/self-employed"
KASPI_RECEIPT_TIMEOUT = (5, 20)


def _phone_digits(value: str | None) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    return digits if 10 <= len(digits) <= 15 else ""


def _saved_contact(db: Session, iin: str | None) -> SelfEmployedContact | None:
    digits = re.sub(r"\D", "", str(iin or ""))
    if len(digits) != 12:
        return None
    return db.execute(select(SelfEmployedContact).where(SelfEmployedContact.iin == digits)).scalar_one_or_none()


def _hydrate_contact_phone(db: Session, record: SelfEmployedAccounting | None) -> None:
    if record is None or record.contractor_phone:
        return
    contact = _saved_contact(db, record.iin)
    if contact and contact.whatsapp_phone:
        # Expose the reusable contact without turning a GET into a DB update.
        set_committed_value(record, "contractor_phone", contact.whatsapp_phone)


def _hydrate_contact_phones(db: Session, records: list[SelfEmployedAccounting | None]) -> None:
    pending: dict[str, list[SelfEmployedAccounting]] = defaultdict(list)
    for record in records:
        if record is None or record.contractor_phone:
            continue
        digits = re.sub(r"\D", "", str(record.iin or ""))
        if len(digits) == 12:
            pending[digits].append(record)
    if not pending:
        return
    contacts = db.execute(
        select(SelfEmployedContact).where(SelfEmployedContact.iin.in_(list(pending)))
    ).scalars().all()
    for contact in contacts:
        for record in pending.get(contact.iin, []):
            set_committed_value(record, "contractor_phone", contact.whatsapp_phone)


def _remember_contact_phone(
    db: Session,
    record: SelfEmployedAccounting,
    *,
    iin: str | None,
    phone_value: str | None,
) -> None:
    if phone_value is None:
        return
    phone = _phone_digits(phone_value)
    if str(phone_value).strip() and not phone:
        raise HTTPException(status_code=400, detail="Укажите корректный номер WhatsApp самозанятого")
    record.contractor_phone = phone or None
    digits = re.sub(r"\D", "", str(iin or ""))
    if not phone or len(digits) != 12:
        return
    contact = _saved_contact(db, digits)
    now = datetime.utcnow()
    if contact is None:
        contact = SelfEmployedContact(
            iin=digits,
            full_name=record.contractor_full_name,
            whatsapp_phone=phone,
            created_at=now,
            updated_at=now,
        )
    else:
        contact.whatsapp_phone = phone
        if record.contractor_full_name:
            contact.full_name = record.contractor_full_name
        contact.updated_at = now
    db.add(contact)


def _qr_query_value(params: dict[str, list[str]], *aliases: str) -> str | None:
    normalized = {re.sub(r"[^a-z0-9]", "", str(key).lower()): values for key, values in params.items()}
    for alias in aliases:
        values = normalized.get(re.sub(r"[^a-z0-9]", "", alias.lower())) or []
        for value in values:
            digits = re.sub(r"\D", "", str(value or ""))
            if digits:
                return digits
    return None


def _extract_esalyq_qr_ids(value: str | None) -> tuple[str, str] | None:
    """Extract e-Salyq receipt identifiers from old and new QR variants.

    e-Salyq has changed QR generation over time. Older receipts can use a
    different scheme/host/path while still carrying the same stable identifiers.
    We therefore never fetch the raw QR URL. We only extract numeric check_id and
    ip_reg_id, then reconstruct a request to the one trusted KGD endpoint below.
    This keeps SSRF protection while accepting historical e-Salyq receipts.
    """
    if not value or not str(value).strip():
        return None
    raw = unescape(str(value).strip()).replace("\\u0026", "&")

    candidates = [raw]
    # Some scanners wrap an URL in text/JSON. Extract the URL when present.
    url_match = re.search(r"https?://[^\s\"'<>]+", raw, re.I)
    if url_match and url_match.group(0) != raw:
        candidates.insert(0, url_match.group(0))

    for candidate in candidates:
        parsed = urlparse(candidate if "://" in candidate else f"https://{candidate.lstrip('/')}")
        params = parse_qs(parsed.query, keep_blank_values=False)
        check_id = _qr_query_value(params, "check_id", "checkId", "check-id", "checkid")
        ip_reg_id = _qr_query_value(params, "ip_reg_id", "ipRegId", "ip-reg-id", "ipregid", "ip_regid")
        if check_id and ip_reg_id:
            return check_id, ip_reg_id

    # Fallback for QR payloads that are not a conventional URL but still contain
    # the named identifiers (for example a JSON/deeplink payload).
    check_match = re.search(r"check[\s_\-]*id[^0-9]{0,12}(\d{1,24})", raw, re.I)
    ip_match = re.search(r"ip[\s_\-]*reg[\s_\-]*id[^0-9]{0,12}(\d{1,24})", raw, re.I)
    if check_match and ip_match:
        return check_match.group(1), ip_match.group(1)
    return None


def canonical_esalyq_qr(value: str | None) -> str | None:
    """Return a stable official KGD receipt URL for any supported e-Salyq QR.

    The raw QR target is deliberately ignored after the identifiers are parsed.
    The backend always talks only to the fixed KGD host/path, so accepting older
    QR URL variants does not create an SSRF path.
    """
    ids = _extract_esalyq_qr_ids(value)
    if ids is None:
        if not value or not str(value).strip():
            return None
        raise HTTPException(status_code=400, detail="В QR не найдены идентификаторы чека e-Salyq Business")
    check_id, ip_reg_id = ids
    query = urlencode({"check_id": check_id, "ip_reg_id": ip_reg_id})
    return f"https://{KGD_RECEIPT_HOST}{KGD_RECEIPT_PATH}?{query}"


def canonical_kaspi_qr(value: str | None) -> str | None:
    """Validate a Kaspi self-employed QR and rebuild its trusted public URL."""
    if not value or not str(value).strip():
        return None
    parsed = urlparse(unescape(str(value).strip()).replace("\\u0026", "&"))
    if (
        parsed.scheme.lower() != "https"
        or (parsed.hostname or "").lower() != KASPI_RECEIPT_HOST
        or parsed.path.rstrip("/") != KASPI_RECEIPT_PATH
    ):
        raise HTTPException(status_code=400, detail="QR не относится к чеку самозанятого Kaspi")
    params = parse_qs(parsed.query, keep_blank_values=False)
    operation_id = str((params.get("operation_id") or [""])[0]).strip()
    operation_time = str((params.get("operation_time") or [""])[0]).strip()
    if not re.fullmatch(r"\d{6,30}", operation_id):
        raise HTTPException(status_code=400, detail="В QR Kaspi не найден корректный номер операции")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?", operation_time):
        raise HTTPException(status_code=400, detail="В QR Kaspi не найдено корректное время операции")
    query = urlencode({"operation_id": operation_id, "operation_time": operation_time})
    return f"https://{KASPI_RECEIPT_HOST}{KASPI_RECEIPT_PATH}?{query}"


def canonical_receipt_qr(value: str | None) -> str | None:
    """Canonicalize any officially supported self-employed receipt QR."""
    if not value or not str(value).strip():
        return None
    parsed = urlparse(unescape(str(value).strip()).replace("\\u0026", "&"))
    if (parsed.hostname or "").lower() == KASPI_RECEIPT_HOST:
        return canonical_kaspi_qr(value)
    return canonical_esalyq_qr(value)


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
_KK_MONTHS = {
    "қаңтар": 1, "қаңтары": 1, "ақпан": 2, "ақпаны": 2, "наурыз": 3, "наурызы": 3,
    "сәуір": 4, "сәуірі": 4, "мамыр": 5, "мамыры": 5, "маусым": 6, "маусымы": 6,
    "шілде": 7, "шілдесі": 7, "тамыз": 8, "тамызы": 8, "қыркүйек": 9, "қыркүйегі": 9,
    "қазан": 10, "қазаны": 10, "қараша": 11, "қарашасы": 11, "желтоқсан": 12, "желтоқсаны": 12,
}
_OCR_MONTH_ALIASES = {
    # On the e-Salyq font, Tesseract can choose Latin glyphs for the entire
    # Cyrillic word "августа": ``aprycta`` / ``aBrycta``. Keep these aliases
    # limited to the month position inside a full date pattern.
    "aprycta": 8,
    "abrycta": 8,
    "avrycta": 8,
    "avgysta": 8,
    "avgycta": 8,
    "avgusta": 8,
}
_REPORT_MONTHS = {**_RU_MONTHS, **_KK_MONTHS, **_OCR_MONTH_ALIASES}


def _safe_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime | None:
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


_OCR_DATE_TOKEN_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі\d])"
    r"[0-9OОOoоIІil|]{1,4}"
    r"(?![A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі\d])"
)


def _normalize_ocr_date_text(value: str | None) -> str:
    """Repair OCR confusables only inside standalone numeric date/time tokens."""
    text = str(value or "").replace("\xa0", " ")

    def repair(match: re.Match[str]) -> str:
        token = match.group(0)
        if not any(char.isdigit() for char in token):
            return token
        return token.translate(str.maketrans({
            "O": "0", "o": "0", "О": "0", "о": "0",
            "I": "1", "І": "1", "i": "1", "l": "1", "|": "1",
        }))

    return _OCR_DATE_TOKEN_RE.sub(repair, text)


def _parse_report_datetime(text: str) -> datetime | None:
    lower = _normalize_ocr_date_text(text).lower()
    month_names = "|".join(sorted((re.escape(value) for value in _REPORT_MONTHS), key=len, reverse=True))
    match = re.search(
        rf"(?:от\s*)?(\d{{1,2}})\s+({month_names})\s+(20\d{{2}})(?:\s*(?:г(?:ода)?|ж(?:ылғы|ыл)?|[rg])[.,]?)?(?:\s*[,\-]?\s*(\d{{1,2}})[:.](\d{{2}}))?",
        lower,
        re.I,
    )
    if match:
        month = _REPORT_MONTHS.get(match.group(2))
        if month:
            return _safe_datetime(int(match.group(3)), month, int(match.group(1)), int(match.group(4) or 0), int(match.group(5) or 0))
    match = re.search(r"(20\d{2})\s*(?:жылғы|жыл)?\s*(\d{1,2})\s+([а-яёәғқңөұүһі]+)(?:\s*[,\-]?\s*(\d{1,2})[:.](\d{2}))?", lower, re.I)
    if match:
        month = _REPORT_MONTHS.get(match.group(3))
        if month:
            return _safe_datetime(int(match.group(1)), month, int(match.group(2)), int(match.group(4) or 0), int(match.group(5) or 0))
    match = re.search(r"(?<!\d)(\d{1,2})[.\-/](\d{1,2})[.\-/](20\d{2})(?:[^\d]{0,10}(\d{1,2})[:.](\d{2}))?", lower)
    if match:
        return _safe_datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), int(match.group(4) or 0), int(match.group(5) or 0))
    match = re.search(r"(?<!\d)(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})(?:[^\d]{0,10}(\d{1,2})[:.](\d{2}))?", lower)
    if match:
        return _safe_datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4) or 0), int(match.group(5) or 0))
    return None


def _merge_receipt_source_text(*values: str | None) -> str | None:
    parts = [str(value).strip() for value in values if value and str(value).strip()]
    if not parts:
        return None
    return "\n\n".join(dict.fromkeys(parts))[:50000]


def _money_from_text(value: str | None) -> Decimal | None:
    if not value:
        return None
    raw = re.sub(r"[^0-9,.-]", "", str(value))
    if not raw:
        return None

    # KGD reports have used both Russian and machine-oriented money formats:
    # ``100 000,00``, ``100 000.00`` and plain ``100000``.  Treat a final
    # one/two-digit group as decimals and a three-digit group as thousands.
    comma = raw.rfind(",")
    dot = raw.rfind(".")
    separator = max(comma, dot)
    if separator >= 0:
        tail = re.sub(r"\D", "", raw[separator + 1:])
        if 1 <= len(tail) <= 2:
            whole = re.sub(r"\D", "", raw[:separator]) or "0"
            raw = f"{whole}.{tail}"
        else:
            raw = re.sub(r"\D", "", raw)
    else:
        raw = re.sub(r"\D", "", raw)
    try:
        amount = Decimal(raw).quantize(Decimal("0.01")) if raw else None
        return amount if amount is not None and amount > 0 else None
    except InvalidOperation:
        return None


_MONEY_TOKEN_RE = re.compile(
    r"(?<!\d)(\d{1,6}(?:[\s\u00a0\u202f]+\d{3})+(?:[.,]\d{1,2})?|\d{3,}(?:[.,]\d{1,2})?)(?!\d)"
)


def _money_candidates(value: str | None) -> list[Decimal]:
    result: list[Decimal] = []
    for match in _MONEY_TOKEN_RE.finditer(str(value or "")):
        parsed = _money_from_text(match.group(1))
        if parsed is not None:
            result.append(parsed)
    return result


def _parse_esalyq_report_text(raw_text: str) -> dict:
    """Parse the official KGD report text, not pixels from the uploaded image."""
    text = _strip_receipt_system_chars(raw_text)
    text = text.replace("\xa0", " ").replace("\r", "")
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

    # PDF text extraction often separates ``Итого`` and the number into two
    # lines and may omit the tenge sign.  Read a small window around the total
    # label instead of requiring one exact visual layout.
    for index, line in enumerate(lines):
        if not re.search(r"\b(?:Итого|Total)\b", line, re.I):
            continue
        window = " ".join(lines[index:min(len(lines), index + 3)])
        candidates = _money_candidates(window)
        if candidates:
            result["receipt_amount"] = max(candidates)
            break

    if "receipt_amount" not in result:
        currency_candidates: list[Decimal] = []
        for line in lines:
            if re.search(r"(?:₸|тг|тенге|KZT|[TТ]\b)", line, re.I):
                currency_candidates.extend(_money_candidates(line))
        if currency_candidates:
            result["receipt_amount"] = max(currency_candidates)

    def clean_name_fragment(line: str) -> str:
        clean = _strip_receipt_system_chars(line)
        clean = re.sub(r"[^A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі .'-]+", " ", clean)
        return re.sub(r"\s+", " ", clean).strip(" .'-")

    def looks_like_name_fragment(line: str) -> bool:
        clean = re.sub(r"\s+", " ", line or "").strip(" •·")
        if not clean or ":" in clean or "," in clean or re.search(r"\d|режим|налогооблож|самозанят|БИН|BIN|ИП\b|ТОО\b|чек|итого|плат[её]ж|наличн|безналичн|банк|Кбе|ИИК|HSBK|₸|тг", clean, re.I):
            return False
        words = clean.split()
        letters = len(re.findall(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", clean))
        name_case = clean.upper() == clean or all(word[:1].isupper() for word in words)
        return 1 <= len(words) <= 4 and letters >= 3 and name_case

    def looks_like_name(line: str) -> bool:
        words = str(line or "").split()
        return 2 <= len(words) <= 5 and looks_like_name_fragment(line)

    iin_line_index = next((i for i, line in enumerate(lines) if re.search(r"(?:ИИН|IIN|ЖСН)", line, re.I)), -1)
    if iin_line_index >= 0:
        def collect_name(direction: int) -> str | None:
            fragments: list[str] = []
            for offset in range(1, 5):
                idx = iin_line_index + direction * offset
                if idx < 0 or idx >= len(lines):
                    break
                fragment = clean_name_fragment(lines[idx])
                if not looks_like_name_fragment(fragment):
                    if fragments:
                        break
                    continue
                fragments.append(fragment)
            if direction < 0:
                fragments.reverse()
            return clean_person_name(" ".join(fragments))

        candidates = [candidate for candidate in (collect_name(1), collect_name(-1)) if looks_like_name(candidate)]
        if candidates:
            result["contractor_full_name"] = max(candidates, key=lambda candidate: len(candidate.split()))

    total_index = next((i for i, line in enumerate(lines) if re.search(r"^(?:итого|total)\b", line, re.I)), -1)
    payment_index = next((i for i, line in enumerate(lines) if re.search(r"безналичн|наличн|текущ(?:ий)?\s+плат[её]ж|способ\s+оплаты", line, re.I)), -1)

    # The most stable e-Salyq layout puts each service on a line ending with its
    # amount immediately before ``Итого``. Prefer that signal over positional
    # guessing so dates/FIO from shortened KGD reports cannot leak into R-1.
    service_amount_re = re.compile(
        r"\s+(?:\d{1,6}(?:[\s\u00a0\u202f]+\d{3})+|\d{3,})(?:[.,]\d{1,2})?\s*(?:₸|тг|тенге|KZT|[TТ]\b)?.*$",
        re.I,
    )
    service_candidates: list[tuple[int, str]] = []
    scan_end = total_index if total_index > 0 else len(lines)
    for raw_line in lines[:scan_end]:
        has_amount = bool(service_amount_re.search(raw_line))
        if not has_amount:
            continue
        line = clean_service_name(raw_line)
        if not line:
            continue
        if re.search(r"(?:ИИН|IIN|ЖСН|БИН|BIN|чек|receipt|итого|режим\s+налогооблож|самозанят|ИП\b|плат[её]ж|наличн|безналичн)", line, re.I):
            continue
        if len(re.findall(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", line)) >= 3:
            service_candidates.append((_service_text_score(line) + 40, line))

    if not service_candidates:
        if payment_index >= 0:
            end = total_index if total_index > payment_index else min(len(lines), payment_index + 8)
            candidates = lines[payment_index + 1:end]
        elif total_index > 0:
            candidates = lines[max(0, total_index - 6):total_index]
        else:
            candidates = []
        for raw_line in candidates:
            line = clean_service_name(raw_line)
            if not line:
                continue
            if re.search(r"(?:ИИН|IIN|ЖСН|БИН|BIN|чек|receipt|итого|режим\s+налогооблож|самозанят|ИП\b)", line, re.I):
                continue
            # In fallback mode reject obvious date and person-name lines.
            if _parse_report_datetime(line) is not None or looks_like_name(line):
                continue
            if len(re.findall(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", line)) >= 3:
                service_candidates.append((_service_text_score(line), line))
    if service_candidates:
        result["service_name"] = max(service_candidates, key=lambda item: item[0])[1]

    exact_iin = _extract_iin_from_text(joined, str(R1_CUSTOMER_PROFILE.get("bin_iin") or ""))
    if exact_iin:
        result["iin"] = exact_iin
    exact_number = clean_receipt_number(_extract_receipt_number_from_text(joined))
    if exact_number:
        result["receipt_number"] = exact_number
    exact_name = clean_person_name(_extract_unicode_name_from_text(joined))
    if exact_name:
        result["contractor_full_name"] = prefer_full_person_name(result.get("contractor_full_name"), exact_name)
    if result.get("receipt_number"):
        result["receipt_number"] = clean_receipt_number(result["receipt_number"])

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
        or first_value(("номер", "чек"))
        or first_value(("№", "чек"))
    )
    if receipt_number is not None:
        cleaned_number = clean_receipt_number(str(receipt_number))
        if cleaned_number:
            result["receipt_number"] = cleaned_number

    iin_candidates = []
    for path, value in rows:
        normalized_path = re.sub(r"[^a-zа-яёәғқңөұүһі0-9]", "", path.casefold())
        if not any(token in normalized_path for token in ("iin", "iinbin", "biniin", "иин", "жсн")):
            continue
        digits = re.sub(r"\D", "", str(value or ""))
        if len(digits) == 12 and digits != str(R1_CUSTOMER_PROFILE.get("bin_iin") or ""):
            if any(token in normalized_path for token in ("customer", "buyer", "payer", "покупател", "плательщик", "төлеуші")):
                continue
            priority = 0 if any(token in normalized_path for token in ("seller", "executor", "taxpayer", "individual", "person", "самозанят", "сатушы")) else 1
            iin_candidates.append((priority, digits))
    if iin_candidates:
        result["iin"] = sorted(iin_candidates, key=lambda item: item[0])[0][1]

    name_candidates: list[tuple[int, str]] = []
    for path, value in rows:
        if not isinstance(value, str) or not value.strip():
            continue
        normalized_path = re.sub(r"[^a-zа-яёәғқңөұүһі0-9]", "", path.casefold())
        if any(token in normalized_path for token in ("customer", "buyer", "payer", "покупател", "плательщик", "төлеуші")):
            continue
        is_name = any(token in normalized_path for token in ("fullname", "fio", "фио", "атыжөні", "атыжони"))
        is_party_name = "name" in normalized_path and any(
            token in normalized_path for token in ("seller", "executor", "taxpayer", "individual", "person")
        )
        if not (is_name or is_party_name):
            continue
        cleaned = clean_person_name(value)
        if not cleaned or "contrast event" in cleaned.casefold():
            continue
        priority = 0 if any(token in normalized_path for token in ("seller", "executor", "taxpayer", "самозанят", "сатушы")) else 1
        name_candidates.append((priority, cleaned))
    if name_candidates:
        best_priority = min(item[0] for item in name_candidates)
        best_names = [item[1] for item in name_candidates if item[0] == best_priority]
        result["contractor_full_name"] = max(best_names, key=lambda value: (len(re.findall(r"[ӘәҒғҚқҢңӨөҰұҮүҺһІі]", value)), len(value.split()), len(value)))

    amount_candidates: list[tuple[int, Decimal]] = []
    for path, value in rows:
        if value in {None, ""}:
            continue
        normalized_path = re.sub(r"[^a-z0-9]", "", path)
        if not any(token in normalized_path for token in ("amount", "sum", "total", "price")):
            continue
        if any(token in normalized_path for token in ("tax", "vat", "discount", "change", "unitprice")):
            continue
        parsed_amount = _money_from_text(str(value))
        if parsed_amount is None:
            continue
        score = 0
        if "total" in normalized_path:
            score += 50
        if "check" in normalized_path or "receipt" in normalized_path:
            score += 25
        if "payment" in normalized_path:
            score += 15
        amount_candidates.append((score, parsed_amount))
    if amount_candidates:
        result["receipt_amount"] = max(amount_candidates, key=lambda item: (item[0], item[1]))[1]

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

    service_candidates: list[tuple[int, str]] = []
    for path, value in rows:
        if not isinstance(value, str) or not value.strip():
            continue
        normalized_path = re.sub(r"[^a-z0-9]", "", path)
        service_path = any(token in normalized_path for token in ("service", "item", "product", "goods", "commodity", "work"))
        operation_path = "operation" in normalized_path and any(token in normalized_path for token in ("name", "title", "description"))
        description_path = "description" in normalized_path
        if not (service_path or operation_path or description_path):
            continue
        cleaned = clean_service_name(value)
        if not cleaned or len(re.findall(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", cleaned)) < 3:
            continue
        score = _service_text_score(cleaned)
        if service_path:
            score += 35
        if any(token in normalized_path for token in ("name", "title")):
            score += 25
        if description_path and not service_path:
            score -= 20
        service_candidates.append((score, cleaned))
    if service_candidates:
        result["service_name"] = max(service_candidates, key=lambda item: item[0])[1]

    # JSON reports often contain human-readable labels too. Feeding a flattened
    # representation through the text parser covers variants without hardcoding
    # every historical backend key name.
    human_values: list[str] = []
    for _path, value in rows:
        if not isinstance(value, str) or not value.strip():
            continue
        text_value = _strip_html_to_text(value) if "<" in value and ">" in value else value
        human_values.append(text_value)
    flattened_text = "\n".join(human_values)
    text_result = _parse_esalyq_report_text(flattened_text)
    for key, value in text_result.items():
        result.setdefault(key, value)

    # Legal receipt fields must come from receipt-specific keys, never from a
    # generic response/create timestamp or arbitrary numeric ID in the KGD JSON.
    result.pop("receipt_datetime", None)
    exact_datetime = _find_json_receipt_datetime(__import__(__name__, fromlist=["*"]), payload)
    if exact_datetime:
        result["receipt_datetime"] = exact_datetime
    exact_name = clean_person_name(_extract_json_unicode_name(__import__(__name__, fromlist=["*"]), payload))
    if exact_name:
        result["contractor_full_name"] = prefer_full_person_name(result.get("contractor_full_name"), exact_name)
    exact_iin = _extract_json_iin(__import__(__name__, fromlist=["*"]), payload)
    if exact_iin:
        result["iin"] = exact_iin
    exact_number = clean_receipt_number(_extract_json_receipt_number(__import__(__name__, fromlist=["*"]), payload))
    if exact_number:
        result["receipt_number"] = exact_number
    if result.get("contractor_full_name"):
        result["contractor_full_name"] = clean_person_name(result["contractor_full_name"])
    if result.get("receipt_number"):
        result["receipt_number"] = clean_receipt_number(result["receipt_number"])
    if result.get("service_name"):
        result["service_name"] = clean_service_name(result["service_name"])
    return result


def _kgd_response_payload(response: requests.Response) -> tuple[dict, str]:
    content_type = (response.headers.get("content-type") or "").lower()
    raw = response.content or b""
    # Some historical KGD gateways returned JSON with ``text/plain`` or
    # ``application/octet-stream``.  Detect JSON by the body too; otherwise the
    # machine keys leak into the visible service text and amount fields remain
    # empty even though the payload contains them.
    stripped = raw.lstrip()
    if "json" in content_type or stripped.startswith((b"{", b"[")):
        try:
            encoding = response.encoding or "utf-8"
            payload = json.loads(raw.decode(encoding, errors="replace"))
        except (ValueError, UnicodeDecodeError):
            payload = None
        if payload is not None:
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
                "User-Agent": "ContrastFinance/0.5.89 (+e-Salyq receipt verification)",
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
    parsed["source"] = "kgd_qr"
    return parsed


def _nuxt_reference(values: list, value):
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value < len(values):
        return values[value]
    return value


def _parse_kaspi_receipt_html(source: str) -> dict:
    match = re.search(
        r"<script\b[^>]*\bid=[\"']__NUXT_DATA__[\"'][^>]*>(.*?)</script>",
        source or "",
        flags=re.I | re.S,
    )
    if not match:
        raise HTTPException(status_code=502, detail="Kaspi вернул чек без структурированных данных")
    try:
        values = json.loads(unescape(match.group(1)))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Не удалось разобрать данные официального чека Kaspi") from exc
    if not isinstance(values, list):
        raise HTTPException(status_code=502, detail="Kaspi вернул неизвестный формат чека")

    receipt = next((
        value for value in values
        if isinstance(value, dict) and {"header", "amount", "cartItems", "payParameters"}.issubset(value)
    ), None)
    if receipt is None:
        raise HTTPException(status_code=502, detail="В ответе Kaspi не найдена карточка чека")

    item_names: list[str] = []
    items_value = _nuxt_reference(values, receipt.get("cartItems"))
    if isinstance(items_value, list):
        for item_ref in items_value:
            item = _nuxt_reference(values, item_ref)
            if not isinstance(item, dict):
                continue
            cleaned = clean_service_name(str(_nuxt_reference(values, item.get("item_name")) or ""))
            if cleaned:
                item_names.append(cleaned)

    parameters: dict[str, str] = {}
    parameters_value = _nuxt_reference(values, receipt.get("payParameters"))
    if isinstance(parameters_value, list):
        for parameter_ref in parameters_value:
            parameter = _nuxt_reference(values, parameter_ref)
            if not isinstance(parameter, dict):
                continue
            name = _strip_html_to_text(str(_nuxt_reference(values, parameter.get("name")) or ""))
            value = _strip_html_to_text(str(_nuxt_reference(values, parameter.get("value")) or ""))
            if name and value:
                parameters[re.sub(r"\s+", " ", name).strip().casefold()] = value

    amount_text = str(_nuxt_reference(values, receipt.get("amount")) or "")
    parsed = {
        "contractor_full_name": None,
        "iin": clean_iin(parameters.get("иин самозанятого") or parameters.get("жсн самозанятого")),
        "receipt_number": clean_receipt_number(parameters.get("№ чека") or parameters.get("номер чека")),
        "receipt_datetime": _parse_report_datetime(parameters.get("дата и время по астане", "")),
        "service_name": clean_service_name("; ".join(dict.fromkeys(item_names))),
        "receipt_amount": _money_from_text(amount_text),
    }
    useful = [
        parsed.get("iin"), parsed.get("receipt_number"), parsed.get("receipt_datetime"),
        parsed.get("service_name"), parsed.get("receipt_amount"),
    ]
    if sum(value not in {None, ""} for value in useful) < 4:
        raise HTTPException(status_code=502, detail="Официальный чек Kaspi получен, но в нём не хватает основных полей")
    parsed["parse_confidence"] = Decimal("100.00")
    parsed["source"] = "kaspi_qr"
    parsed["source_text"] = json.dumps(
        {"header": "Чек самозанятого Kaspi", "items": item_names, "parameters": parameters, "amount": amount_text},
        ensure_ascii=False,
    )[:50000]
    return parsed


def resolve_kaspi_qr(qr_payload: str) -> dict:
    canonical = canonical_kaspi_qr(qr_payload)
    if not canonical:
        raise HTTPException(status_code=400, detail="QR чека Kaspi не найден")
    try:
        response = requests.get(
            canonical,
            timeout=KASPI_RECEIPT_TIMEOUT,
            allow_redirects=True,
            headers={
                "User-Agent": "ContrastFinance/0.5.111 (+Kaspi self-employed receipt verification)",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
            },
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Не удалось получить официальный чек Kaspi по QR. Попробуйте позже") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Kaspi не отдал чек по QR (HTTP {response.status_code})")
    final = urlparse(response.url)
    if final.scheme.lower() != "https" or (final.hostname or "").lower() != KASPI_RECEIPT_HOST:
        raise HTTPException(status_code=502, detail="Kaspi перенаправил QR на неизвестный адрес")
    encoding = response.encoding or "utf-8"
    parsed = _parse_kaspi_receipt_html((response.content or b"").decode(encoding, errors="replace"))
    parsed["qr_payload"] = canonical
    return parsed


def resolve_receipt_qr(qr_payload: str) -> dict:
    canonical = canonical_receipt_qr(qr_payload)
    if not canonical:
        raise HTTPException(status_code=400, detail="QR чека не найден")
    if (urlparse(canonical).hostname or "").lower() == KASPI_RECEIPT_HOST:
        return resolve_kaspi_qr(canonical)
    return resolve_esalyq_qr(canonical)


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
            canonical_qr = canonical_receipt_qr(qr_payload)
        except HTTPException:
            canonical_qr = str(qr_payload).strip()[:10000]
    if canonical_qr:
        query = select(SelfEmployedAccounting.id).where(SelfEmployedAccounting.qr_payload == canonical_qr)
        if exclude_id is not None:
            query = query.where(SelfEmployedAccounting.id != int(exclude_id))
        duplicate = db.execute(query.limit(1)).scalar_one_or_none()
        if duplicate is not None:
            return int(duplicate)
    number = clean_receipt_number(receipt_number)
    normalized_iin = re.sub(r"\D", "", str(iin or ""))
    if number and len(normalized_iin) == 12:
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


ACT_MUTABLE_STATUSES = {None, "", "not_created", "generated"}


def _assert_act_mutable(record: SelfEmployedAccounting) -> None:
    """Generated drafts may be replaced; signature workflow states are immutable."""
    if record.act_status not in ACT_MUTABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Нельзя менять данные после отправки АВР на подпись")


def _discard_generated_act(record: SelfEmployedAccounting) -> None:
    """Drop only an unsigned draft when its source receipt/group changes."""
    if record.act_status != "generated":
        return
    record.act_status = "not_created"
    record.act_number = None
    record.act_date = None
    record.act_filename = None
    record.act_content_type = None
    record.act_size = None
    record.act_sha256 = None
    record.act_data = None
    record.act_generated_at = None
    record.act_generated_by_user_id = None
    record.act_ddc_status = "pending"
    record.act_ddc_filename = None
    record.act_ddc_size = None
    record.act_ddc_sha256 = None
    record.act_ddc_data = None
    record.act_ddc_generated_at = None
    record.act_ddc_last_attempt_at = None
    record.act_ddc_error = None


def clean_text(value: str | None, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).replace("\x00", " ").split()).strip()
    if not cleaned:
        return None
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def _strip_receipt_system_chars(value: object) -> str:
    """Remove scanner/control artefacts while preserving normal receipt text."""
    source = unescape(str(value or ""))
    cleaned: list[str] = []
    for char in source:
        category = unicodedata.category(char)
        if char in {"\n", "\t"}:
            cleaned.append(char)
        elif category not in {"Cc", "Cf", "Cs", "Co", "Cn"} and char != "�":
            cleaned.append(char)
    return "".join(cleaned)


def clean_person_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _strip_receipt_system_chars(value)
    cleaned = re.sub(r"^\s*(?:ФИО|FIO|ИП|исполнитель|самозанятый)\s*[:№#-]*\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[^A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі .'-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .'-")
    if not cleaned:
        return None
    words = [word for word in cleaned.split() if re.search(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", word)]
    if len(words) < 2:
        return None
    return " ".join(words)[:255]


def prefer_full_person_name(primary: str | None, visual: str | None) -> str | None:
    """Prefer the most complete spelling without crossing contractor identities."""
    official = clean_person_name(primary)
    fallback = clean_person_name(visual)
    if not official:
        return fallback
    if not fallback:
        return official
    official_words = official.casefold().split()
    fallback_words = fallback.casefold().split()
    if official_words[0] != fallback_words[0]:
        return official

    kazakh_map = str.maketrans("әғқңөұүһі", "агкноууhi")
    def comparable(value: str) -> str:
        return re.sub(r"[^a-zа-яё]", "", value.casefold().translate(kazakh_map))

    similarity = SequenceMatcher(None, comparable(official), comparable(fallback)).ratio()
    if similarity < 0.64:
        return official

    def quality(value: str) -> tuple[int, int, int]:
        kazakh_letters = len(re.findall(r"[ӘәҒғҚқҢңӨөҰұҮүҺһІі]", value))
        words = len(value.split())
        letters = len(re.findall(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", value))
        return (kazakh_letters, words, letters)

    return fallback if quality(fallback) > quality(official) else official


def clean_receipt_number(value: str | None) -> str | None:
    if not value:
        return None
    source = str(value).replace("О", "0").replace("O", "0")
    compact = re.sub(r"[\s-]+", "", source)
    for candidate in re.findall(r"\d{12,24}", compact):
        if len(candidate) == 12:
            return candidate
        suffix = candidate[-12:]
        if suffix.startswith("0"):
            return suffix
    return None


def clean_service_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _strip_receipt_system_chars(value)
    cleaned = re.sub(r"^\s*(?:услуга|service|наименование(?:\s+работы)?|description)\s*[:#-]*\s*", "", cleaned, flags=re.I)
    # A receipt is a visual table. OCR may concatenate the left service cell,
    # the right amount cell and fragments from the following column. Preserve
    # meaningful words on both sides of the amount, then cut scanner garbage.
    cleaned = re.split(r"\s*[|¦]\s*", cleaned, maxsplit=1)[0]
    cleaned = re.sub(r"[¬`~^{}\[\]<>\\]+", " ", cleaned)
    cleaned = re.sub(
        r"(?<!\d)\d{1,6}(?:[\s\u00a0\u202f]+\d{3})+(?:[.,]\d{1,2})?\s*(?:₸|тг|тенге|KZT|[TТ]\b)?",
        " ",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\s+(?:I{1,4}|IV|V|VI|L)\s*[\"'“”«].*$", "", cleaned, flags=re.I)
    cleaned = re.split(r"\b(?:ИИН|IIN|ЖСН|БИН|BIN|Итого|Total|Чек\s*[№N#])\b", cleaned, maxsplit=1, flags=re.I)[0]
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;_-—")
    if not cleaned:
        return None

    months = r"январ[ья]|феврал[ья]|март[а]?|апрел[ья]|ма[йя]|июн[ья]|июл[ья]|август[а]?|сентябр[ья]|октябр[ья]|ноябр[ья]|декабр[ья]"
    # KGD JSON has generic ``description`` fields. A date description such as
    # ``от 28 августа`` is metadata, never a service name.
    if re.fullmatch(
        rf"(?:от\s+)?\d{{1,2}}\s+(?:{months})(?:\s+20\d{{2}}(?:\s*г(?:ода)?[.]?)?)?(?:\s*[,;]\s*\d{{1,2}}:\d{{2}})?",
        cleaned,
        flags=re.I,
    ):
        return None

    # The work-name cell on e-Salyq contains text only. A long service may
    # visually overlap the amount column and OCR can return fragments such as
    # ``с 1 2 ( водителем``. Strip every numeric/currency remnant while
    # preserving the words on both sides of it.
    cleaned = re.sub(r"\d+", " ", cleaned)
    cleaned = re.sub(r"(?:₸|%|№|#|=|\*)", " ", cleaned)
    cleaned = re.sub(r"\b(?:тг|тенге|KZT)\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"(?:^|\s)[TТ](?=\s|$|[.,;:])", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"[()\[\]{}<>]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;_-—")
    if not cleaned:
        return None
    if re.match(
        r"^(?:для\s+юридическ|режим\s+налогооблож|специальн\w*\s+налогов|безналичн|наличн|текущ\w*\s+плат[её]ж|способ\s+оплаты|чек\b|receipt\b|итого\b|total\b)",
        cleaned,
        flags=re.I,
    ):
        return None
    return cleaned


def _service_text_score(value: str | None) -> int:
    text = str(value or "")
    letters = len(re.findall(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", text))
    cyrillic = len(re.findall(r"[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", text))
    singletons = len([word for word in text.split() if len(re.sub(r"\W", "", word)) == 1])
    symbols = len(re.findall(r"[^\w\s.,:;()/'&+\-—]", text, re.UNICODE))
    return letters + cyrillic - singletons * 7 - symbols * 5


def clean_iin(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return None
    if len(digits) != 12:
        raise HTTPException(status_code=400, detail="ИИН должен содержать 12 цифр")
    return digits


def _person_identity_key(value: str | None) -> str:
    cleaned = clean_person_name(value)
    return re.sub(r"[^a-zа-яёәғқңөұүһі]", "", (cleaned or "").casefold())


def _valid_iin_or_none(value: object) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if len(digits) == 12 else None


def _restore_missing_iins_from_exact_names(
    records: list[SelfEmployedAccounting],
) -> list[SelfEmployedAccounting]:
    """Fill missing IINs only when one full normalized name maps to one IIN."""
    iins_by_name: dict[str, set[str]] = defaultdict(set)
    for historical in records:
        name_key = _person_identity_key(historical.contractor_full_name)
        iin = _valid_iin_or_none(historical.iin)
        if name_key and iin:
            iins_by_name[name_key].add(iin)

    changed: list[SelfEmployedAccounting] = []
    changed_at: datetime | None = None
    for record in records:
        if _valid_iin_or_none(record.iin):
            continue
        name_key = _person_identity_key(record.contractor_full_name)
        matches = iins_by_name.get(name_key, set()) if name_key else set()
        if len(matches) != 1:
            continue
        changed_at = changed_at or datetime.utcnow()
        record.iin = next(iter(matches))
        record.updated_at = changed_at
        changed.append(record)
    return changed


def _restore_receipt_identity(db: Session, record: SelfEmployedAccounting) -> None:
    """Reuse only unambiguous identity data from receipts of the same person."""
    current_name = clean_person_name(record.contractor_full_name)
    current_iin = _valid_iin_or_none(record.iin)
    historical = db.execute(
        select(
            SelfEmployedAccounting.id,
            SelfEmployedAccounting.iin,
            SelfEmployedAccounting.contractor_full_name,
        ).where(SelfEmployedAccounting.id != record.id)
    ).all()

    if current_iin is None and current_name:
        name_key = _person_identity_key(current_name)
        matching_iins = {
            _valid_iin_or_none(iin)
            for _record_id, iin, full_name in historical
            if iin and _person_identity_key(full_name) == name_key
        }
        matching_iins.discard(None)
        if len(matching_iins) == 1:
            current_iin = next(iter(matching_iins))
            record.iin = current_iin

    if current_iin:
        names = [current_name] if current_name else []
        names.extend(
            clean_person_name(full_name)
            for _record_id, iin, full_name in historical
            if iin and _valid_iin_or_none(iin) == current_iin and full_name
        )
        contact = _saved_contact(db, current_iin)
        if contact and contact.full_name:
            names.append(clean_person_name(contact.full_name))
        best_name: str | None = None
        for candidate in (name for name in names if name):
            best_name = prefer_full_person_name(best_name, candidate)
        if best_name:
            record.contractor_full_name = best_name
            if contact and contact.full_name != best_name:
                contact.full_name = best_name
                contact.updated_at = datetime.utcnow()
                db.add(contact)


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
    signatures = {item.signer_role: item for item in (record.act_signatures if record else [])}

    def party(role: str) -> SelfEmployedActPartyRead:
        signature = signatures.get(role)
        return SelfEmployedActPartyRead(
            status=signature.status if signature else "not_sent",
            sent_at=signature.sent_at if signature else None,
            signed_at=signature.signed_at if signature else None,
            signer_iin=signature.signer_iin if signature else None,
        )

    return {
        "receipt_filename": record.receipt_filename if record else None,
        "receipt_content_type": record.receipt_content_type if record else None,
        "receipt_size": record.receipt_size if record else None,
        "receipt_sha256": record.receipt_sha256 if record else None,
        "receipt_uploaded_at": record.receipt_uploaded_at if record else None,
        "has_receipt": bool(record and record.receipt_filename and record.receipt_size),
        "contractor_full_name": record.contractor_full_name if record else None,
        "contractor_phone": record.contractor_phone if record else None,
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
        "act_number": record.act_number if record else None,
        "act_date": record.act_date if record else None,
        "act_size": record.act_size if record else None,
        "act_generated_at": record.act_generated_at if record else None,
        "has_act": bool(record and record.act_filename and record.act_size),
        "has_signed_act": bool(
            record
            and record.act_ddc_status == "ready"
            and record.act_ddc_filename
            and record.act_ddc_size
        ),
        "act_ddc_status": record.act_ddc_status if record else "pending",
        "act_ddc_size": record.act_ddc_size if record else None,
        "act_ddc_generated_at": record.act_ddc_generated_at if record else None,
        "act_ddc_error": record.act_ddc_error if record else None,
        "act_session_status": record.act_session_status if record else None,
        "act_signing_error": record.act_signing_error if record else None,
        "customer_signature": party("customer"),
        "contractor_signature": party("contractor"),
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
    _hydrate_contact_phone(db, record)
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
        return False
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
    include_undated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)

    # Repair old rows too, not only the receipt currently being uploaded. A
    # full exact-name match is safe for repeat contractors; conflicting IINs
    # for the same name deliberately leave the target untouched.
    identity_records = db.execute(
        select(SelfEmployedAccounting).where(
            SelfEmployedAccounting.contractor_full_name.is_not(None)
        )
    ).scalars().all()
    recovered_iins = _restore_missing_iins_from_exact_names(identity_records)
    if recovered_iins:
        for record in recovered_iins:
            db.add(record)
        db.commit()

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

    _hydrate_contact_phones(db, list(records.values()))
    result = [build_row(members, records.get(key)) for key, members in grouped_members.items()]

    if month_bounds:
        # A real e-Salyq receipt date is the source of truth for accounting
        # period. Rows still waiting for a receipt remain discoverable by event
        # month so the accountant can attach the future receipt.
        result = [
            row for row in result
            if _row_matches_accounting_month(row, month_bounds)
            or (include_undated and row.has_receipt and not row.receipt_datetime)
        ]

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
    _hydrate_contact_phones(db, list(standalone_records))
    for record in standalone_records:
        if month_bounds:
            # Never invent a legal accounting period from upload/create time.
            # Undated checks stay visible only as an explicit repair queue.
            if record.receipt_datetime is None and not include_undated:
                continue
            if record.receipt_datetime and not (month_bounds[0] <= record.receipt_datetime.date() < month_bounds[1]):
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
    if destination is not None:
        _assert_act_mutable(destination)
        _discard_generated_act(destination)
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
    _assert_act_mutable(record)
    _discard_generated_act(record)
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
    record.contractor_full_name = clean_person_name(contractor_full_name)
    record.iin = clean_iin(iin)
    record.receipt_number = clean_receipt_number(receipt_number)
    record.receipt_datetime = clean_datetime(receipt_datetime) or _parse_report_datetime(ocr_text or "")
    record.service_name = clean_service_name(service_name)
    record.receipt_amount = clean_decimal(receipt_amount)
    record.qr_payload = canonical_receipt_qr(qr_payload) if qr_payload else None
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
    iin: str | None,
    receipt_amount: Decimal | None,
) -> tuple[SelfEmployedAccounting | None, str, list[int]]:
    surname = _surname_key(contractor_full_name)
    normalized_iin = clean_iin(iin)
    if receipt_amount is None:
        return None, "unmatched", []

    amount_matches: list[tuple[list[PaymentRequest], SelfEmployedAccounting | None]] = []
    identity_matches: list[tuple[list[PaymentRequest], SelfEmployedAccounting | None]] = []
    for requests, record in _unreceipted_candidate_groups(db):
        total = sum((Decimal(request.amount_requested) for request in requests), Decimal("0.00")).quantize(Decimal("0.01"))
        if total != receipt_amount:
            continue
        amount_matches.append((requests, record))
        candidate_iins = {
            clean_iin(value)
            for value in [getattr(record, "iin", None), *(request.iin_bin_snapshot for request in requests)]
            if value
        }
        candidate_iins.discard(None)
        request_surnames = {_surname_key(request.contractor_name_snapshot) for request in requests}
        request_surnames.discard(None)
        if (normalized_iin and normalized_iin in candidate_iins) or (surname and surname in request_surnames):
            identity_matches.append((requests, record))

    matches = identity_matches or (amount_matches if not surname and not normalized_iin else [])

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
    parsed = resolve_receipt_qr(payload.qr_payload)
    source = parsed.get("source") or "kgd_qr"
    return SelfEmployedReceiptQrResolveRead(
        contractor_full_name=parsed.get("contractor_full_name"),
        iin=parsed.get("iin"),
        receipt_number=parsed.get("receipt_number"),
        receipt_datetime=parsed.get("receipt_datetime"),
        service_name=parsed.get("service_name"),
        receipt_amount=parsed.get("receipt_amount"),
        qr_payload=parsed["qr_payload"],
        parse_confidence=parsed.get("parse_confidence", Decimal("100.00")),
        source=source,
        message=(
            "Данные получены из официального чека Kaspi по QR"
            if source == "kaspi_qr" else "Данные получены из официального чека КГД по QR"
        ),
        source_text=parsed.get("source_text"),
    )


@router.post("/receipts/{accounting_id}/refresh-qr", response_model=SelfEmployedAccountingRead)
def refresh_accounting_receipt_from_qr(
    accounting_id: int,
    payload: SelfEmployedReceiptQrRefreshCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-read one stored receipt using KGD plus visual receipt fields.

    Historical e-Salyq QR codes may no longer resolve.  In that case the same
    endpoint accepts the browser's zone-aware visual recognition instead of
    refusing to repair the stored receipt.
    """
    require_accounting_access(current_user)
    record = get_record_or_404(db, accounting_id, lock=True)
    _assert_act_mutable(record)
    _discard_generated_act(record)
    qr_payload = payload.qr_payload or record.qr_payload
    official: dict = {}
    canonical_qr: str | None = None
    if qr_payload:
        try:
            canonical_qr = canonical_receipt_qr(qr_payload)
            # The browser refresh first resolves the QR, then visually verifies
            # the same receipt. Do not request the identical KGD report again
            # when the resulting official fields are already in this payload.
            if not payload.kgd_resolved:
                official = resolve_receipt_qr(canonical_qr)
        except HTTPException:
            # The pixels remain a valid accounting source even when an old KGD
            # link is unavailable. Fresh zone OCR fields are applied below.
            official = {}

    assert_receipt_metadata_unique(
        db,
        exclude_id=record.id,
        qr_payload=official.get("qr_payload") or canonical_qr,
        receipt_number=official.get("receipt_number") or payload.receipt_number,
        iin=official.get("iin") or payload.iin,
    )

    official_source = official.get("source") or (
        "kaspi_qr" if canonical_qr and (urlparse(canonical_qr).hostname or "").lower() == KASPI_RECEIPT_HOST else "kgd_qr"
    )
    record.contractor_full_name = prefer_full_person_name(
        official.get("contractor_full_name"),
        payload.contractor_full_name or record.contractor_full_name,
    )
    record.iin = clean_iin(official.get("iin") or payload.iin or record.iin)
    record.receipt_number = (
        clean_receipt_number(official.get("receipt_number"))
        or clean_receipt_number(payload.receipt_number)
        or clean_receipt_number(record.receipt_number)
    )
    combined_source_text = _merge_receipt_source_text(payload.ocr_text, official.get("source_text"), record.ocr_text)
    selected_dt = (
        official.get("receipt_datetime")
        or payload.receipt_datetime
        or _parse_report_datetime(combined_source_text or "")
        or record.receipt_datetime
    )
    record.receipt_datetime = selected_dt.replace(tzinfo=None) if isinstance(selected_dt, datetime) else clean_datetime(selected_dt)
    if official_source == "kaspi_qr":
        record.service_name = (
            clean_service_name(official.get("service_name"))
            or clean_service_name(payload.service_name)
            or clean_service_name(record.service_name)
        )
    else:
        record.service_name = (
            clean_service_name(payload.service_name)
            or clean_service_name(official.get("service_name"))
            or clean_service_name(record.service_name)
        )
    selected_amount = official.get("receipt_amount")
    if selected_amount is None:
        selected_amount = payload.receipt_amount if payload.receipt_amount is not None else record.receipt_amount
    record.receipt_amount = clean_decimal(selected_amount)
    record.qr_payload = official.get("qr_payload") or canonical_qr or record.qr_payload
    record.ocr_text = combined_source_text
    record.parse_confidence = Decimal(
        official.get("parse_confidence")
        or payload.parse_confidence
        or (Decimal("80.00") if payload.ocr_text else Decimal("50.00"))
    )
    record.parse_status = "parsed"
    record.confirmed_at = None
    record.confirmed_by_user_id = None
    record.updated_at = datetime.utcnow()
    _restore_receipt_identity(db, record)
    db.add(record)
    db.commit()
    return load_accounting_row(db, record.id)


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
            official = resolve_receipt_qr(qr_payload)
            contractor_full_name = prefer_full_person_name(official.get("contractor_full_name"), contractor_full_name)
            iin = official.get("iin") or iin
            receipt_number = official.get("receipt_number") or receipt_number
            official_dt = official.get("receipt_datetime")
            receipt_datetime = official_dt.isoformat() if isinstance(official_dt, datetime) else (official_dt or receipt_datetime)
            if official.get("source") == "kaspi_qr":
                service_name = clean_service_name(official.get("service_name")) or clean_service_name(service_name)
            else:
                service_name = clean_service_name(service_name) or clean_service_name(official.get("service_name"))
            official_amount = official.get("receipt_amount")
            receipt_amount = str(official_amount) if official_amount is not None else receipt_amount
            qr_payload = official.get("qr_payload") or qr_payload
            parse_confidence = str(official.get("parse_confidence", Decimal("100.00")))
            # Preserve both the visual OCR and the official response. When QR
            # omits the date, the server can still recover it from the header.
            ocr_text = _merge_receipt_source_text(ocr_text, official.get("source_text"))
        except HTTPException as exc:
            try:
                qr_payload = canonical_receipt_qr(qr_payload)
            except HTTPException:
                qr_payload = None
            qr_error = str(exc.detail)

    assert_receipt_metadata_unique(
        db,
        qr_payload=qr_payload,
        receipt_number=receipt_number,
        iin=iin,
    )

    normalized_amount = clean_decimal(receipt_amount)
    record, match_status, matched_ids = _auto_match_receipt(db, contractor_full_name, iin, normalized_amount)
    if record is None:
        record = create_standalone_record(db)
    elif not contractor_full_name and matched_ids:
        matched_name = db.execute(
            select(PaymentRequest.contractor_name_snapshot)
            .where(PaymentRequest.id.in_(matched_ids), PaymentRequest.contractor_name_snapshot.is_not(None))
            .order_by(PaymentRequest.id)
            .limit(1)
        ).scalar_one_or_none()
        contractor_full_name = clean_person_name(matched_name)

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
    _restore_receipt_identity(db, record)
    db.add(record)
    db.commit()

    receipt_source = "Kaspi" if qr_payload and (urlparse(qr_payload).hostname or "").lower() == KASPI_RECEIPT_HOST else "КГД"
    if qr_error:
        message = f"Чек сохранён, QR найден, но официальные данные не получены: {qr_error}"
    elif match_status == "matched":
        message = f"Чек проверен по QR {receipt_source} и автоматически привязан к заявке{'м' if len(matched_ids) > 1 else ''} №" + ", №".join(str(i) for i in matched_ids)
    elif match_status == "ambiguous":
        message = f"Чек проверен по QR {receipt_source}. Есть несколько подходящих заявок — оставлен отдельной строкой"
    else:
        message = f"Чек проверен по QR {receipt_source}. Точного совпадения данных и суммы нет — создан отдельной строкой" if qr_payload else "QR не найден: чек создан отдельной строкой по резервному распознаванию"
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
    _assert_act_mutable(target)
    _discard_generated_act(target)

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
        _assert_act_mutable(source)
        _discard_generated_act(source)
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
    _assert_act_mutable(target)
    _discard_generated_act(target)
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


@router.delete("/requests/{request_id}")
def hide_self_employed_request_from_accounting(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove one request from Accounting without deleting it from the event."""
    require_accounting_access(current_user)
    request, _ = get_request_or_404(
        db,
        request_id,
        require_active=False,
        require_visible=True,
    )
    request = db.execute(
        select(PaymentRequest)
        .where(PaymentRequest.id == request.id)
        .with_for_update()
    ).scalar_one()

    target = find_record_for_request(db, request.id)
    standalone_receipt_id: int | None = None
    if target is not None:
        target = get_record_or_404(db, target.id, lock=True)
        _assert_act_mutable(target)
        _discard_generated_act(target)
        link = db.execute(
            select(SelfEmployedAccountingRequest).where(
                SelfEmployedAccountingRequest.accounting_id == target.id,
                SelfEmployedAccountingRequest.payment_request_id == request.id,
            )
        ).scalar_one_or_none()
        if link is not None:
            db.delete(link)
        if target.payment_request_id == request.id:
            target.payment_request_id = None
        target.confirmed_at = None
        target.confirmed_by_user_id = None
        if target.parse_status == "reviewed":
            target.parse_status = "parsed"
        target.updated_at = datetime.utcnow()
        db.flush()
        remaining_link = db.execute(
            select(SelfEmployedAccountingRequest.id).where(
                SelfEmployedAccountingRequest.accounting_id == target.id
            ).limit(1)
        ).scalar_one_or_none()
        if remaining_link is None and not record_has_business_data(target):
            db.delete(target)
        else:
            if remaining_link is None and target.receipt_filename:
                standalone_receipt_id = target.id
            db.add(target)

    request.self_employed_accounting_visible = False
    request.updated_at = datetime.utcnow()
    db.add(request)
    db.commit()
    return {
        "ok": True,
        "removed_request_id": request.id,
        "standalone_receipt_id": standalone_receipt_id,
    }


@router.delete("/receipts/{accounting_id}")
def delete_accounting_receipt(
    accounting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    target = get_record_or_404(db, accounting_id, lock=True)
    _assert_act_mutable(target)
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
            official = resolve_receipt_qr(qr_payload)
            contractor_full_name = prefer_full_person_name(official.get("contractor_full_name"), contractor_full_name)
            iin = official.get("iin") or iin
            receipt_number = official.get("receipt_number") or receipt_number
            official_dt = official.get("receipt_datetime")
            receipt_datetime = official_dt.isoformat() if isinstance(official_dt, datetime) else (official_dt or receipt_datetime)
            if official.get("source") == "kaspi_qr":
                service_name = clean_service_name(official.get("service_name")) or clean_service_name(service_name)
            else:
                service_name = clean_service_name(service_name) or clean_service_name(official.get("service_name"))
            official_amount = official.get("receipt_amount")
            receipt_amount = str(official_amount) if official_amount is not None else receipt_amount
            qr_payload = official.get("qr_payload") or qr_payload
            parse_confidence = str(official.get("parse_confidence", Decimal("100.00")))
            ocr_text = _merge_receipt_source_text(ocr_text, official.get("source_text"))
        except HTTPException as exc:
            try:
                qr_payload = canonical_receipt_qr(qr_payload)
            except HTTPException:
                qr_payload = None
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
    _restore_receipt_identity(db, record)
    db.add(record)
    db.commit()
    return load_group_row(db, request_id)


def _update_record(
    db: Session,
    record: SelfEmployedAccounting,
    payload: SelfEmployedAccountingUpdate,
    current_user: User,
) -> None:
    source_changed = any(
        value is not None
        for value in (
            payload.contractor_full_name,
            payload.iin,
            payload.receipt_number,
            payload.receipt_datetime,
            payload.service_name,
            payload.receipt_amount,
            payload.qr_payload,
        )
    )
    if source_changed:
        _assert_act_mutable(record)
        _discard_generated_act(record)
    if payload.contractor_full_name is not None:
        record.contractor_full_name = clean_person_name(payload.contractor_full_name)
    if payload.iin is not None:
        new_iin = clean_iin(payload.iin)
        if payload.contractor_phone is None and new_iin != record.iin:
            record.contractor_phone = None
        record.iin = new_iin
    _remember_contact_phone(db, record, iin=record.iin, phone_value=payload.contractor_phone)
    if payload.contractor_phone is None and payload.iin is not None:
        _hydrate_contact_phone(db, record)
    if payload.receipt_number is not None:
        record.receipt_number = clean_receipt_number(payload.receipt_number)
    if payload.receipt_datetime is not None:
        record.receipt_datetime = payload.receipt_datetime.replace(tzinfo=None)
    if payload.service_name is not None:
        record.service_name = clean_service_name(payload.service_name)
    if payload.receipt_amount is not None:
        record.receipt_amount = clean_decimal(payload.receipt_amount)
    if payload.qr_payload is not None:
        record.qr_payload = canonical_receipt_qr(payload.qr_payload) if payload.qr_payload else None
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
        if not payload.mark_confirmed:
            record.confirmed_at = None
            record.confirmed_by_user_id = None

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
    _update_record(db, record, payload, current_user)
    _restore_receipt_identity(db, record)
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
    _update_record(db, record, payload, current_user)
    _restore_receipt_identity(db, record)
    db.add(record)
    db.commit()
    return load_group_row(db, request.id)


def _r1_payload(record: SelfEmployedAccounting, member_ids: list[int]) -> R1ActPayload:
    missing: list[str] = []
    if not record.receipt_filename:
        missing.append("чек")
    if not record.contractor_full_name:
        missing.append("ФИО")
    if len(re.sub(r"\D", "", str(record.iin or ""))) != 12:
        missing.append("ИИН")
    if not record.receipt_number:
        missing.append("номер чека")
    if not record.receipt_datetime:
        missing.append("дату чека")
    if not record.service_name:
        missing.append("наименование работы")
    if record.receipt_amount is None or Decimal(record.receipt_amount) <= 0:
        missing.append("сумму")
    if missing:
        raise HTTPException(
            status_code=400,
            detail="Перед формированием АВР заполните: " + ", ".join(missing),
        )

    work_date = record.receipt_datetime.date()
    act_number = record.act_number or f"АВР-{work_date.year}-{record.id:06d}"
    return R1ActPayload(
        act_number=act_number,
        act_date=work_date,
        work_date=work_date,
        contractor_name=str(record.contractor_full_name).strip(),
        contractor_iin=re.sub(r"\D", "", str(record.iin or "")),
        service_name=str(record.service_name).strip(),
        amount=Decimal(record.receipt_amount),
        receipt_number=str(record.receipt_number).strip() or None,
        linked_request_ids=tuple(sorted(int(value) for value in member_ids)),
        customer_name=str(R1_CUSTOMER_PROFILE["name"]),
        customer_bin_iin=str(R1_CUSTOMER_PROFILE["bin_iin"]),
        customer_address=f"{R1_CUSTOMER_PROFILE['country']}, {R1_CUSTOMER_PROFILE['address']}",
        customer_iik=str(R1_CUSTOMER_PROFILE["iik"]),
        customer_bank_name=str(R1_CUSTOMER_PROFILE["bank_name"]),
        customer_bik=str(R1_CUSTOMER_PROFILE["bik"]),
        customer_kbe=str(R1_CUSTOMER_PROFILE["kbe"]),
        customer_director=str(R1_CUSTOMER_PROFILE["director"]),
    )


@router.post("/receipts/{accounting_id}/act", response_model=SelfEmployedAccountingRead)
def generate_accounting_act(
    accounting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and persist an unsigned R-1 PDF snapshot for one receipt row."""
    require_accounting_access(current_user)
    record = get_record_or_404(db, accounting_id, lock=True)
    _assert_act_mutable(record)
    if record.act_filename or record.act_size or record.act_status == "generated":
        raise HTTPException(status_code=409, detail="АВР уже сформирован. Откройте его по иконке документа")
    _restore_receipt_identity(db, record)
    member_ids = list(
        db.execute(
            select(SelfEmployedAccountingRequest.payment_request_id).where(
                SelfEmployedAccountingRequest.accounting_id == record.id
            )
        ).scalars().all()
    )
    payload = _r1_payload(record, member_ids)
    try:
        pdf_data = generate_r1_act_pdf(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Не удалось сформировать PDF АВР") from exc

    filename = f"AVR_{payload.work_date.isoformat()}_{record.id}.pdf"
    generated_at = datetime.utcnow()
    record.act_status = "generated"
    record.act_number = payload.act_number
    record.act_date = payload.act_date
    record.act_filename = filename
    record.act_content_type = "application/pdf"
    record.act_size = len(pdf_data)
    record.act_sha256 = sha256(pdf_data).hexdigest()
    record.act_data = pdf_data
    record.act_generated_at = generated_at
    record.act_generated_by_user_id = current_user.id
    record.act_ddc_status = "pending"
    record.act_ddc_filename = None
    record.act_ddc_size = None
    record.act_ddc_sha256 = None
    record.act_ddc_data = None
    record.act_ddc_generated_at = None
    record.act_ddc_last_attempt_at = None
    record.act_ddc_error = None
    record.updated_at = generated_at
    db.add(record)
    db.commit()
    return load_accounting_row(db, record.id)


def _act_response(db: Session, record: SelfEmployedAccounting) -> Response:
    row = db.execute(
        select(
            SelfEmployedAccounting.act_data,
            SelfEmployedAccounting.act_filename,
            SelfEmployedAccounting.act_content_type,
            SelfEmployedAccounting.act_ddc_data,
            SelfEmployedAccounting.act_ddc_filename,
            SelfEmployedAccounting.act_ddc_status,
            SelfEmployedAccounting.act_ddc_error,
        ).where(SelfEmployedAccounting.id == record.id)
    ).one_or_none()
    if row is None or row.act_data is None:
        raise HTTPException(status_code=404, detail="АВР ещё не сформирован")
    content = row.act_data
    filename = row.act_filename or "AVR.pdf"
    if record.act_status == "signed":
        if row.act_ddc_status != "ready" or row.act_ddc_data is None:
            detail = "Подписанный PDF ещё формируется. Повторите открытие через несколько секунд"
            if row.act_ddc_status == "error" and row.act_ddc_error:
                detail = f"Обе подписи сохранены, но SIGEX пока не сформировал PDF: {row.act_ddc_error}"
            raise HTTPException(status_code=409, detail=detail)
        content = row.act_ddc_data
        filename = row.act_ddc_filename or f"{Path(filename).stem}_SIGNED_SIGEX.pdf"
    filename = Path(filename).name.replace('"', "")
    encoded_name = quote(filename, safe="")
    return Response(
        content=content,
        media_type="application/pdf" if record.act_status == "signed" else row.act_content_type or "application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=AVR.pdf; filename*=UTF-8''{encoded_name}",
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/receipts/{accounting_id}/act/file")
def download_accounting_act(
    accounting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_accounting_access(current_user)
    return _act_response(db, get_record_or_404(db, accounting_id))


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
