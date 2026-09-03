from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import logging
import re
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

LOOKUP_TIMEOUT = (3, 6)
USER_AGENT = "Contrast-Finance/0.5.119 self-employed-identity-lookup"

# These providers expose public counterparty pages and are used only as a
# best-effort fallback when Contrast Finance has no confirmed IIN -> FIO pair.
# We never submit the whole receipt: only the 12-digit IIN is requested.
_ALLOWED_HOSTS = {
    "ba.prg.kz",
    "pk.adata.kz",
}

_KZ_LETTERS = "A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі"
_STOP_WORDS = (
    "Проверено",
    "Дата назначения",
    "Дата регистрации",
    "ИИН",
    "БИН",
    "КРП",
    "ОКЭД",
    "Юридический адрес",
    "Контактные данные",
    "Источники",
    "На рынке",
)


@dataclass(frozen=True)
class ExternalIdentityResult:
    full_name: str
    source: str


def _plain_text(html: str) -> str:
    value = re.sub(r"(?is)<script\b[^>]*>.*?</script>", " ", html or "")
    value = re.sub(r"(?is)<style\b[^>]*>.*?</style>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _normalize_candidate(value: str | None) -> str | None:
    if not value:
        return None
    candidate = unescape(str(value))
    for stop in _STOP_WORDS:
        candidate = candidate.split(stop, 1)[0]
    candidate = re.sub(rf"[^ {_KZ_LETTERS}.'’-]+", " ", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip(" .'-’")
    words = [word for word in candidate.split() if re.search(rf"[{_KZ_LETTERS}]", word)]
    if len(words) < 2:
        return None
    # Reject generic organization labels accidentally captured as a person.
    lowered = " ".join(words).casefold()
    if any(token in lowered for token in ("информация в источнике", "товарищество", "акционерное общество")):
        return None
    return " ".join(words)[:255]


def _extract_name(text: str, iin: str) -> str | None:
    if iin not in text:
        return None

    patterns = (
        r"Руководитель компании\s+(.{5,180}?)(?=\s+(?:Проверено|Дата назначения|Дата регистрации|ИИН|БИН|КРП|ОКЭД|Источники|На рынке))",
        r"Руководитель\s+(.{5,180}?)(?=\s+(?:Проверено|Дата назначения|Дата регистрации|ИИН|БИН|КРП|ОКЭД|Источники|На рынке))",
        r"ФИО\s+(.{5,180}?)(?=\s+(?:Проверено|Дата|ИИН|БИН|КРП|ОКЭД|Источники))",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = _normalize_candidate(match.group(1))
            if candidate:
                return candidate
    return None


def _safe_get(session: requests.Session, url: str) -> requests.Response | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in _ALLOWED_HOSTS:
        return None
    try:
        response = session.get(
            url,
            timeout=LOOKUP_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "ru-KZ,ru;q=0.9,kk;q=0.8"},
        )
    except requests.RequestException as exc:
        logger.info("External IIN lookup failed url=%s error=%s", url, exc)
        return None
    final = urlparse(response.url)
    if final.scheme != "https" or (final.hostname or "").lower() not in _ALLOWED_HOSTS:
        return None
    if response.status_code != 200 or not response.text:
        return None
    return response


def _lookup_ba_prg(session: requests.Session, iin: str) -> ExternalIdentityResult | None:
    # ba.prg.kz routes counterparty pages by IIN; the slug is cosmetic. The
    # unknown route is useful for people without a known organization slug and
    # follows redirects when a canonical counterparty page exists.
    urls = (
        f"https://ba.prg.kz/000000000-unknown/{iin}-{iin}/",
        f"https://ba.prg.kz/amp/000000000-unknown/{iin}-{iin}/",
    )
    for url in urls:
        response = _safe_get(session, url)
        if response is None:
            continue
        name = _extract_name(_plain_text(response.text), iin)
        if name:
            return ExternalIdentityResult(full_name=name, source="ba.prg.kz")
    return None


def _lookup_adata(session: requests.Session, iin: str) -> ExternalIdentityResult | None:
    response = _safe_get(
        session,
        f"https://pk.adata.kz/counterparty/main/company/{iin}/basic-info",
    )
    if response is None:
        return None
    name = _extract_name(_plain_text(response.text), iin)
    if not name:
        return None
    return ExternalIdentityResult(full_name=name, source="pk.adata.kz")


def lookup_full_name_by_iin(iin: str | None) -> ExternalIdentityResult | None:
    digits = re.sub(r"\D", "", str(iin or ""))
    if len(digits) != 12:
        return None

    with requests.Session() as session:
        # Prefer the public Business Analyst page because it aggregates several
        # official registries; Adata is an independent fallback. Both are
        # best-effort only and a human can always correct the resulting FIO.
        for provider in (_lookup_ba_prg, _lookup_adata):
            try:
                result = provider(session, digits)
            except Exception as exc:  # External pages must never break receipt import.
                logger.info("External IIN provider crashed provider=%s error=%s", provider.__name__, exc)
                continue
            if result:
                return result
    return None
