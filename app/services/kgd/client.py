from dataclasses import dataclass

from app.core.config import get_settings


@dataclass
class KgdTaxpayerResult:
    iin_bin: str
    tax_status: str
    message: str
    source: str
    raw_response: dict | None = None


def normalize_iin_bin(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def validate_iin_bin(iin_bin: str) -> None:
    if len(iin_bin) != 12:
        raise ValueError("BIN / ИИН должен содержать 12 цифр")


def check_taxpayer_stub(iin_bin: str) -> KgdTaxpayerResult:
    """
    Safe fake KGD mode for development.

    Last digit:
    1 -> our_vat / ОУР с НДС
    2 -> our_no_vat / ОУР без НДС
    3 -> simplified / Упрощенка
    other -> not_found
    """
    last_digit = iin_bin[-1]

    if last_digit == "1":
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="our_vat",
            message="ОУР с НДС",
            source="kgd_stub",
            raw_response={"stub": True, "rule": "last_digit_1"},
        )

    if last_digit == "2":
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="our_no_vat",
            message="ОУР без НДС",
            source="kgd_stub",
            raw_response={"stub": True, "rule": "last_digit_2"},
        )

    if last_digit == "3":
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="simplified",
            message="Упрощенка",
            source="kgd_stub",
            raw_response={"stub": True, "rule": "last_digit_3"},
        )

    return KgdTaxpayerResult(
        iin_bin=iin_bin,
        tax_status="not_found",
        message="Не найден / КГД не ответил",
        source="kgd_stub",
        raw_response={"stub": True, "rule": "other_last_digit"},
    )


def check_taxpayer_live(iin_bin: str) -> KgdTaxpayerResult:
    """
    Placeholder for real KGD integration.

    We intentionally do not hardcode endpoint format here.
    Real implementation should be added only after confirming:
    - exact KGD endpoint URL
    - request method
    - headers/auth format
    - response JSON structure

    Until then live mode fails safely and does not fake success.
    """
    settings = get_settings()

    if not settings.KGD_API_KEY:
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="not_found",
            message="KGD_API_KEY is not configured",
            source="kgd_live",
            raw_response={"error": "KGD_API_KEY is not configured"},
        )

    if not settings.KGD_BASE_URL:
        return KgdTaxpayerResult(
            iin_bin=iin_bin,
            tax_status="not_found",
            message="KGD_BASE_URL is not configured",
            source="kgd_live",
            raw_response={"error": "KGD_BASE_URL is not configured"},
        )

    return KgdTaxpayerResult(
        iin_bin=iin_bin,
        tax_status="not_found",
        message="Live KGD client is prepared but endpoint mapping is not implemented yet",
        source="kgd_live",
        raw_response={
            "error": "live_client_not_implemented",
            "base_url_configured": bool(settings.KGD_BASE_URL),
            "api_key_configured": bool(settings.KGD_API_KEY),
        },
    )


def check_taxpayer(iin_bin_raw: str) -> KgdTaxpayerResult:
    settings = get_settings()

    iin_bin = normalize_iin_bin(iin_bin_raw)
    validate_iin_bin(iin_bin)

    if settings.KGD_MODE == "live":
        return check_taxpayer_live(iin_bin)

    return check_taxpayer_stub(iin_bin)
