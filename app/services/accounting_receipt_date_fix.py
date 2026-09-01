from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

_ASTANA_TZ = ZoneInfo("Asia/Almaty")

_RU_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

_RECEIPT_CONTEXT = (
    "check",
    "receipt",
    "fiscal",
    "чек",
    "issued",
    "issue",
    "sale",
    "operation",
)
_BAD_CONTEXT = (
    "response",
    "request",
    "server",
    "generated",
    "generation",
    "updated",
    "modified",
    "upload",
    "createdat",
    "reportcreated",
)


def _as_astana_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(_ASTANA_TZ).replace(tzinfo=None, microsecond=0)


def _safe_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime | None:
    try:
        return datetime(year, month, day, hour, minute, second)
    except (TypeError, ValueError):
        return None


def _parse_numeric_timestamp(value: Any) -> datetime | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric:
        return None
    # e-Salyq/KGD APIs may expose Unix timestamps either in seconds or ms.
    if numeric > 10_000_000_000:
        numeric /= 1000.0
    if numeric < 946684800 or numeric > 4102444800:  # 2000-01-01 .. 2100-01-01
        return None
    try:
        return datetime.fromtimestamp(numeric, tz=timezone.utc).astimezone(_ASTANA_TZ).replace(tzinfo=None, microsecond=0)
    except (OverflowError, OSError, ValueError):
        return None


def _parse_any_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _as_astana_naive(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _parse_numeric_timestamp(value)

    text = str(value).strip()
    if not text:
        return None

    if re.fullmatch(r"\d{10,13}(?:\.\d+)?", text):
        parsed = _parse_numeric_timestamp(text)
        if parsed is not None:
            return parsed

    # ISO-8601, including Z / timezone. Date-only ISO is intentionally accepted.
    iso = text.replace("Z", "+00:00")
    try:
        return _as_astana_naive(datetime.fromisoformat(iso))
    except ValueError:
        pass
    try:
        parsed_date = date.fromisoformat(text[:10])
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text[:10]):
            return datetime(parsed_date.year, parsed_date.month, parsed_date.day)
    except ValueError:
        pass

    return _best_text_datetime(text)


def _text_date_candidates(text: str) -> list[tuple[datetime, int, int]]:
    result: list[tuple[datetime, int, int]] = []
    if not text:
        return result

    # 28 августа 2026 г., 13:36 / 28 августа 2026 г.
    ru_pattern = re.compile(
        r"(?<!\d)(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+"
        r"(20\d{2})(?:\s*г(?:ода)?\.?\s*)?"
        r"(?:[,;\s]+(?:в\s*)?(\d{1,2})[:.](\d{2})(?::(\d{2}))?)?",
        re.IGNORECASE,
    )
    for match in ru_pattern.finditer(text):
        day = int(match.group(1))
        month = _RU_MONTHS[match.group(2).lower()]
        year = int(match.group(3))
        hour = int(match.group(4) or 0)
        minute = int(match.group(5) or 0)
        second = int(match.group(6) or 0)
        parsed = _safe_datetime(year, month, day, hour, minute, second)
        if parsed is not None:
            result.append((parsed, match.start(), match.end()))

    # 28.08.2026 13:36 / 28-08-2026 / 28/08/2026
    dmy_pattern = re.compile(
        r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](20\d{2})"
        r"(?:[T,;\s]+(\d{1,2})[:.](\d{2})(?::(\d{2}))?)?",
        re.IGNORECASE,
    )
    for match in dmy_pattern.finditer(text):
        parsed = _safe_datetime(
            int(match.group(3)),
            int(match.group(2)),
            int(match.group(1)),
            int(match.group(4) or 0),
            int(match.group(5) or 0),
            int(match.group(6) or 0),
        )
        if parsed is not None:
            result.append((parsed, match.start(), match.end()))

    # 2026-08-28T13:36:00 / 2026-08-28 13:36 / 2026-08-28
    ymd_pattern = re.compile(
        r"(?<!\d)(20\d{2})-(\d{1,2})-(\d{1,2})"
        r"(?:[T,;\s]+(\d{1,2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?",
        re.IGNORECASE,
    )
    for match in ymd_pattern.finditer(text):
        parsed = _safe_datetime(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4) or 0),
            int(match.group(5) or 0),
            int(match.group(6) or 0),
        )
        if parsed is not None:
            result.append((parsed, match.start(), match.end()))

    return result


def _context_score(text: str, start: int, end: int) -> int:
    left = text[max(0, start - 120):start].lower()
    around = text[max(0, start - 70):min(len(text), end + 70)].lower()
    score = 0
    if "чек" in around or "receipt" in around or "check" in around:
        score += 140
    if re.search(r"(?:^|\s)от\s*$", left[-20:]):
        score += 60
    if "дата чека" in around or "дата выписки" in around or "issue date" in around:
        score += 100
    if re.search(r"\bсоздан(?:о|а)?\b|сформирован(?:о|а)?|загружен(?:о|а)?", around):
        score -= 120
    return score


def _best_text_datetime(text: str) -> datetime | None:
    candidates = _text_date_candidates(text or "")
    if not candidates:
        return None
    # Prefer a date explicitly tied to a receipt/check; otherwise the earliest
    # printed date. This prevents footer/report generation timestamps winning.
    ranked = sorted(
        candidates,
        key=lambda item: (_context_score(text, item[1], item[2]), -item[1]),
        reverse=True,
    )
    return ranked[0][0]


def _path_score(path: str) -> int | None:
    normalized = re.sub(r"[^a-zа-я0-9]+", "", (path or "").lower())
    if not normalized:
        return None
    has_date_signal = any(token in normalized for token in ("date", "time", "дата", "время", "created", "issued", "issue"))
    if not has_date_signal:
        return None

    score = 0
    if any(token in normalized for token in _RECEIPT_CONTEXT):
        score += 140
    if any(token in normalized for token in ("issued", "issue", "checkdate", "receiptdate", "fiscaldate")):
        score += 100
    if any(token in normalized for token in ("operation", "sale")):
        score += 35

    if any(token in normalized for token in _BAD_CONTEXT):
        score -= 180

    # A bare create_date/createDate is not trustworthy. KGD can use it for the
    # generated report/response time; accept create only when nested under an
    # explicit receipt/check/fiscal context.
    has_create = "create" in normalized or "created" in normalized
    has_receipt_context = any(token in normalized for token in ("check", "receipt", "fiscal", "чек"))
    if has_create and not has_receipt_context:
        return None

    # Generic top-level "date"/"datetime" is weaker but can still be the only
    # field in compact KGD payloads. It must beat no candidate, not a receipt one.
    if score == 0 and normalized in {"date", "datetime", "dateandtime", "datetimevalue"}:
        score = 10
    if score <= -100:
        return None
    return score


def _find_json_receipt_datetime(accounting: Any, payload: Any) -> datetime | None:
    candidates: list[tuple[int, datetime, str]] = []
    try:
        flat = accounting._flatten_json(payload)
    except Exception:
        flat = []

    for path, value in flat:
        score = _path_score(str(path))
        if score is not None:
            parsed = _parse_any_datetime(value)
            if parsed is not None:
                candidates.append((score, parsed, str(path)))

        # Some API fields contain a whole human-readable receipt/HTML fragment.
        # Do not treat an arbitrary ISO string as receipt text: that is exactly
        # how technical response timestamps used to become today's receipt date.
        if isinstance(value, str):
            value_text = value.lower()
            looks_like_receipt_text = (
                "чек" in value_text
                or "receipt" in value_text
                or "check" in value_text
                or bool(re.search(r"\bот\s+\d{1,2}(?:[.\/-]|\s+[а-яё]+)", value_text, re.I))
            )
            if looks_like_receipt_text:
                text_dt = _best_text_datetime(value)
                if text_dt is not None:
                    text_score = 170 if any(token in value_text for token in ("чек", "receipt", "check")) else 90
                    candidates.append((text_score, text_dt, str(path)))

    if not candidates:
        # A JSON dump may contain many machine timestamps. Only use a textual
        # fallback when the payload itself clearly contains receipt/check text.
        raw_text = str(payload)
        lowered = raw_text.lower()
        if any(token in lowered for token in ("чек", "receipt", "check")):
            return _best_text_datetime(raw_text)
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def apply_accounting_receipt_date_fix() -> None:
    """Patch v0.5.103 accounting date helpers without replacing its large route.

    This is intentionally a small compatibility layer so the v0.5.103 SIGEX/
    eGov/R-1 changes remain untouched while receipt-date handling is corrected.
    """
    from app.api.routes import self_employed_accounting as accounting

    if getattr(accounting, "_receipt_date_fix_v0104", False):
        return

    original_parse_json = accounting._parse_esalyq_json
    original_build_row = accounting.build_row

    def patched_parse_report_datetime(text: str) -> datetime | None:
        return _best_text_datetime(text or "")

    def patched_clean_datetime(value: Any) -> datetime | None:
        if value is None or value == "":
            return None
        parsed = _parse_any_datetime(value)
        if parsed is not None:
            return parsed
        # Preserve the route's existing API contract for invalid manual input.
        raise accounting.HTTPException(status_code=422, detail="Некорректная дата чека")

    def patched_parse_esalyq_json(payload: Any) -> dict[str, Any]:
        result = dict(original_parse_json(payload) or {})
        # Never trust the old generic create_date fallback. Only an explicitly
        # receipt/check-related field or the printed receipt text may set it.
        result.pop("receipt_datetime", None)
        receipt_dt = _find_json_receipt_datetime(accounting, payload)
        if receipt_dt is not None:
            result["receipt_datetime"] = receipt_dt
        return result

    def patched_build_row(*args: Any, **kwargs: Any):
        row = original_build_row(*args, **kwargs)
        # Do not present upload time as if it were the receipt issue date. This
        # changes display semantics only; a request without a receipt date can
        # still be found in its event month until QR refresh repairs it.
        if getattr(row, "has_receipt", False) and not getattr(row, "receipt_datetime", None):
            updates = {"receipt_uploaded_at": None}
            if getattr(row, "is_receipt_only", False):
                updates["request_created_at"] = None
            if hasattr(row, "model_copy"):
                row = row.model_copy(update=updates)
            elif hasattr(row, "copy"):
                row = row.copy(update=updates)
        return row

    accounting._parse_report_datetime = patched_parse_report_datetime
    accounting.clean_datetime = patched_clean_datetime
    accounting._parse_esalyq_json = patched_parse_esalyq_json
    accounting.build_row = patched_build_row
    accounting._receipt_date_fix_v0104 = True
