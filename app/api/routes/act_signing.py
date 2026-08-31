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
    SelfEmployedActCmsCreate,
    SelfEmployedActInviteCreate,
    SelfEmployedActInviteRead,
    SelfEmployedActPublicRead,
    SelfEmployedActSessionRead,
)
from app.services.auth import get_current_user
from app.services.sigex_signing import (
    SigexError,
    add_document_signature,
    build_document_card,
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
_active_finalizers: set[int] = set()
_active_ddc_workers: set[int] = set()
_worker_lock = threading.Lock()
DDC_RETRY_COOLDOWN = timedelta(seconds=30)
DDC_STALE_BUILD = timedelta(minutes=5)


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


def _signed_file_ready(record: SelfEmployedAccounting) -> bool:
    return bool(
        record.act_ddc_status == "ready"
        and record.act_ddc_filename
        and record.act_ddc_size
    )


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
        signed_file_ready=_signed_file_ready(record),
        signed_file_status=str(record.act_ddc_status or "pending"),
        token_expires_at=record.act_signing_token_expires_at or datetime.utcnow(),
    )


@public_router.get("/{token}/info", response_model=SelfEmployedActPublicRead)
def act_public_info(token: str, db: Session = Depends(get_db)):
    record = _record_by_token(db, token)
    if record.act_status == "signed" and not _signed_file_ready(record):
        _start_ddc_worker(record.id)
    return _public_info(record)


@router.post("/receipts/{accounting_id}/act/ddc")
def retry_accounting_act_ddc(
    accounting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_accounting_access(current_user)
    record = _record_or_404(db, accounting_id)
    if record.act_status != "signed":
        raise HTTPException(status_code=409, detail="DDC формируется только после двух подписей")
    if _signed_file_ready(record):
        return {"status": "ready", "ready": True}
    _start_ddc_worker(record.id, force=True)
    return {
        "status": "building",
        "ready": False,
        "message": "SIGEX формирует PDF с обеими подписями и QR",
    }


@public_router.get("/{token}/file")
def act_public_file(token: str, download: bool = False, db: Session = Depends(get_db)):
    record = _record_by_token(db, token)
    _public_info(record)
    row = db.execute(
        select(
            SelfEmployedAccounting.act_data,
            SelfEmployedAccounting.act_filename,
            SelfEmployedAccounting.act_ddc_data,
            SelfEmployedAccounting.act_ddc_filename,
            SelfEmployedAccounting.act_ddc_status,
            SelfEmployedAccounting.act_ddc_error,
        ).where(SelfEmployedAccounting.id == record.id)
    ).one_or_none()
    if row is None or row.act_data is None:
        raise HTTPException(status_code=404, detail="Файл АВР не найден")
    content = row.act_data
    filename = row.act_filename or "AVR.pdf"
    if record.act_status == "signed":
        if row.act_ddc_status != "ready" or row.act_ddc_data is None:
            _start_ddc_worker(record.id)
            detail = "Обе подписи сохранены. Подписанный PDF ещё формируется — повторите через несколько секунд"
            if row.act_ddc_status == "error" and row.act_ddc_error:
                detail = f"Обе подписи сохранены, но SIGEX пока не сформировал PDF: {row.act_ddc_error}"
            raise HTTPException(status_code=409, detail=detail)
        content = row.act_ddc_data
        filename = row.act_ddc_filename or f"{Path(filename).stem}_SIGNED_SIGEX.pdf"
    filename = Path(filename).name.replace('"', "")
    disposition = "attachment" if download and record.act_status == "signed" else "inline"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"{disposition}; filename=AVR.pdf; filename*=UTF-8''{quote(filename, safe='')}",
            "Cache-Control": "private, no-store",
            "X-Robots-Tag": "noindex, nofollow",
        },
    )


def _session_read(record: SelfEmployedAccounting, message: str | None = None) -> SelfEmployedActSessionRead:
    now = datetime.utcnow()
    expired = bool(
        record.act_session_status == "signing"
        and record.act_session_expires_at
        and record.act_session_expires_at <= now
    )
    active = record.act_session_status == "signing" and not expired
    finalizing = record.act_session_status == "finalizing"
    qr = str(record.act_qr_code or "") or None
    if qr and not qr.startswith("data:"):
        qr = f"data:image/png;base64,{qr}"
    signed_file_ready = _signed_file_ready(record)
    signed_file_status = str(record.act_ddc_status or "pending")
    if record.act_status == "signed" and not signed_file_ready:
        status = "document_error" if signed_file_status == "error" else "document_building"
    else:
        status = (
            "signing"
            if active
            else "finalizing"
            if finalizing
            else "error"
            if record.act_session_status == "error" or expired
            else str(record.act_status)
        )
    if status == "document_building" and message is None:
        message = "Обе подписи проверены. SIGEX формирует PDF с подписями и QR…"
    elif status == "document_error" and message is None:
        message = (
            "Обе подписи сохранены. Не удалось сразу сформировать подписанный PDF; "
            f"сайт повторит попытку. {record.act_ddc_error or ''}"
        ).strip()
    return SelfEmployedActSessionRead(
        status=status,
        expire_at=record.act_session_expires_at if active else None,
        qr_code=qr if active else None,
        egov_mobile_url=record.act_egov_mobile_url if active else None,
        egov_business_url=record.act_egov_business_url if active else None,
        signed_file_ready=signed_file_ready,
        signed_file_status=signed_file_status,
        message=(
            message
            or record.act_signing_error
            or ("Сессия eGov истекла. Создайте новую попытку подписания." if expired else None)
        ),
    )


def _phone_for_inferred_role(db: Session, record: SelfEmployedAccounting, role: str) -> str:
    if role == "customer":
        return _whatsapp_phone(get_settings().R1_CUSTOMER_SIGNER_PHONE) or "77021123403"
    contact = _contact_for_iin(db, record.iin)
    return _whatsapp_phone(record.contractor_phone or (contact.whatsapp_phone if contact else None)) or ""


def _decode_signature(signature_b64: str) -> bytes:
    try:
        raw = base64.b64decode(re.sub(r"\s+", "", str(signature_b64 or "")), validate=True)
    except ValueError as exc:
        raise SigexError("Получена повреждённая CMS-подпись") from exc
    if len(raw) < 128:
        raise SigexError("Полученная CMS-подпись слишком короткая")
    return raw


def _expected_iins(record: SelfEmployedAccounting) -> tuple[str, str]:
    customer_iin = _digits(R1_CUSTOMER_PROFILE.get("bin_iin"))
    contractor_iin = _digits(record.iin)
    if len(customer_iin) != 12 or len(contractor_iin) != 12 or customer_iin == contractor_iin:
        raise SigexError("Не удалось определить корректные ИИН обеих сторон АВР")
    return customer_iin, contractor_iin


def _signer_role(record: SelfEmployedAccounting, signature_b64: str) -> tuple[str, str, str | None]:
    customer_iin, contractor_iin = _expected_iins(record)
    signer_iin, signer_name = cms_signer_identity(
        signature_b64,
        expected_iins=[customer_iin, contractor_iin],
    )
    if signer_iin == customer_iin:
        return "customer", signer_iin, signer_name
    if signer_iin == contractor_iin:
        return "contractor", signer_iin, signer_name
    raise SigexError("ИИН в ЭЦП не совпадает ни с ИП, ни с самозанятым в АВР")


def _stage_pending_signature(
    db: Session,
    record: SelfEmployedAccounting,
    signature_b64: str,
) -> bytes:
    raw_signature = _decode_signature(signature_b64)
    record.act_pending_signature_data = raw_signature
    record.act_pending_signature_sha256 = sha256(raw_signature).hexdigest()
    record.act_pending_signature_received_at = datetime.utcnow()
    record.act_session_status = "finalizing"
    record.act_signing_error = None
    record.updated_at = datetime.utcnow()
    db.add(record)
    return raw_signature


def _build_signed_ddc(accounting_id: int, *, force: bool = False) -> None:
    """Build and persist SIGEX DDC without ever rolling back valid CMS signatures."""
    if SessionLocal is None:
        return
    now = datetime.utcnow()
    with SessionLocal() as db:
        record = db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id == accounting_id)
            .with_for_update()
        ).scalar_one_or_none()
        if record is None or record.act_status != "signed" or _signed_file_ready(record):
            return
        last_attempt = record.act_ddc_last_attempt_at
        if (
            record.act_ddc_status == "building"
            and last_attempt
            and last_attempt > now - DDC_STALE_BUILD
        ):
            return
        if (
            not force
            and record.act_ddc_status == "error"
            and last_attempt
            and last_attempt > now - DDC_RETRY_COOLDOWN
        ):
            return
        row = db.execute(
            select(
                SelfEmployedAccounting.act_data,
                SelfEmployedAccounting.act_filename,
            ).where(SelfEmployedAccounting.id == record.id)
        ).one_or_none()
        if row is None or row.act_data is None:
            record.act_ddc_status = "error"
            record.act_ddc_error = "Исходный PDF АВР не найден в архиве"
            record.act_ddc_last_attempt_at = now
            db.add(record)
            db.commit()
            return
        document_id = str(record.act_sigex_document_id or "").strip()
        if not document_id:
            record.act_ddc_status = "error"
            record.act_ddc_error = "Не найден номер подписанного документа SIGEX"
            record.act_ddc_last_attempt_at = now
            db.add(record)
            db.commit()
            return
        pdf_data = bytes(row.act_data)
        source_filename = str(row.act_filename or record.act_number or "AVR.pdf")
        record.act_ddc_status = "building"
        record.act_ddc_error = None
        record.act_ddc_last_attempt_at = now
        record.updated_at = now
        db.add(record)
        db.commit()

    try:
        ddc_data = build_document_card(
            document_id=document_id,
            pdf_data=pdf_data,
            filename=source_filename,
        )
    except Exception as exc:
        message = str(exc)[:1000] or "SIGEX не сформировал подписанный PDF"
        with SessionLocal() as db:
            record = db.execute(
                select(SelfEmployedAccounting)
                .where(SelfEmployedAccounting.id == accounting_id)
                .with_for_update()
            ).scalar_one_or_none()
            if record is not None and not _signed_file_ready(record):
                record.act_ddc_status = "error"
                record.act_ddc_error = message
                record.updated_at = datetime.utcnow()
                db.add(record)
                db.commit()
        return

    generated_at = datetime.utcnow()
    with SessionLocal() as db:
        record = db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id == accounting_id)
            .with_for_update()
        ).scalar_one_or_none()
        if record is None or record.act_status != "signed":
            return
        stem = Path(source_filename).stem or "AVR"
        record.act_ddc_status = "ready"
        record.act_ddc_filename = f"{stem}_SIGNED_SIGEX.pdf"
        record.act_ddc_size = len(ddc_data)
        record.act_ddc_sha256 = sha256(ddc_data).hexdigest()
        record.act_ddc_data = ddc_data
        record.act_ddc_generated_at = generated_at
        record.act_ddc_error = None
        record.updated_at = generated_at
        db.add(record)
        db.commit()


def _ddc_worker(accounting_id: int, force: bool) -> None:
    try:
        _build_signed_ddc(accounting_id, force=force)
    finally:
        with _worker_lock:
            _active_ddc_workers.discard(accounting_id)


def _start_ddc_worker(accounting_id: int, *, force: bool = False) -> None:
    with _worker_lock:
        if accounting_id in _active_ddc_workers:
            return
        _active_ddc_workers.add(accounting_id)
    threading.Thread(target=_ddc_worker, args=(accounting_id, force), daemon=True).start()


def _finalize_pending_signature(accounting_id: int) -> None:
    if SessionLocal is None:
        return
    with SessionLocal() as db:
        record = db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id == accounting_id)
            .with_for_update()
        ).scalar_one_or_none()
        if record is None or not record.act_pending_signature_data:
            return
        raw_signature = bytes(record.act_pending_signature_data)
        signature_b64 = base64.b64encode(raw_signature).decode("ascii")
        signer_role, signer_iin, signer_name = _signer_role(record, signature_b64)
        target = db.execute(
            select(SelfEmployedActSignature)
            .where(
                SelfEmployedActSignature.accounting_id == record.id,
                SelfEmployedActSignature.signer_role == signer_role,
            )
            .with_for_update()
        ).scalar_one_or_none()
        pending_hash = sha256(raw_signature).hexdigest()
        if target is not None and target.status == "signed":
            if target.signature_sha256 == pending_hash:
                record.act_pending_signature_data = None
                record.act_pending_signature_sha256 = None
                record.act_pending_signature_received_at = None
                record.act_session_status = "idle"
                record.act_signing_error = None
                db.add(record)
                db.commit()
                if record.act_status == "signed" and not _signed_file_ready(record):
                    _start_ddc_worker(record.id, force=True)
                return
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
        target.signature_data = raw_signature
        target.signature_sha256 = pending_hash
        target.sigex_sign_id = sign_id
        target.signer_iin = signer_iin
        target.signer_name = signer_name
        target.signed_at = now
        target.status = "signed"
        target.last_error = None
        target.updated_at = now
        record.act_pending_signature_data = None
        record.act_pending_signature_sha256 = None
        record.act_pending_signature_received_at = None
        record.act_session_status = "idle"
        record.act_signing_error = None
        _signature_status(record, target)
        fully_signed = record.act_status == "signed"
        record.updated_at = now
        db.add_all([target, record])
        db.commit()
        if fully_signed:
            _build_signed_ddc(record.id, force=True)


def _mark_signature_error(accounting_id: int, exc: Exception) -> None:
    if SessionLocal is None:
        return
    message = str(exc)[:1000] or "Не удалось завершить подписание"
    with SessionLocal() as db:
        record = db.execute(
            select(SelfEmployedAccounting)
            .where(SelfEmployedAccounting.id == accounting_id)
            .with_for_update()
        ).scalar_one_or_none()
        if record is None or record.act_session_status not in {"signing", "finalizing", "error"}:
            return
        record.act_session_status = "error"
        record.act_signing_error = message
        record.updated_at = datetime.utcnow()
        if record.act_pending_signature_data:
            try:
                signature_b64 = base64.b64encode(bytes(record.act_pending_signature_data)).decode("ascii")
                signer_role, _, _ = _signer_role(record, signature_b64)
                target = _signature_for_role(record, signer_role)
                if target is not None and target.status != "signed":
                    target.status = "error"
                    target.last_error = message
                    target.updated_at = datetime.utcnow()
                    db.add(target)
            except Exception:
                pass
        db.add(record)
        db.commit()


def _process_signature(accounting_id: int) -> None:
    if SessionLocal is None:
        return
    try:
        with SessionLocal() as db:
            record = db.get(SelfEmployedAccounting, accounting_id)
            if record is None:
                return
            if record.act_pending_signature_data:
                signature_b64 = base64.b64encode(bytes(record.act_pending_signature_data)).decode("ascii")
            elif record.act_session_status == "signing":
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
            else:
                return

        with SessionLocal() as db:
            record = db.execute(
                select(SelfEmployedAccounting)
                .where(SelfEmployedAccounting.id == accounting_id)
                .with_for_update()
            ).scalar_one_or_none()
            if record is None:
                return
            if not record.act_pending_signature_data:
                if record.act_session_status != "signing":
                    return
                # Persist first. Certificate parsing and SIGEX registration are
                # deliberately performed only after this commit so neither an
                # unfamiliar certificate profile nor a temporary SIGEX error
                # can discard the CMS already returned by eGov.
                _stage_pending_signature(db, record, signature_b64)
                db.commit()
        _finalize_pending_signature(accounting_id)
    except Exception as exc:
        _mark_signature_error(accounting_id, exc)
    finally:
        with _worker_lock:
            _active_workers.discard(accounting_id)


def _finalize_worker(accounting_id: int) -> None:
    try:
        _finalize_pending_signature(accounting_id)
    except Exception as exc:
        _mark_signature_error(accounting_id, exc)
    finally:
        with _worker_lock:
            _active_finalizers.discard(accounting_id)


def _start_worker(accounting_id: int) -> None:
    with _worker_lock:
        if accounting_id in _active_workers:
            return
        _active_workers.add(accounting_id)
    threading.Thread(target=_process_signature, args=(accounting_id,), daemon=True).start()


def _start_finalize_worker(accounting_id: int) -> None:
    with _worker_lock:
        if accounting_id in _active_finalizers:
            return
        _active_finalizers.add(accounting_id)
    threading.Thread(target=_finalize_worker, args=(accounting_id,), daemon=True).start()


@public_router.post("/{token}/session", response_model=SelfEmployedActSessionRead)
def start_act_session(token: str, request: Request, db: Session = Depends(get_db)):
    record = _record_by_token(db, token, lock=True)
    _public_info(record)
    if record.act_status == "signed":
        if not _signed_file_ready(record):
            _start_ddc_worker(record.id)
        return _session_read(record)
    customer_iin = _digits(R1_CUSTOMER_PROFILE.get("bin_iin"))
    contractor_iin = _digits(record.iin)
    if len(customer_iin) != 12 or len(contractor_iin) != 12 or customer_iin == contractor_iin:
        raise HTTPException(status_code=400, detail="Не удалось определить корректные ИИН обеих сторон АВР")
    now = datetime.utcnow()
    if record.act_pending_signature_data:
        record.act_session_status = "finalizing"
        record.act_signing_error = None
        record.updated_at = now
        db.add(record)
        db.commit()
        result = _session_read(record, "Подпись уже получена. Завершаем её проверку и сохранение…")
        _start_finalize_worker(record.id)
        return result
    if (
        record.act_session_status == "error"
        and record.act_session_expires_at
        and record.act_session_expires_at > now
        and record.act_sigex_data_url
        and record.act_sigex_sign_url
        and "отменено" not in str(record.act_signing_error or "").lower()
    ):
        # A network interruption may happen after the person has already
        # signed in eGov. Reuse the still-valid one-time operation and retrieve
        # its result instead of forcing a second signature.
        record.act_session_status = "signing"
        record.act_signing_error = None
        record.updated_at = now
        db.add(record)
        db.commit()
        result = _session_read(record, "Повторно получаем уже выполненную подпись из eGov…")
        _start_worker(record.id)
        return result
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


@public_router.post("/{token}/ncalayer", response_model=SelfEmployedActSessionRead)
def submit_ncalayer_signature(
    token: str,
    payload: SelfEmployedActCmsCreate,
    db: Session = Depends(get_db),
):
    record = _record_by_token(db, token, lock=True)
    _public_info(record)
    if record.act_status == "signed":
        if not _signed_file_ready(record):
            _start_ddc_worker(record.id)
        return _session_read(record)
    try:
        _signer_role(record, payload.signature)
        _stage_pending_signature(db, record, payload.signature)
    except SigexError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    result = _session_read(record, "ЭЦП получена. Проверяем сертификат и сохраняем подпись…")
    _start_finalize_worker(record.id)
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
    elif record.act_session_status == "finalizing" and record.act_pending_signature_data:
        _start_finalize_worker(record.id)
    elif record.act_status == "signed" and not _signed_file_ready(record):
        _start_ddc_worker(record.id)
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
            "Content-Security-Policy": (
                "default-src 'self' data:; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self' wss://127.0.0.1:13579 https://127.0.0.1:24680; "
                "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
            ),
        },
    )
