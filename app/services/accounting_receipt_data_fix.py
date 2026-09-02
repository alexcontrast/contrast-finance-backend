from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

_ASTANA_TZ = ZoneInfo("Asia/Almaty")

_RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
    "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}
_KK_MONTHS = {
    "қаңтар": 1, "ақпан": 2, "наурыз": 3, "сәуір": 4, "мамыр": 5, "маусым": 6,
    "шілде": 7, "тамыз": 8, "қыркүйек": 9, "қазан": 10, "қараша": 11, "желтоқсан": 12,
}
_MONTHS = {**_RU_MONTHS, **_KK_MONTHS}
_MONTH_PATTERN = "|".join(sorted((re.escape(v) for v in _MONTHS), key=len, reverse=True))

_RECEIPT_CONTEXT = (
    "check", "receipt", "fiscal", "чек", "issued", "issue", "sale", "operation", "document",
)
_BAD_CONTEXT = (
    "response", "request", "server", "generated", "generation", "updated", "modified", "upload",
    "reportcreated", "responsecreated", "requestcreated",
)


def _as_astana_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(_ASTANA_TZ).replace(tzinfo=None, microsecond=0)


def _safe_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime | None:
    try:
        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
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
    if numeric > 10_000_000_000:
        numeric /= 1000.0
    if numeric < 946684800 or numeric > 4102444800:  # 2000-01-01 .. 2100-01-01
        return None
    try:
        return datetime.fromtimestamp(numeric, tz=timezone.utc).astimezone(_ASTANA_TZ).replace(tzinfo=None, microsecond=0)
    except (OverflowError, OSError, ValueError):
        return None


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-zа-яёәғқңөұүһі0-9]+", "", str(value or "").casefold())


def _parse_structured_datetime(value: Any) -> datetime | None:
    """Handle Jackson/Java date objects and arrays sometimes returned by KGD."""
    if isinstance(value, (list, tuple)):
        parts = list(value)
        if len(parts) >= 3:
            try:
                ints = [int(float(v)) for v in parts[:6]]
            except (TypeError, ValueError):
                ints = []
            if len(ints) >= 3:
                if 2000 <= ints[0] <= 2100:
                    vals = ints + [0] * (6 - len(ints))
                    return _safe_datetime(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5])
                if 2000 <= ints[2] <= 2100:
                    vals = ints + [0] * (6 - len(ints))
                    return _safe_datetime(vals[2], vals[1], vals[0], vals[3], vals[4], vals[5])
        return None

    if not isinstance(value, dict):
        return None

    keys = {_normalized_key(k): v for k, v in value.items()}

    def pick(*aliases: str):
        for alias in aliases:
            key = _normalized_key(alias)
            if key in keys and keys[key] not in {None, ""}:
                return keys[key]
        return None

    year = pick("year", "год", "жыл")
    month = pick("month", "monthValue", "месяц", "ай")
    day = pick("day", "dayOfMonth", "date", "день", "күн")
    if year is not None and month is not None and day is not None:
        try:
            month_value = int(month)
        except (TypeError, ValueError):
            month_value = _MONTHS.get(str(month).strip().casefold())
        if month_value:
            return _safe_datetime(
                int(year), month_value, int(day),
                int(pick("hour", "hours", "час", "сағат") or 0),
                int(pick("minute", "minutes", "минута", "минут") or 0),
                int(pick("second", "seconds", "секунда", "секунд") or 0),
            )

    # Some wrappers use {"value": "2026-08-28T13:36:00"} under a date field.
    for alias in ("value", "dateTime", "datetime", "timestamp", "time"):
        candidate = pick(alias)
        if candidate is not None and candidate is not value:
            parsed = _parse_any_datetime(candidate)
            if parsed is not None:
                return parsed
    return None


def _parse_any_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _as_astana_naive(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, (dict, list, tuple)):
        return _parse_structured_datetime(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _parse_numeric_timestamp(value)

    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{10,13}(?:\.\d+)?", text):
        parsed = _parse_numeric_timestamp(text)
        if parsed is not None:
            return parsed

    iso = text.replace("Z", "+00:00")
    try:
        return _as_astana_naive(datetime.fromisoformat(iso))
    except ValueError:
        pass
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text[:10]):
            parsed_date = date.fromisoformat(text[:10])
            return datetime(parsed_date.year, parsed_date.month, parsed_date.day)
    except ValueError:
        pass

    return _best_text_datetime(text)


def _text_date_candidates(text: str) -> list[tuple[datetime, int, int]]:
    result: list[tuple[datetime, int, int]] = []
    if not text:
        return result
    source = str(text).replace("\xa0", " ")

    # 28 августа 2026 г., 13:36 / 28 тамыз 2026 ж. / same without time.
    day_month_year = re.compile(
        rf"(?<!\d)(\d{{1,2}})\s+({_MONTH_PATTERN})\s+(20\d{{2}})"
        rf"(?:\s*(?:г(?:ода)?|ж(?:ылы)?|жылғы)?\.?\s*)?"
        rf"(?:[,;\s]+(?:в\s*)?(\d{{1,2}})[:.](\d{{2}})(?::(\d{{2}}))?)?",
        re.IGNORECASE,
    )
    for match in day_month_year.finditer(source):
        month = _MONTHS.get(match.group(2).casefold())
        parsed = _safe_datetime(
            int(match.group(3)), month or 0, int(match.group(1)),
            int(match.group(4) or 0), int(match.group(5) or 0), int(match.group(6) or 0),
        )
        if parsed is not None:
            result.append((parsed, match.start(), match.end()))

    # Kazakh official style: 2026 жылғы 28 тамыз, 13:36.
    year_day_month = re.compile(
        rf"(?<!\d)(20\d{{2}})\s*(?:жылғы|ж\.?|г\.?|года)?\s*(\d{{1,2}})\s+({_MONTH_PATTERN})"
        rf"(?:[,;\s]+(\d{{1,2}})[:.](\d{{2}})(?::(\d{{2}}))?)?",
        re.IGNORECASE,
    )
    for match in year_day_month.finditer(source):
        month = _MONTHS.get(match.group(3).casefold())
        parsed = _safe_datetime(
            int(match.group(1)), month or 0, int(match.group(2)),
            int(match.group(4) or 0), int(match.group(5) or 0), int(match.group(6) or 0),
        )
        if parsed is not None:
            result.append((parsed, match.start(), match.end()))

    dmy_pattern = re.compile(
        r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](20\d{2})"
        r"(?:[T,;\s]+(\d{1,2})[:.](\d{2})(?::(\d{2}))?)?",
        re.IGNORECASE,
    )
    for match in dmy_pattern.finditer(source):
        parsed = _safe_datetime(
            int(match.group(3)), int(match.group(2)), int(match.group(1)),
            int(match.group(4) or 0), int(match.group(5) or 0), int(match.group(6) or 0),
        )
        if parsed is not None:
            result.append((parsed, match.start(), match.end()))

    ymd_pattern = re.compile(
        r"(?<!\d)(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})"
        r"(?:[T,;\s]+(\d{1,2}):?(\d{2})(?::?(\d{2})(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?",
        re.IGNORECASE,
    )
    for match in ymd_pattern.finditer(source):
        parsed = _safe_datetime(
            int(match.group(1)), int(match.group(2)), int(match.group(3)),
            int(match.group(4) or 0), int(match.group(5) or 0), int(match.group(6) or 0),
        )
        if parsed is not None:
            result.append((parsed, match.start(), match.end()))

    return result


def _context_score(text: str, start: int, end: int) -> int:
    left = text[max(0, start - 140):start].casefold()
    around = text[max(0, start - 90):min(len(text), end + 90)].casefold()
    score = 0
    if any(token in around for token in ("чек", "receipt", "check")):
        score += 160
    if re.search(r"(?:^|\s)от\s*$", left[-24:], re.IGNORECASE):
        score += 70
    if any(token in around for token in ("дата чека", "дата выписки", "issue date", "receipt date", "чек күні")):
        score += 120
    if re.search(r"создан(?:о|а)?|сформирован(?:о|а)?|загружен(?:о|а)?|generated|response|server", around, re.IGNORECASE):
        score -= 150
    return score


def _best_text_datetime(text: str) -> datetime | None:
    candidates = _text_date_candidates(text or "")
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda item: (_context_score(text, item[1], item[2]), -item[1]), reverse=True)
    return ranked[0][0]


def _path_score(path: str) -> int | None:
    normalized = _normalized_key(path)
    if not normalized:
        return None
    has_date_signal = any(token in normalized for token in ("date", "time", "дата", "время", "created", "issued", "issue", "timestamp", "күн"))
    if not has_date_signal:
        return None

    score = 0
    if any(token in normalized for token in _RECEIPT_CONTEXT):
        score += 150
    if any(token in normalized for token in (
        "receiptdatetime", "checkdatetime", "receiptdate", "checkdate", "fiscaldate",
        "issuedat", "issueddate", "issuedtime", "documentdatetime", "operationdatetime",
    )):
        score += 130
    if any(token in normalized for token in ("issued", "issue", "operation", "sale")):
        score += 45
    if any(token in normalized for token in _BAD_CONTEXT):
        score -= 220

    has_create = "create" in normalized or "created" in normalized
    has_receipt_context = any(token in normalized for token in ("check", "receipt", "fiscal", "чек", "document"))
    if has_create and not has_receipt_context:
        return None

    if score == 0 and normalized in {"date", "datetime", "dateandtime", "datetimevalue", "timestamp", "createdate"}:
        score = 10
    if score <= -100:
        return None
    return score


def _container_receipt_score(value: Any) -> int:
    if not isinstance(value, dict):
        return 0
    keys = {_normalized_key(key) for key in value.keys()}
    joined = " ".join(keys)
    score = 0
    if any(token in joined for token in ("check", "receipt", "fiscal", "чек")):
        score += 70
    if any(token in joined for token in ("iin", "bin", "seller", "executor", "taxpayer", "total", "amount", "service", "item")):
        score += 35
    return score


def _find_json_receipt_datetime(accounting: Any, payload: Any) -> datetime | None:
    candidates: list[tuple[int, datetime, str]] = []

    def walk(node: Any, path: str = "", inherited_score: int = 0) -> None:
        local_score = inherited_score + _container_receipt_score(node)
        if path:
            score = _path_score(path)
            if score is not None:
                parsed = _parse_any_datetime(node)
                if parsed is not None:
                    candidates.append((score + min(local_score, 80), parsed, path))

        if isinstance(node, dict):
            for key, child in node.items():
                child_path = f"{path}.{key}" if path else str(key)
                walk(child, child_path, min(local_score, 80))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]", min(local_score, 80))
        elif isinstance(node, str):
            lowered = node.casefold()
            looks_like_receipt_text = (
                any(token in lowered for token in ("чек", "receipt", "check"))
                or bool(re.search(r"\bот\s+\d{1,2}(?:[./-]|\s+[а-яёәғқңөұүһі]+)", lowered, re.IGNORECASE))
                or "жылғы" in lowered
            )
            if looks_like_receipt_text:
                parsed = _best_text_datetime(node)
                if parsed is not None:
                    text_score = 190 if any(token in lowered for token in ("чек", "receipt", "check")) else 110
                    candidates.append((text_score + min(local_score, 50), parsed, path))

    walk(payload)

    # Keep compatibility with route-specific flattening and catch unusual key wrappers.
    try:
        for path, value in accounting._flatten_json(payload):
            score = _path_score(str(path))
            if score is None:
                continue
            parsed = _parse_any_datetime(value)
            if parsed is not None:
                candidates.append((score, parsed, str(path)))
    except Exception:
        pass

    if not candidates:
        try:
            raw_text = json.dumps(payload, ensure_ascii=False, default=str)
        except Exception:
            raw_text = str(payload)
        lowered = raw_text.casefold()
        if any(token in lowered for token in ("чек", "receipt", "check", "жылғы")):
            return _best_text_datetime(raw_text)
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _letter_count(value: str) -> int:
    return sum(1 for char in str(value or "") if char.isalpha())


def _trim_person_candidate(value: str) -> str:
    text = " ".join(str(value or "").replace("\xa0", " ").split()).strip()
    allowed_edge = {".", "'", "’", "-"}
    while text and not (text[0].isalpha() or text[0] in allowed_edge):
        text = text[1:]
    while text and not (text[-1].isalpha() or text[-1] in allowed_edge):
        text = text[:-1]
    return text.strip()


def _looks_like_person_name(value: str) -> bool:
    clean = _trim_person_candidate(value)
    if not clean or any(char.isdigit() for char in clean):
        return False
    lowered = clean.casefold()
    reject = (
        "режим", "налогооблож", "самозанят", "бин", "чек", "receipt", "итого", "платеж", "платёж",
        "наличн", "безналичн", "банк", "кбе", "иик", "contrast event", "қорытынды", "төлем",
    )
    if any(token in lowered for token in reject):
        return False
    words = [part for part in clean.split() if part]
    return 2 <= len(words) <= 6 and _letter_count(clean) >= 6


def _extract_unicode_name_from_text(raw_text: str) -> str | None:
    text = str(raw_text or "").replace("\xa0", " ").replace("\r", "")
    lines = [" ".join(line.split()).strip() for line in text.split("\n") if line.strip()]
    iin_index = next((i for i, line in enumerate(lines) if re.search(r"(?:ИИН|IIN|ЖСН)", line, re.IGNORECASE)), -1)
    if iin_index < 0:
        return None
    indexes = list(range(iin_index + 1, min(len(lines), iin_index + 6)))
    indexes += list(range(iin_index - 1, max(-1, iin_index - 5), -1))
    for index in indexes:
        candidate = _trim_person_candidate(lines[index])
        if _looks_like_person_name(candidate):
            return candidate
    return None


def _extract_unicode_service_from_text(raw_text: str) -> str | None:
    text = str(raw_text or "").replace("\xa0", " ").replace("\r", "")
    lines = [" ".join(line.split()).strip() for line in text.split("\n") if line.strip()]
    total_index = next((i for i, line in enumerate(lines) if re.search(r"^(?:итого|total|барлығы|қорытынды)\b", line, re.IGNORECASE)), -1)
    payment_index = next((i for i, line in enumerate(lines) if re.search(r"безналичн|наличн|текущ(?:ий)?\s+плат[её]ж|способ\s+оплаты|төлем", line, re.IGNORECASE)), -1)
    end = total_index if total_index > 0 else len(lines)
    start = payment_index + 1 if payment_index >= 0 else max(0, end - 8)
    amount_tail = re.compile(r"\s+[0-9][0-9\s.,]{0,18}\s*(?:₸|тг|тенге|теңге|T\b)\s*$", re.IGNORECASE)
    candidates: list[str] = []
    for raw_line in lines[start:end]:
        if not amount_tail.search(raw_line):
            continue
        line = amount_tail.sub("", raw_line).strip()
        lowered = line.casefold()
        if any(token in lowered for token in ("иин", "жсн", "бин", "чек", "receipt", "итого", "режим", "самозанят", "ип ", "қорытынды")):
            continue
        if _letter_count(line) >= 3:
            candidates.append(line)
    return " ".join(candidates).strip() or None


def _extract_json_unicode_name(accounting: Any, payload: Any) -> str | None:
    try:
        rows = accounting._flatten_json(payload)
    except Exception:
        return None
    candidates: list[tuple[int, str]] = []
    for path, value in rows:
        if not isinstance(value, str):
            continue
        normalized = _normalized_key(path)
        if any(token in normalized for token in ("customer", "buyer")):
            continue
        has_name = any(token in normalized for token in ("fullname", "fio", "name", "атжөні", "атыжөні"))
        has_party = any(token in normalized for token in ("seller", "executor", "taxpayer", "individual", "person", "ip", "contractor"))
        if not has_name:
            continue
        candidate = _trim_person_candidate(value)
        if not _looks_like_person_name(candidate) or "contrast event" in candidate.casefold():
            continue
        score = 100 if has_party else 20
        candidates.append((score, candidate))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1] if candidates else None




def _unicode_clean_person_name(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\xa0", " ")
    text = re.sub(r"^\s*(?:ФИО|FIO|ИП|исполнитель|самозанятый|аты[- ]?жөні|аты жөні)\s*[:№#-]*\s*", "", text, flags=re.IGNORECASE)
    cleaned_chars: list[str] = []
    for ch in text:
        if ch.isalpha() or ch in {" ", ".", "'", "’", "-"}:
            cleaned_chars.append(ch)
        elif ch.isspace():
            cleaned_chars.append(" ")
        else:
            cleaned_chars.append(" ")
    cleaned = " ".join("".join(cleaned_chars).split()).strip(" .'-’")
    words = [word for word in cleaned.split() if any(ch.isalpha() for ch in word)]
    if len(words) < 2:
        return None
    return " ".join(words)[:255]


def _normalize_iin_candidate(value: Any) -> str | None:
    if value is None:
        return None
    source = str(value)
    # OCR-confusable characters are normalized only inside an IIN-labelled/keyed value.
    trans = str.maketrans({"О": "0", "O": "0", "о": "0", "o": "0", "І": "1", "I": "1", "i": "1", "l": "1", "|": "1"})
    source = source.translate(trans)
    digits = "".join(ch for ch in source if ch.isdigit())
    return digits if len(digits) == 12 else None


def _extract_iin_from_text(raw_text: Any, customer_iin: str = "") -> str | None:
    text = str(raw_text or "").replace("\xa0", " ")
    patterns = [
        r"(?:ИИН|IIN|ЖСН)\s*[:№#-]*\s*((?:[0-9ОOоoІIil|][ \t-]?){12,18})",
        r"(?:individual\s*(?:iin|id)|taxpayer\s*(?:iin|id))\s*[:=\"' ]+((?:[0-9ОOоoІIil|][ \t-]?){12,18})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            digits = _normalize_iin_candidate(match.group(1))
            if digits and digits != str(customer_iin or ""):
                return digits
    return None


def _extract_receipt_number_from_text(raw_text: Any) -> str | None:
    text = str(raw_text or "").replace("\xa0", " ")
    patterns = [
        r"(?:Чек|Receipt)\s*(?:№|N|#|номер|number)?\s*[:#=-]*\s*((?:[0-9ОO][ \t-]?){4,24})",
        r"(?:checkNumber|receiptNumber|fiscalNumber)\s*[\"']?\s*[:=]\s*[\"']?((?:[0-9ОO][ \t-]?){4,24})",
    ]
    candidates: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            candidate = match.group(1).replace("О", "0").replace("O", "0")
            digits = "".join(ch for ch in candidate if ch.isdigit())
            if 4 <= len(digits) <= 24:
                candidates.append(digits)
    if not candidates:
        return None
    # Printed e-Salyq numbers are normally 12 digits. Prefer exact printed shape,
    # then the first labelled value rather than an arbitrary JSON numeric field.
    candidates.sort(key=lambda value: (len(value) == 12, len(value)), reverse=True)
    return candidates[0]


def _extract_json_iin(accounting: Any, payload: Any) -> str | None:
    customer = str(getattr(accounting, "R1_CUSTOMER_PROFILE", {}).get("bin_iin") or "")
    candidates: list[tuple[int, str]] = []
    try:
        rows = accounting._flatten_json(payload)
    except Exception:
        rows = []
    for path, value in rows:
        normalized = _normalized_key(path)
        score = 0
        if any(token in normalized for token in ("iin", "iinbin", "biniin", "жсн", "taxpayerid", "identificationnumber", "personalnumber")):
            score += 90
        if any(token in normalized for token in ("seller", "executor", "contractor", "taxpayer", "individual", "person", "supplier")):
            score += 70
        if any(token in normalized for token in ("customer", "buyer", "purchaser")):
            score -= 180
        if score <= 0:
            continue
        digits = _normalize_iin_candidate(value)
        if digits and digits != customer:
            candidates.append((score, digits))
    # Human-readable KGD report text is more trustworthy than a generic JSON key.
    try:
        raw = json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        raw = str(payload)
    printed = _extract_iin_from_text(raw, customer)
    if printed:
        candidates.append((250, printed))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _extract_json_receipt_number(accounting: Any, payload: Any) -> str | None:
    candidates: list[tuple[int, str]] = []
    try:
        rows = accounting._flatten_json(payload)
    except Exception:
        rows = []
    for path, value in rows:
        normalized = _normalized_key(path)
        if any(token in normalized for token in ("checkid", "receiptid", "ipregid", "registrationid")):
            continue
        score = 0
        if any(token in normalized for token in ("checknumber", "receiptnumber", "fiscalnumber", "checknum", "receiptnum")):
            score += 130
        elif ("check" in normalized or "receipt" in normalized) and "number" in normalized:
            score += 100
        if score <= 0:
            continue
        digits = "".join(ch for ch in str(value or "").replace("О", "0").replace("O", "0") if ch.isdigit())
        if 4 <= len(digits) <= 24:
            if len(digits) == 12:
                score += 20
            candidates.append((score, digits))
    try:
        raw = json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        raw = str(payload)
    printed = _extract_receipt_number_from_text(raw)
    if printed:
        candidates.append((300, printed))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]

