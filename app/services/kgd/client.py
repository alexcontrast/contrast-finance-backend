import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class KgdServiceError(RuntimeError):
    """Техническая ошибка доступа к КГД, не равная результату «контрагент не найден»."""

    def __init__(self, message: str, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _mask_iin_bin(value: str) -> str:
    digits = normalize_iin_bin(value or "")
    if len(digits) <= 4:
        return "***"
    return f"***{digits[-4:]}"


@dataclass
class KgdTaxpayerResult:
    iin_bin: str
    tax_status: str
    message: str
    source: str
    contractor_name: str | None = None
    regime_name: str | None = None
    regime_source: str | None = None
    vat_status: str | None = None
    vat_credit_allowed: bool = False
    raw_response: dict | None = None
    perf: dict | None = None


def normalize_iin_bin(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def validate_iin_bin(iin_bin: str) -> None:
    if len(iin_bin) != 12:
        raise ValueError("BIN / ИИН должен содержать 12 цифр")


def check_taxpayer_stub(iin_bin: str) -> KgdTaxpayerResult:
    last_digit = iin_bin[-1]

    if last_digit == "1":
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="our_vat",
            message="ОУР с НДС",
            source="kgd_stub",
            contractor_name="Тестовый контрагент ОУР с НДС",
            vat_status="Плательщик НДС",
            vat_credit_allowed=True,
            raw_response={"stub": True, "rule": "last_digit_1"},
        )

    if last_digit == "2":
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="our_no_vat",
            message="ОУР без НДС",
            source="kgd_stub",
            contractor_name="Тестовый контрагент ОУР без НДС",
            vat_status="Без НДС",
            vat_credit_allowed=False,
            raw_response={"stub": True, "rule": "last_digit_2"},
        )

    if last_digit == "3":
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="simplified",
            message="Упрощенка",
            source="kgd_stub",
            contractor_name="Тестовый контрагент Упрощенка",
            vat_status="Без НДС",
            vat_credit_allowed=False,
            raw_response={"stub": True, "rule": "last_digit_3"},
        )

    return KgdTaxpayerResult(
        iin_bin=iin_bin,
        tax_status="not_found",
        message="Не найден / КГД не ответил",
        source="kgd_stub",
        contractor_name=None,
        vat_status="Неизвестно",
        vat_credit_allowed=False,
        raw_response={"stub": True, "rule": "other_last_digit"},
    )


def _fetch_json(
    label: str,
    url: str,
    headers: dict[str, str],
    timeout_seconds: int = 20,
    method: str = "GET",
    json_payload: dict | None = None,
) -> dict:
    started_at = time.perf_counter()
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "ContrastFinance/0.5.50",
        **headers,
    }
    data = None
    if json_payload is not None:
        data = json.dumps(json_payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url=url,
        headers=request_headers,
        data=data,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.getcode()
            text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "label": label,
            "status_code": exc.code,
            "body": _safe_json_parse(text),
            "text": text[:2000],
            "text_len": len(text or ""),
            "elapsed_sec": time.perf_counter() - started_at,
            "error": f"HTTP {exc.code}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "label": label,
            "status_code": None,
            "body": None,
            "text": "",
            "text_len": 0,
            "elapsed_sec": time.perf_counter() - started_at,
            "error": str(exc),
        }

    body = _safe_json_parse(text)
    return {
        "ok": 200 <= int(status_code) < 300 and body is not None,
        "label": label,
        "status_code": status_code,
        "body": body,
        "text": text[:2000],
        "text_len": len(text or ""),
        "elapsed_sec": time.perf_counter() - started_at,
        "error": None if 200 <= int(status_code) < 300 and body is not None else (
            "Ответ КГД не является JSON" if 200 <= int(status_code) < 300 else f"HTTP {status_code}"
        ),
    }

def _safe_json_parse(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def _iter_nested(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_nested(child)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_nested(item)


def _all_strings(value: Any) -> list[str]:
    result = []

    if isinstance(value, str):
        result.append(value)
    elif isinstance(value, dict):
        for key, child in value.items():
            result.append(str(key))
            result.extend(_all_strings(child))
    elif isinstance(value, list):
        for item in value:
            result.extend(_all_strings(item))
    elif value is not None:
        result.append(str(value))

    return result


def _find_first_by_keys(value: Any, keys: set[str]) -> str:
    keys_lower = {key.lower() for key in keys}

    for obj in _iter_nested(value):
        for key, child in obj.items():
            if str(key).lower() in keys_lower and child not in (None, ""):
                return str(child)

    return ""


def _pick_contractor_name(snr_body: Any, vat_body: Any) -> str:
    keys = {
        "nameRu",
        "nameKz",
        "taxpayerName",
        "taxpayerNameRu",
        "taxPayerName",
        "taxpayerFullName",
        "fullName",
        "fio",
        "name",
    }

    return (
        _find_first_by_keys(snr_body, keys)
        or _find_first_by_keys(vat_body, keys)
        or ""
    )


def _detect_snr_regime(snr_body: Any) -> dict:
    if not snr_body:
        return {
            "regime": "Неизвестно",
            "tax_status": "not_found",
            "regime_name": "",
            "regime_source": "snr_empty",
            "deduction_percent": 0,
        }

    joined = " ".join(_all_strings(snr_body)).lower()
    regime_name = _find_first_by_keys(
        snr_body,
        {"nameRu", "nameKz", "regimeName", "taxRegimeName", "taxRegimeNameRu", "ru", "name"},
    )
    regime_source = _find_first_by_keys(
        snr_body,
        {"type", "code", "regimeType", "taxRegimeType", "source"},
    )

    if (
        "snr_general_order" in joined
        or "general_order" in joined
        or "общеустанов" in joined
        or "общеустановленный" in joined
        or "оур" in joined
    ):
        return {
            "regime": "ОУР",
            "tax_status": "our_no_vat",
            "regime_name": regime_name or "Общеустановленный порядок",
            "regime_source": regime_source or "SNR_GENERAL_ORDER",
            "deduction_percent": 10,
        }

    if "simplified" in joined or "упрощ" in joined:
        return {
            "regime": "Упрощенка",
            "tax_status": "simplified",
            "regime_name": regime_name,
            "regime_source": regime_source or "snr_simplified",
            "deduction_percent": 0,
        }

    # Любой другой спецрежим: НДС 0, вычеты 0.
    return {
        "regime": "СНР",
        "tax_status": "snr",
        "regime_name": regime_name,
        "regime_source": regime_source or "snr_found_unknown_type",
        "deduction_percent": 0,
    }


def _detect_vat_status(vat_body: Any) -> dict:
    if not vat_body:
        return {
            "vat_status": "Неизвестно",
            "vat_credit_allowed": False,
            "nds_registration_date": "",
            "nds_deregistration_date": "",
        }

    reg_date = _find_first_by_keys(
        vat_body,
        {"ndsRegistrationDate", "registrationDate", "regDate"},
    )
    dereg_date = _find_first_by_keys(
        vat_body,
        {"ndsDeregistrationDate", "deregistrationDate", "deRegDate"},
    )

    if reg_date and not dereg_date:
        return {
            "vat_status": "Плательщик НДС",
            "vat_credit_allowed": True,
            "nds_registration_date": reg_date,
            "nds_deregistration_date": "",
        }

    if reg_date and dereg_date:
        return {
            "vat_status": "Снят с НДС",
            "vat_credit_allowed": False,
            "nds_registration_date": reg_date,
            "nds_deregistration_date": dereg_date,
        }

    return {
        "vat_status": "Без НДС",
        "vat_credit_allowed": False,
        "nds_registration_date": "",
        "nds_deregistration_date": "",
    }


def _localized_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("ru", "kk", "en", "nameRu", "nameKz", "name"):
            child = value.get(key)
            if child not in (None, ""):
                return str(child).strip()
    return ""


def _detect_open_data_vat(vat_info: str, vat_date: Any) -> bool | None:
    """Return the current VAT state from the unified KGD response.

    The 2026 open-data API exposes both a localized ``vatInfo`` label and a
    separate ``vatDate``.  The label is not stable enough to be the only
    signal: in real responses it can use different wording or contain only a
    Kazakh value.  A non-empty date confirms VAT registration unless the label
    explicitly says that the registration was cancelled.
    """
    joined_vat = " ".join(str(vat_info or "").lower().split())

    # A current deregistration/cancellation status must win even when KGD also
    # returns the historical registration date.
    inactive_tokens = (
        "снят",
        "исключ",
        "прекращ",
        "аннулир",
        "приостанов",
        "не состоит",
        "не является",
        "не плательщик",
        "не зарегистрирован",
        "без ндс",
        "есептен шығар",
        "есебінен шығар",
        "тіркеуден шығар",
        "тіркелмеген",
        "тұрмайды",
        "төлеуші емес",
        "табылмайды",
        "deregister",
        "unregistered",
        "not registered",
        "not vat",
        "not a vat",
    )
    if any(token in joined_vat for token in inactive_tokens):
        return False

    has_vat_date = vat_date not in (None, "") and bool(str(vat_date).strip())
    no_data_tokens = ("нет данных", "мәлімет жоқ", "no data")
    if not has_vat_date and any(token in joined_vat for token in no_data_tokens):
        return False

    active_tokens = (
        "ндс",
        "плательщик",
        "состоит",
        "ққс",
        "төлеуші",
        "vat",
        "registered",
    )
    if any(token in joined_vat for token in active_tokens):
        return True

    if has_vat_date:
        return True

    return None


def _detect_open_data_result(body: Any, iin_bin: str) -> KgdTaxpayerResult | None:
    if not isinstance(body, dict):
        return None

    returned_xin = normalize_iin_bin(str(body.get("xin") or body.get("taxpayerCode") or ""))
    if returned_xin and returned_xin != iin_bin:
        return None

    contractor_name = _localized_text(body.get("name"))
    tax_mode = _localized_text(body.get("taxMode"))
    vat_info = _localized_text(body.get("vatInfo"))
    vat_date = body.get("vatDate")
    joined_mode = tax_mode.lower()

    # Пустой объект / явное отсутствие данных не считаем найденным контрагентом.
    meaningful = contractor_name or tax_mode or vat_info or vat_date or body.get("regDate")
    if not meaningful:
        return None

    vat_credit_allowed = _detect_open_data_vat(vat_info, vat_date)

    if any(token in joined_mode for token in ("общеустанов", "общеустановленный", "оур", "general")):
        # Не превращаем неизвестный статус НДС в «без НДС». В этом редком
        # случае check_taxpayer_live продолжит проверку через резервный VAT API.
        if vat_credit_allowed is None:
            return None
        tax_status = "our_vat" if vat_credit_allowed else "our_no_vat"
        regime = "ОУР"
    elif any(token in joined_mode for token in ("упрощ", "упрощенной декларации", "simplified")):
        tax_status = "simplified"
        regime = "Упрощенка"
    elif tax_mode:
        tax_status = "snr"
        regime = "СНР"
    else:
        return None

    vat_status = "Плательщик НДС" if vat_credit_allowed else (vat_info or "Без НДС")
    message = " / ".join(part for part in (contractor_name, regime, vat_status) if part)

    return KgdTaxpayerResult(
        iin_bin=iin_bin,
        tax_status=tax_status,
        message=message or "КГД проверка выполнена",
        source="kgd_open_data",
        contractor_name=contractor_name or None,
        regime_name=tax_mode,
        regime_source="open_data_taxMode",
        vat_status=vat_status,
        vat_credit_allowed=bool(vat_credit_allowed),
        raw_response={
            "open_data": body,
            "normalized": {
                "binIin": iin_bin,
                "contractorName": contractor_name,
                "regime": regime,
                "regimeName": tax_mode,
                "regimeSource": "open_data_taxMode",
                "vatStatus": vat_status,
                "vatCreditAllowed": bool(vat_credit_allowed),
                "vatDate": vat_date or "",
                "deductionPercent": 10 if tax_status in {"our_vat", "our_no_vat"} else 0,
            },
        },
    )


def _kgd_failure_message(*responses: dict) -> str:
    parts = []
    for response in responses:
        if not response:
            continue
        label = response.get("label") or "КГД"
        status = response.get("status_code")
        error = response.get("error")
        if status:
            parts.append(f"{label}: HTTP {status}")
        elif error:
            parts.append(f"{label}: {error}")
    return "; ".join(parts) or "КГД временно не ответил"


def check_taxpayer_live(iin_bin: str) -> KgdTaxpayerResult:
    started_at = time.perf_counter()
    settings = get_settings()

    if not settings.KGD_API_KEY:
        raise KgdServiceError(
            "КГД не настроен на сервере: отсутствует переменная KGD_API_KEY",
            {"configured": False, "base_url": settings.KGD_BASE_URL},
        )

    host = (settings.KGD_BASE_URL or "https://portal.kgd.gov.kz").rstrip("/")
    headers = {"X-Portal-Token": settings.KGD_API_KEY}

    # Новый официальный единый сервис КГД (2026): имя + налоговый режим + НДС.
    # Он используется первым; старые SNR/VAT endpoint'ы ниже остаются резервом.
    open_data_url = f"{host}/services/isnaportal/public/get-sur-data"
    open_data = _fetch_json(
        "КГД сведения по контрагенту",
        open_data_url,
        headers,
        method="POST",
        json_payload={"xin": iin_bin},
    )
    open_data_result = _detect_open_data_result(open_data.get("body") if open_data.get("ok") else None, iin_bin)
    if open_data_result is not None:
        elapsed = time.perf_counter() - started_at
        open_data_result.perf = {
            "configured": True,
            "total_sec": elapsed,
            "open_data_http_sec": float(open_data.get("elapsed_sec") or elapsed),
            "open_data_ok": True,
            "open_data_status_code": open_data.get("status_code"),
        }
        logger.warning(
            "PERF kgd-client iin_bin=%s source=kgd_open_data tax_status=%s open_data_ok=True status=%s total=%.3fs",
            _mask_iin_bin(iin_bin),
            open_data_result.tax_status,
            open_data.get("status_code"),
            elapsed,
        )
        return open_data_result

    encoded = urllib.parse.quote(iin_bin)
    snr_url = f"{host}/services/isnaportalsync/public/snr-search/search?uin={encoded}"
    vat_url = f"{host}/services/isnaportalsync/public/search-payer-data?taxpayerCode={encoded}"

    fetch_started_at = time.perf_counter()
    snr = _fetch_json("SNR налоговый режим", snr_url, headers)
    snr_done_at = time.perf_counter()
    vat = _fetch_json("VAT НДС статус", vat_url, headers)
    vat_done_at = time.perf_counter()

    detect_started_at = time.perf_counter()
    if not snr.get("ok") and not vat.get("ok"):
        failure_message = _kgd_failure_message(open_data, snr, vat)
        elapsed = time.perf_counter() - started_at
        logger.error(
            "KGD unavailable iin_bin=%s open_data=%s snr=%s vat=%s message=%s",
            _mask_iin_bin(iin_bin),
            open_data.get("status_code"),
            snr.get("status_code"),
            vat.get("status_code"),
            failure_message,
        )
        diagnostics = {
            "configured": True,
            "base_url": host,
            "open_data": {
                "status_code": open_data.get("status_code"),
                "error": open_data.get("error"),
                "text": str(open_data.get("text") or "")[:500],
            },
            "snr": {
                "status_code": snr.get("status_code"),
                "error": snr.get("error"),
                "text": str(snr.get("text") or "")[:500],
            },
            "vat": {
                "status_code": vat.get("status_code"),
                "error": vat.get("error"),
                "text": str(vat.get("text") or "")[:500],
            },
        }
        raise KgdServiceError(
            f"КГД не ответил корректно. {failure_message}",
            diagnostics,
        )

    snr_detected = _detect_snr_regime(snr.get("body") if snr.get("ok") else None)
    vat_detected = _detect_vat_status(vat.get("body") if vat.get("ok") else None)

    if snr_detected["tax_status"] == "not_found":
        tax_status = "not_found"
    elif snr_detected["tax_status"] == "our_no_vat" and vat_detected["vat_credit_allowed"]:
        tax_status = "our_vat"
    else:
        tax_status = snr_detected["tax_status"]

    contractor_name = _pick_contractor_name(snr.get("body"), vat.get("body"))

    message_parts = []
    if contractor_name:
        message_parts.append(contractor_name)
    message_parts.append(snr_detected["regime"])
    message_parts.append(vat_detected["vat_status"])
    message = " / ".join(part for part in message_parts if part)

    detect_done_at = time.perf_counter()
    total_sec = detect_done_at - started_at
    perf = {
        "configured": True,
        "snr_http_sec": float(snr.get("elapsed_sec") or (snr_done_at - fetch_started_at)),
        "vat_http_sec": float(vat.get("elapsed_sec") or (vat_done_at - snr_done_at)),
        "http_total_sec": vat_done_at - fetch_started_at,
        "detect_sec": detect_done_at - detect_started_at,
        "total_sec": total_sec,
        "snr_ok": bool(snr.get("ok")),
        "vat_ok": bool(vat.get("ok")),
        "snr_status_code": snr.get("status_code"),
        "vat_status_code": vat.get("status_code"),
        "snr_text_len": int(snr.get("text_len") or 0),
        "vat_text_len": int(vat.get("text_len") or 0),
    }
    logger.warning(
        "PERF kgd-client iin_bin=%s source=kgd_live tax_status=%s snr_ok=%s vat_ok=%s "
        "snr_status=%s vat_status=%s snr_http=%.3fs vat_http=%.3fs http_total=%.3fs detect=%.3fs total=%.3fs",
        _mask_iin_bin(iin_bin),
        tax_status,
        perf["snr_ok"],
        perf["vat_ok"],
        perf["snr_status_code"],
        perf["vat_status_code"],
        perf["snr_http_sec"],
        perf["vat_http_sec"],
        perf["http_total_sec"],
        perf["detect_sec"],
        perf["total_sec"],
    )

    return KgdTaxpayerResult(
        iin_bin=iin_bin,
        tax_status=tax_status,
        message=message or "КГД проверка выполнена",
        source="kgd_live",
        contractor_name=contractor_name or None,
        regime_name=snr_detected.get("regime_name") or "",
        regime_source=snr_detected.get("regime_source") or "",
        vat_status=vat_detected.get("vat_status") or "",
        vat_credit_allowed=bool(vat_detected.get("vat_credit_allowed")),
        raw_response={
            "snr": snr,
            "vat": vat,
            "normalized": {
                "binIin": iin_bin,
                "contractorName": contractor_name,
                "regime": snr_detected["regime"],
                "regimeName": snr_detected.get("regime_name") or "",
                "regimeSource": snr_detected.get("regime_source") or "",
                "vatStatus": vat_detected.get("vat_status") or "",
                "vatCreditAllowed": bool(vat_detected.get("vat_credit_allowed")),
                "deductionPercent": 10 if tax_status in {"our_vat", "our_no_vat"} else 0,
                "ndsRegistrationDate": vat_detected.get("nds_registration_date") or "",
                "ndsDeregistrationDate": vat_detected.get("nds_deregistration_date") or "",
            },
        },
        perf=perf,
    )


def check_taxpayer(iin_bin_raw: str) -> KgdTaxpayerResult:
    settings = get_settings()

    iin_bin = normalize_iin_bin(iin_bin_raw)
    validate_iin_bin(iin_bin)

    # Рабочий режим по умолчанию — реальный КГД.
    # Заглушка остаётся только как явный dev-режим, если специально поставить KGD_MODE=stub.
    if settings.KGD_MODE == "stub":
        return check_taxpayer_stub(iin_bin)

    return check_taxpayer_live(iin_bin)
