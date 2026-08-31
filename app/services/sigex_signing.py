"""Small, defensive client for SIGEX's public eGov QR and document APIs."""

from __future__ import annotations

import base64
from io import BytesIO
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests
from cryptography import x509
from cryptography.hazmat.primitives.serialization.pkcs7 import load_der_pkcs7_certificates
from cryptography.x509.oid import NameOID
from pypdf import PdfReader

from app.core.config import get_settings


class SigexError(RuntimeError):
    pass


_CMS_PEM_BOUNDARY = re.compile(
    r"-----\s*(?:BEGIN|END)\s+(?:CMS|PKCS\s*#?7(?:\s+SIGNED\s+DATA)?)\s*-----",
    re.IGNORECASE,
)


def decode_cms_signature(signature: str) -> bytes:
    """Accept pure Base64 from eGov and PEM-wrapped CMS returned by NCALayer."""
    value = str(signature or "").strip()
    if value.lower().startswith("data:") and "," in value:
        value = value.split(",", 1)[1]
    value = _CMS_PEM_BOUNDARY.sub("", value)
    value = re.sub(r"\s+", "", value)
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise SigexError("NCALayer/eGov вернул повреждённую CMS-подпись") from exc
    if len(decoded) < 128:
        raise SigexError("Полученная CMS-подпись слишком короткая")
    return decoded


@dataclass(frozen=True)
class SigexSession:
    expire_at_ms: int
    qr_code: str
    data_url: str
    sign_url: str
    egov_mobile_url: str | None
    egov_business_url: str | None


def _base_url() -> str:
    return get_settings().SIGEX_BASE_URL.rstrip("/")


def _json_response(response: requests.Response, action: str) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise SigexError(f"SIGEX: некорректный ответ при операции «{action}»") from exc
    if not isinstance(data, dict):
        raise SigexError(f"SIGEX: пустой ответ при операции «{action}»")
    # SIGEX documents that API errors are JSON objects with `message` and
    # `requestID`. Some gateway paths preserve HTTP 200 for that object, so an
    # HTTP-only check masks the real error as a missing document/signature ID.
    message = str(data.get("message") or "").strip()
    request_id = str(data.get("requestID") or data.get("requestId") or "").strip()
    if not response.ok or message:
        detail = message or f"SIGEX вернул HTTP {response.status_code}"
        if request_id:
            detail = f"{detail} (SIGEX requestID: {request_id})"
        raise SigexError(f"SIGEX — {action}: {detail}")
    return data


def _positive_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _trusted_sigex_url(value: str | None) -> str:
    candidate = str(value or "").strip()
    parsed = urlparse(candidate)
    configured = urlparse(_base_url())
    if parsed.scheme != "https" or not parsed.hostname:
        raise SigexError("SIGEX вернул небезопасную служебную ссылку")
    allowed_host = str(configured.hostname or "").lower()
    actual_host = str(parsed.hostname or "").lower()
    if actual_host != allowed_host and not actual_host.endswith(f".{allowed_host}"):
        raise SigexError("SIGEX вернул ссылку с неожиданного домена")
    return candidate


def create_egov_session(description: str, back_url: str) -> SigexSession:
    try:
        response = requests.post(
            f"{_base_url()}/api/egovQr",
            json={"description": description[:250], "whenDone": {"backUrl": back_url}},
            timeout=(8, 25),
        )
    except requests.RequestException as exc:
        raise SigexError("Не удалось подключиться к SIGEX") from exc
    data = _json_response(response, "создание QR")
    try:
        return SigexSession(
            expire_at_ms=int(data["expireAt"]),
            qr_code=str(data["qrCode"]),
            data_url=_trusted_sigex_url(data.get("dataURLAuto") or data.get("dataURL")),
            sign_url=_trusted_sigex_url(data.get("signURLAuto") or data.get("signURL")),
            egov_mobile_url=str(data.get("eGovMobileLaunchLink") or "").strip() or None,
            egov_business_url=str(data.get("eGovBusinessLaunchLink") or "").strip() or None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SigexError("SIGEX вернул неполные данные QR-сессии") from exc


def wait_for_egov_signature(
    *,
    data_url: str,
    sign_url: str,
    pdf_data: bytes,
    act_number: str,
    contractor_name: str,
    amount_text: str,
) -> str:
    payload = {
        "signMethod": "CMS_SIGN_ONLY",
        "documentsToSign": [
            {
                "id": 1,
                "nameRu": f"Акт выполненных работ {act_number}",
                "nameKz": f"Орындалған жұмыстар актісі {act_number}",
                "nameEn": f"Act of completed works {act_number}",
                "meta": [
                    {"name": "Исполнитель", "value": contractor_name[:255]},
                    {"name": "Сумма", "value": amount_text[:100]},
                ],
                "document": {
                    "file": {
                        "mime": "@file/pdf",
                        "data": base64.b64encode(pdf_data).decode("ascii"),
                    }
                },
            }
        ],
    }
    try:
        post_response = requests.post(
            _trusted_sigex_url(data_url),
            json=payload,
            timeout=(15, 420),
        )
    except requests.RequestException as exc:
        raise SigexError("eGov не забрал документ на подписание вовремя") from exc
    post_data = _json_response(post_response, "отправка документа в eGov")
    result_url = _trusted_sigex_url(post_data.get("signURLAuto") or post_data.get("signURL") or sign_url)

    try:
        sign_response = requests.get(result_url, timeout=(15, 600))
    except requests.RequestException as exc:
        raise SigexError("Не получен результат подписания из eGov") from exc
    result = _json_response(sign_response, "получение подписи eGov")
    if str(result.get("status") or "").upper() == "CANCELED":
        raise SigexError("Подписание отменено в eGov")
    documents = result.get("documentsToSign")
    if not isinstance(documents, list) or not documents:
        raise SigexError("eGov не вернул подпись документа")
    signature = (((documents[0] or {}).get("document") or {}).get("file") or {}).get("data")
    signature = re.sub(r"\s+", "", str(signature or ""))
    if not signature:
        raise SigexError("eGov вернул пустую подпись")
    try:
        decoded = base64.b64decode(signature, validate=True)
    except ValueError as exc:
        raise SigexError("eGov вернул повреждённую подпись") from exc
    if len(decoded) < 128:
        raise SigexError("Полученная подпись слишком короткая")
    return signature


def register_document_signature(
    *,
    signature_b64: str,
    title: str,
    expected_iins: list[str],
) -> tuple[str, int]:
    requirements = [
        {"iin": f"IIN{re.sub(r'\D', '', value)}"}
        for value in expected_iins
        if len(re.sub(r"\D", "", value)) == 12
    ]
    payload = {
        "title": title[:200],
        "description": "Акт выполненных работ формы Р-1",
        "signType": "cms",
        "signature": signature_b64,
        "settings": {
            "private": False,
            "signaturesLimit": 2,
            # The backend must still be able to build the public verification
            # DDC after the second signature without authenticating as either
            # signer. The random SIGEX document ID remains the access secret.
            "switchToPrivateAfterLimitReached": False,
            "unique": ["iin"],
            # The first CMS has already been assigned to an AVR side after a
            # local certificate/IIN check. SIGEX recommends `false` here so
            # requirements constrain subsequent signatures without rejecting
            # the registering signature under a stricter certificate profile.
            "strictSignersRequirements": False,
            "signersRequirements": requirements,
        },
    }
    try:
        response = requests.post(f"{_base_url()}/api", json=payload, timeout=(10, 60))
    except requests.RequestException as exc:
        raise SigexError("SIGEX не смог зарегистрировать первую подпись") from exc
    result = _json_response(response, "регистрация документа")
    document_id = str(result.get("documentId") or "").strip()
    sign_id = _positive_int(result.get("signId"))
    if not document_id or sign_id <= 0:
        fields = ", ".join(sorted(str(key) for key in result)) or "нет полей"
        raise SigexError(
            f"SIGEX вернул успешный ответ без номера документа или подписи (поля: {fields})"
        )
    return document_id, sign_id


def finalize_document_data(document_id: str, pdf_data: bytes) -> None:
    clean_id = str(document_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", clean_id):
        raise SigexError("Некорректный номер документа SIGEX")
    source = bytes(pdf_data or b"")
    if not source.startswith(b"%PDF-"):
        raise SigexError("Исходный АВР не является PDF")
    try:
        data_response = requests.post(
            f"{_base_url()}/api/{clean_id}/data",
            data=source,
            headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(source))},
            timeout=(10, 90),
        )
    except requests.RequestException as exc:
        raise SigexError("SIGEX не завершил регистрацию документа") from exc
    result = _json_response(data_response, "фиксация хешей PDF")
    returned_id = str(result.get("documentId") or "").strip()
    if returned_id and returned_id != clean_id:
        raise SigexError("SIGEX вернул номер другого документа при фиксации PDF")


def cms_signer_identity(
    signature_b64: str,
    expected_iins: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, str | None]:
    """Read the IIN from the certificate before assigning a signature to a side."""
    try:
        der = decode_cms_signature(signature_b64)
        certificates: list[x509.Certificate] = load_der_pkcs7_certificates(der)
    except Exception as exc:
        if isinstance(exc, SigexError):
            raise
        raise SigexError("Не удалось прочитать сертификат CMS-подписи") from exc
    if not certificates:
        raise SigexError("CMS-подпись не содержит сертификат подписанта")
    expected = {
        re.sub(r"\D", "", str(value or ""))
        for value in (expected_iins or [])
        if len(re.sub(r"\D", "", str(value or ""))) == 12
    }
    candidates: list[tuple[str, str | None]] = []
    for certificate in certificates:
        common_names = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        name = str(common_names[0].value).strip() if common_names else None
        # Current NCA certificates normally keep IIN in SERIALNUMBER, while
        # several older/legal-person profiles expose the same IIN through a
        # different Subject attribute. Search every Subject value, but only
        # accept an explicitly prefixed IIN to avoid confusing it with BIN or
        # the certificate's own serial number.
        for attribute in certificate.subject:
            value = str(attribute.value or "")
            match = re.search(r"(?:^|[^A-Z])IIN\s*([0-9]{12})(?:\D|$)", value, re.I)
            if match:
                candidate = (match.group(1), name)
                if candidate[0] in expected:
                    return candidate
                candidates.append(candidate)
    if candidates:
        return candidates[0]
    raise SigexError("В сертификате ЭЦП не найден ИИН подписанта")


def add_document_signature(document_id: str, signature_b64: str) -> int:
    try:
        response = requests.post(
            f"{_base_url()}/api/{document_id}",
            json={"signType": "cms", "signature": signature_b64},
            timeout=(10, 60),
        )
    except requests.RequestException as exc:
        raise SigexError("SIGEX не смог зарегистрировать вторую подпись") from exc
    result = _json_response(response, "добавление подписи")
    sign_id = _positive_int(result.get("signId"))
    if sign_id <= 0:
        fields = ", ".join(sorted(str(key) for key in result)) or "нет полей"
        raise SigexError(f"SIGEX вернул успешный ответ без номера подписи (поля: {fields})")
    return sign_id


def build_document_card(
    *,
    document_id: str,
    pdf_data: bytes,
    filename: str,
) -> bytes:
    """Build the official SIGEX DDC PDF for a registered two-party document."""
    clean_id = str(document_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", clean_id):
        raise SigexError("Некорректный номер документа SIGEX")
    source = bytes(pdf_data or b"")
    if not source.startswith(b"%PDF-"):
        raise SigexError("Исходный АВР не является PDF")
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "_", str(filename or "AVR.pdf")).strip("._")
    if not safe_filename.lower().endswith(".pdf"):
        safe_filename = f"{safe_filename or 'AVR'}.pdf"
    safe_filename = f"{safe_filename[:-4][:190] or 'AVR'}.pdf"
    params = {
        "fileName": safe_filename,
        "withoutDocumentVisualization": "false",
        "withoutSignaturesVisualization": "false",
        "withoutQRCodesInSignaturesVisualization": "false",
        "withoutID": "false",
        "language": "ru",
    }
    try:
        response = requests.post(
            f"{_base_url()}/api/{clean_id}/buildDDC",
            params=params,
            data=source,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(source)),
            },
            timeout=(15, 180),
        )
    except requests.RequestException as exc:
        raise SigexError("SIGEX не смог сформировать подписанный PDF") from exc
    result = _json_response(response, "формирование карточки электронного документа")
    encoded = re.sub(r"\s+", "", str(result.get("ddc") or ""))
    if not encoded:
        raise SigexError("SIGEX не вернул карточку электронного документа")
    try:
        ddc = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise SigexError("SIGEX вернул повреждённую карточку электронного документа") from exc
    if len(ddc) < 128 or not ddc.startswith(b"%PDF-"):
        raise SigexError("SIGEX вернул некорректный PDF карточки электронного документа")
    try:
        if len(PdfReader(BytesIO(ddc), strict=False).pages) < 1:
            raise ValueError("empty PDF")
    except Exception as exc:
        raise SigexError("SIGEX вернул повреждённый PDF карточки электронного документа") from exc
    return ddc


def get_document_signer(document_id: str, sign_id: int) -> tuple[str | None, str | None]:
    """Return signer IIN and name when the public document card is available."""
    try:
        response = requests.get(f"{_base_url()}/api/{document_id}", timeout=(8, 30))
    except requests.RequestException:
        return None, None
    if not response.ok:
        return None, None
    try:
        data = response.json()
    except ValueError:
        return None, None
    for signature in data.get("signatures") or []:
        if int(signature.get("signId") or 0) != int(sign_id):
            continue
        digits = re.sub(r"\D", "", str(signature.get("userId") or ""))
        subject = str(signature.get("subject") or "")
        name_match = re.search(r"(?:^|,)CN=([^,]+)", subject, re.I)
        return (digits if len(digits) == 12 else None), (name_match.group(1).strip() if name_match else None)
    return None, None
