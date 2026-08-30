from __future__ import annotations

import base64
from hashlib import sha256
import re
import secrets
import threading
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.r1_profile import R1_CUSTOMER_PROFILE
from app.db.session import SessionLocal, get_db
from app.models.self_employed_accounting import SelfEmployedAccounting
from app.models.self_employed_act_signature import SelfEmployedActSignature
from app.models.self_employed_contact import SelfEmployedContact
from app.models.user import User
from app.schemas.self_employed_accounting import (
    SelfEmployedActInviteCreate,
    SelfEmployedActInviteRead,
    SelfEmployedActPublicRead,
    SelfEmployedActSessionRead,
)
from app.services.auth import get_current_user
from app.services.sigex_signing import (
    SigexError,
    add_document_signature,
    cms_signer_identity,
    create_egov_session,
    register_document,
    wait_for_egov_signature,
)


router = APIRouter(prefix="/accounting/self-employed", tags=["self_employed_act_signing"])
public_router = APIRouter(prefix="/sign/avr", tags=["public_act_signing"])

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
INVITE_TTL = timedelta(days=30)
_active_workers: set[int] = set()
_worker_lock = threading.Lock()


def _require_accounting_access(user: User) -> None:
    if user.role not in {"admin", "accountant"}:
        raise HTTPException(status_code=403, detail="Бухгалтерия доступна только администратору и бухгалтеру")


def _digits(value: str | None) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _whatsapp_phone(value: str | None) -> str | None:
    digits = _digits(value)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    if not 10 <= len(digits) <= 15:
        return None
    return digits


def _public_base_url(request: Request) -> str:
    configured = str(get_settings().PUBLIC_BASE_URL or "").strip().rstrip("/")
    return configured or str(request.base_url).rstrip("/")


def _record_or_404(db: Session, accounting_id: int, *, lock: bool = False) -> SelfEmployedAccounting:
    query = select(SelfEmployedAccounting).where(SelfEmployedAccounting.id == int(accounting_id))
    if lock:
        query = query.with_for_update()
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Строка бухгалтерии не найдена")
    return record


def _record_by_token(db: Session, token: str, *, lock: bool = False) -> SelfEmployedAccounting:
    query = select(SelfEmployedAccounting).where(SelfEmployedAccounting.act_signing_token == token)
    if lock:
        query = query.with_for_update()
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Ссылка на подписание не найдена")
    return record


def _resolve_customer_phone(db: Session, current_user: User, supplied: str | None) -> str | None:
    candidates = [supplied, get_settings().R1_CUSTOMER_SIGNER_PHONE]
    if current_user.role == "admin":
        candidates.append(current_user.phone)
    admin_phones = db.execute(
        select(User.phone).where(User.role == "admin", User.is_active.is_(True), User.phone.is_not(None))
    ).scalars().all()
    normalized_admins = sorted({phone for phone in (_whatsapp_phone(value) for value in admin_phones) if phone})
    if len(normalized_admins) == 1:
        candidates.append(normalized_admins[0])
    for candidate in candidates:
        phone = _whatsapp_phone(candidate)
        if phone:
            return phone
    return None


def _contact_for_iin(db: Session, iin: str | None) -> SelfEmployedContact | None:
    digits = _digits(iin)
    if len(digits) != 12:
        return None
    return db.execute(select(SelfEmployedContact).where(SelfEmployedContact.iin == digits)).scalar_one_or_none()


def _save_contractor_contact(
    db: Session,
    *,
    iin: str | None,
    phone: str,
    full_name: str | None,
) -> SelfEmployedContact:
    digits = _digits(iin)
    if len(digits) != 12:
        raise HTTPException(status_code=400, detail="Для самозанятого не указан корректный ИИН")
    contact = _contact_for_iin(db, digits)
    now = datetime.utcnow()
    if contact is None:
        contact = SelfEmployedContact(
            iin=digits,
            whatsapp_phone=phone,
            full_name=str(full_name or "").strip() or None,
            created_at=now,
            updated_at=now,
        )
    else:
        contact.whatsapp_phone = phone
        if str(full_name or "").strip():
            contact.full_name = str(full_name).strip()
        contact.updated_at = now
    db.add(contact)
    return contact


def _signature_for_role(record: SelfEmployedAccounting, role: str) -> SelfEmployedActSignature | None:
    return next((item for item in record.act_signatures if item.signer_role == role), None)


def _signature_status(
    record: SelfEmployedAccounting,
    current: SelfEmployedActSignature | None = None,
) -> None:
    statuses = {item.signer_role: item.status for item in record.act_signatures}
    if current is not None:
        statuses[current.signer_role] = current.status
    signed = sum(1 for role in ("customer", "contractor") if statuses.get(role) == "signed")
    if signed == 2:
        record.act_status = "signed"
    elif signed == 1:
        record.act_status = "partially_signed"
    elif any(statuses.get(role) in {"sent", "signing", "error"} for role in ("customer", "contractor")):
        record.act_status = "awaiting_signatures"
    else:
        record.act_status = "generated"


def _ensure_shared_token(record: SelfEmployedAccounting, now: datetime) -> None:
    expired = bool(record.act_signing_token_expires_at and record.act_signing_token_expires_at <= now)
    if not record.act_signing_token or (expired and record.act_status != "signed"):
        record.act_signing_token = secrets.token_urlsafe(32)
    if record.act_status != "signed":
        record.act_signing_token_expires_at = now + INVITE_TTL


def _whatsapp_message(record: SelfEmployedAccounting, role: str, signing_url: str) -> str:
    addressee = "ИП Contrast Event" if role == "customer" else str(record.contractor_full_name or "самозанятого")
    return (
        f"Здравствуйте! АВР {record.act_number or ''} ожидает подписи ({addressee}).\n"
        f"Откройте ссылку, проверьте документ и подпишите его через eGov Mobile:\n{signing_url}"
    )


@router.post(
    "/receipts/{accounting_id}/act/invites/{signer_role}",
    response_model=SelfEmployedActInviteRead,
)
def create_act_invite(
    accounting_id: int,
    signer_role: str,
    payload: SelfEmployedActInviteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_accounting_access(current_user)
    if signer_role not in {"customer", "contractor"}:
        raise HTTPException(status_code=404, detail="Неизвестная сторона АВР")
    record = _record_or_404(db, accounting_id, lock=True)
    if not record.act_filename or not record.act_size or record.act_status in {None, "", "not_created"}:
        raise HTTPException(status_code=409, detail="Сначала сформируйте АВР")

    expected_iin = _digits(R1_CUSTOMER_PROFILE.get("bin_iin") if signer_role == "customer" else record.iin)
    if len(expected_iin) != 12:
        raise HTTPException(status_code=400, detail="Для подписанта не указан корректный ИИН")
    if signer_role == "customer":
        phone = _resolve_customer_phone(db, current_user, payload.phone)
        phone_error = "Укажите WhatsApp владельца ИП"
    else:
        contact = _contact_for_iin(db, expected_iin)
        phone = _whatsapp_phone(payload.phone or record.contractor_phone or (contact.whatsapp_phone if contact else None))
        phone_error = "Укажите WhatsApp самозанятого"
    if not phone:
        raise HTTPException(status_code=400, detail=phone_error)

    invite = db.execute(
        select(SelfEmployedActSignature)
        .where(
            SelfEmployedActSignature.accounting_id == record.id,
            SelfEmployedActSignature.signer_role == signer_role,
        )
        .with_for_update()
    ).scalar_one_or_none()
    now = datetime.utcnow()
    _ensure_shared_token(record, now)
    if invite is None:
        invite = SelfEmployedActSignature(
            accounting_id=record.id,
            signer_role=signer_role,
            expected_iin=expected_iin,
            phone=phone,
            token=secrets.token_urlsafe(32),
            token_expires_at=record.act_signing_token_expires_at or now + INVITE_TTL,
            status="sent",
            sent_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(invite)
    elif invite.status != "signed":
        invite.expected_iin = expected_iin
        invite.phone = phone
        invite.token_expires_at = record.act_signing_token_expires_at or now + INVITE_TTL
        invite.status = "sent"
        invite.sent_at = now
        invite.updated_at = now
    if signer_role == "contractor":
        record.contractor_phone = phone
        _save_contractor_contact(db, iin=expected_iin, phone=phone, full_name=record.contractor_full_name)
    _signature_status(record, invite)
    record.updated_at = now
    db.add(record)
    db.commit()
    db.refresh(invite)

    signing_url = f"{_public_base_url(request)}/sign/avr/{record.act_signing_token}"
    message = _whatsapp_message(record, signer_role, signing_url)
    return SelfEmployedActInviteRead(
        signer_role=signer_role,
        status=invite.status,
        phone=phone,
        signing_url=signing_url,
        whatsapp_url=f"https://wa.me/{phone}?text={quote(message)}",
    )


def _public_info(record: SelfEmployedAccounting) -> SelfEmployedActPublicRead:
    if (
        record.act_signing_token_expires_at
        and record.act_signing_token_expires_at <= datetime.utcnow()
        and record.act_status != "signed"
    ):
        raise HTTPException(status_code=410, detail="Срок ссылки истёк. Запросите новую ссылку в бухгалтерии")
    customer = _signature_for_role(record, "customer")
    contractor = _signature_for_role(record, "contractor")
    return SelfEmployedActPublicRead(
        act_number=str(record.act_number or "АВР"),
        act_date=record.act_date or date.today(),
        contractor_name=str(record.contractor_full_name or "Самозанятый"),
        amount=Decimal(record.receipt_amount or 0),
        status=str(record.act_status or "generated"),
        customer_status=str(customer.status if customer else "not_sent"),
        contractor_status=str(contractor.status if contractor else "not_sent"),
        token_expires_at=record.act_signing_token_expires_at or datetime.utcnow(),
    )


@public_router.get("/{token}/info", response_model=SelfEmployedActPublicRead)
def act_public_info(token: str, db: Session = Depends(get_db)):
    return _public_info(_record_by_token(db, token))


@public_router.get("/{token}/file")
def act_public_file(token: str, db: Session = Depends(get_db)):
    record = _record_by_token(db, token)
    _public_info(record)
    row = db.execute(
        select(SelfEmployedAccounting.act_data, SelfEmployedAccounting.act_filename).where(
            SelfEmployedAccounting.id == record.id
        )
    ).one_or_none()
    if row is None or row.act_data is None:
        raise HTTPException(status_code=404, detail="Файл АВР не найден")
    filename = Path(row.act_filename or "AVR.pdf").name.replace('"', "")
    return Response(
        content=row.act_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=AVR.pdf; filename*=UTF-8''{quote(filename, safe='')}",
            "Cache-Control": "private, no-store",
            "X-Robots-Tag": "noindex, nofollow",
        },
    )


def _session_read(record: SelfEmployedAccounting, message: str | None = None) -> SelfEmployedActSessionRead:
    active = record.act_session_status == "signing"
    qr = str(record.act_qr_code or "") or None
    if qr and not qr.startswith("data:"):
        qr = f"data:image/png;base64,{qr}"
    status = "signing" if active else "error" if record.act_session_status == "error" else str(record.act_status)
    return SelfEmployedActSessionRead(
        status=status,
        expire_at=record.act_session_expires_at if active else None,
        qr_code=qr if active else None,
        egov_mobile_url=record.act_egov_mobile_url if active else None,
        egov_business_url=record.act_egov_business_url if active else None,
        message=message or record.act_signing_error,
    )


def _phone_for_inferred_role(db: Session, record: SelfEmployedAccounting, role: str) -> str:
    if role == "customer":
        return _whatsapp_phone(get_settings().R1_CUSTOMER_SIGNER_PHONE) or "77021123403"
    contact = _contact_for_iin(db, record.iin)
    return _whatsapp_phone(record.contractor_phone or (contact.whatsapp_phone if contact else None)) or ""


def _process_signature(accounting_id: int) -> None:
    if SessionLocal is None:
        return
    try:
        with SessionLocal() as db:
            record = db.get(SelfEmployedAccounting, accounting_id)
            if record is None or record.act_session_status != "signing":
                return
            pdf_row = db.execute(
                select(SelfEmployedAccounting.act_data).where(SelfEmployedAccounting.id == record.id)
            ).scalar_one_or_none()
            signature_b64 = wait_for_egov_signature(
                data_url=str(record.act_sigex_data_url or ""),
                sign_url=str(record.act_sigex_sign_url or ""),
                pdf_data=bytes(pdf_row or b""),
                act_number=str(record.act_number or "АВР"),
                contractor_name=str(record.contractor_full_name or "Самозанятый"),
                amount_text=f"{Decimal(record.receipt_amount or 0):,.2f} ₸".replace(",", " "),
            )
            signer_iin, signer_name = cms_signer_identity(signature_b64)
            customer_iin = _digits(R1_CUSTOMER_PROFILE.get("bin_iin"))
            contractor_iin = _digits(record.iin)
            if customer_iin == contractor_iin:
                raise SigexError("ИИН ИП и самозанятого не должны совпадать")
            if signer_iin == customer_iin:
                signer_role = "customer"
            elif signer_iin == contractor_iin:
                signer_role = "contractor"
            else:
                raise SigexError("ИИН в ЭЦП не совпадает ни с ИП, ни с самозанятым в АВР")

        with SessionLocal() as db:
            record = db.execute(
                select(SelfEmployedAccounting)
                .where(SelfEmployedAccounting.id == accounting_id)
                .with_for_update()
            ).scalar_one_or_none()
            if record is None or record.act_session_status != "signing":
                return
            target = db.execute(
                select(SelfEmployedActSignature)
                .where(
                    SelfEmployedActSignature.accounting_id == record.id,
                    SelfEmployedActSignature.signer_role == signer_role,
                )
                .with_for_update()
            ).scalar_one_or_none()
            if target is not None and target.status == "signed":
                raise SigexError("Эта сторона уже подписала АВР")
            now = datetime.utcnow()
            if target is None:
                target = SelfEmployedActSignature(
                    accounting_id=record.id,
                    signer_role=signer_role,
                    expected_iin=signer_iin,
                    phone=_phone_for_inferred_role(db, record, signer_role),
                    token=secrets.token_urlsafe(32),
                    token_expires_at=record.act_signing_token_expires_at or now + INVITE_TTL,
                    status="sent",
                    created_at=now,
                    updated_at=now,
                )
                db.add(target)
                db.flush()
            pdf_data = db.execute(
                select(SelfEmployedAccounting.act_data).where(SelfEmployedAccounting.id == record.id)
            ).scalar_one()
            if not record.act_sigex_document_id:
                document_id, sign_id = register_document(
                    pdf_data=bytes(pdf_data),
                    signature_b64=signature_b64,
                    title=str(record.act_filename or record.act_number or "AVR.pdf"),
                    expected_iins=[str(R1_CUSTOMER_PROFILE.get("bin_iin") or ""), str(record.iin or "")],
                )
                record.act_sigex_document_id = document_id
                record.act_sigex_registered_at = now
            else:
                sign_id = add_document_signature(record.act_sigex_document_id, signature_b64)
            raw_signature = base64.b64decode(re.sub(r"\s+", "", signature_b64), validate=True)
            target.signature_data = raw_signature
            target.signature_sha256 = sha256(raw_signature).hexdigest()
            target.sigex_sign_id = sign_id
            target.signer_iin = signer_iin
            target.signer_name = signer_name
            target.signed_at = now
            target.status = "signed"
            target.last_error = None
            target.updated_at = now
            record.act_session_status = "idle"
            record.act_signing_error = None
            _signature_status(record, target)
            record.updated_at = now
            db.add_all([target, record])
            db.commit()
    except Exception as exc:
        if SessionLocal is not None:
            with SessionLocal() as db:
                record = db.get(SelfEmployedAccounting, accounting_id)
                if record is not None and record.act_session_status == "signing":
                    record.act_session_status = "error"
                    record.act_signing_error = str(exc)[:1000] or "Не удалось завершить подписание"
                    record.updated_at = datetime.utcnow()
                    db.add(record)
                    db.commit()
    finally:
        with _worker_lock:
            _active_workers.discard(accounting_id)


def _start_worker(accounting_id: int) -> None:
    with _worker_lock:
        if accounting_id in _active_workers:
            return
        _active_workers.add(accounting_id)
    threading.Thread(target=_process_signature, args=(accounting_id,), daemon=True).start()


@public_router.post("/{token}/session", response_model=SelfEmployedActSessionRead)
def start_act_session(token: str, request: Request, db: Session = Depends(get_db)):
    record = _record_by_token(db, token, lock=True)
    _public_info(record)
    if record.act_status == "signed":
        return _session_read(record, "АВР уже подписан обеими сторонами")
    customer_iin = _digits(R1_CUSTOMER_PROFILE.get("bin_iin"))
    contractor_iin = _digits(record.iin)
    if len(customer_iin) != 12 or len(contractor_iin) != 12 or customer_iin == contractor_iin:
        raise HTTPException(status_code=400, detail="Не удалось определить корректные ИИН обеих сторон АВР")
    now = datetime.utcnow()
    if record.act_session_status == "signing" and record.act_session_expires_at and record.act_session_expires_at > now:
        db.commit()
        _start_worker(record.id)
        return _session_read(record)
    try:
        session = create_egov_session(
            f"АВР {record.act_number or ''}: подпись одной из сторон",
            f"{_public_base_url(request)}/sign/avr/{record.act_signing_token}",
        )
    except SigexError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    record.act_session_status = "signing"
    record.act_session_started_at = now
    record.act_session_expires_at = datetime.utcfromtimestamp(session.expire_at_ms / 1000)
    record.act_sigex_data_url = session.data_url
    record.act_sigex_sign_url = session.sign_url
    record.act_egov_mobile_url = session.egov_mobile_url
    record.act_egov_business_url = session.egov_business_url
    record.act_qr_code = session.qr_code
    record.act_signing_error = None
    record.updated_at = now
    db.add(record)
    db.commit()
    result = _session_read(record)
    _start_worker(record.id)
    return result


@public_router.get("/{token}/status", response_model=SelfEmployedActSessionRead)
def act_session_status(token: str, db: Session = Depends(get_db)):
    record = _record_by_token(db, token)
    _public_info(record)
    if (
        record.act_session_status == "signing"
        and record.act_session_expires_at
        and record.act_session_expires_at > datetime.utcnow()
    ):
        _start_worker(record.id)
    return _session_read(record)


@public_router.get("/{token}", response_class=HTMLResponse)
def act_signing_page(token: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,96}", token):
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    path = WEB_DIR / "sign_avr.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Страница подписания не найдена")
    return HTMLResponse(
        path.read_text(encoding="utf-8"),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "X-Robots-Tag": "noindex, nofollow",
            "Referrer-Policy": "no-referrer",
        },
    )
