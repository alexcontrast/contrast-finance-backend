from datetime import datetime
from decimal import Decimal
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.contractor import Contractor
from app.models.event_item import EventItem
from app.models.taxpayer_check import TaxpayerCheck
from app.models.user import User
from app.schemas.tax import ManualTaxRequest, TaxCheckRequest, TaxResult
from app.schemas.event_item import EventItemCreate, EventItemRead
from app.services.kgd.client import check_taxpayer
from app.services.auth import get_current_user
from app.services.authorization import get_event_or_404, require_event_edit, require_item_event_edit


router = APIRouter(tags=["tax"])
logger = logging.getLogger(__name__)


class EventItemTaxCheckCreatePayload(BaseModel):
    item: EventItemCreate
    iin_bin: str


class EventItemTaxCheckCreateResult(BaseModel):
    item: EventItemRead
    tax: TaxResult


def calculate_external_amount_from_item_payload(payload: EventItemCreate) -> Decimal:
    price = payload.external_price or Decimal("0.00")
    quantity = payload.external_quantity or Decimal("1.00")
    days = payload.external_days or Decimal("1.00")
    return price * quantity * days


def _perf_delta(marks: dict[str, float], start_name: str, end_name: str) -> float:
    return marks[end_name] - marks[start_name]


def _mask_iin_bin(value: str | None) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(digits) <= 4:
        return "***"
    return f"***{digits[-4:]}"


def calculate_tax_values(amount_base: Decimal, tax_status: str) -> tuple[Decimal, Decimal]:
    """
    Возвращает:
    - НДС
    - Вычеты
    """
    if amount_base is None:
        amount_base = Decimal("0.00")

    settings = get_settings()
    vat_rate = settings.VAT_RATE
    deduction_rate = settings.CONTRACTOR_DEDUCTION_RATE

    if tax_status == "our_vat":
        amount_without_vat = amount_base / (Decimal("1.00") + vat_rate)
        vat = amount_base - amount_without_vat
        deduction = amount_without_vat * deduction_rate
        return vat.quantize(Decimal("0.01")), deduction.quantize(Decimal("0.01"))

    if tax_status == "our_no_vat":
        return Decimal("0.00"), (amount_base * deduction_rate).quantize(Decimal("0.01"))

    if tax_status == "self_employed":
        return Decimal("0.00"), (amount_base * deduction_rate).quantize(Decimal("0.01"))

    return Decimal("0.00"), Decimal("0.00")

def get_amount_base(item: EventItem) -> Decimal:
    return item.amount_fact if item.amount_fact is not None else item.external_amount


def upsert_contractor(
    db: Session,
    iin_bin: str,
    tax_status: str,
    vat_amount: Decimal,
    deduction_amount: Decimal,
    source: str,
    contractor_name: str | None = None,
) -> Contractor:
    contractor = db.query(Contractor).filter(Contractor.iin_bin == iin_bin).first()

    if contractor is None:
        contractor = Contractor(
            iin_bin=iin_bin,
            name=contractor_name,
            tax_status=tax_status,
            vat_status="vat" if tax_status == "our_vat" else "no_vat",
            vat_amount=vat_amount,
            deduction_amount=deduction_amount,
            source=source,
            last_checked_at=datetime.utcnow(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(contractor)
        db.flush()
        return contractor

    contractor.name = contractor_name or contractor.name
    contractor.tax_status = tax_status
    contractor.vat_status = "vat" if tax_status == "our_vat" else "no_vat"
    contractor.vat_amount = vat_amount
    contractor.deduction_amount = deduction_amount
    contractor.source = source
    contractor.last_checked_at = datetime.utcnow()
    contractor.updated_at = datetime.utcnow()
    db.add(contractor)
    db.flush()
    return contractor


def write_taxpayer_check(
    db: Session,
    contractor: Contractor | None,
    iin_bin: str,
    tax_status: str,
    source: str,
    status: str,
    message: str,
    raw_response: dict | None = None,
    manual_set_by_user_id: int | None = None,
):
    check = TaxpayerCheck(
        contractor_id=contractor.id if contractor else None,
        iin_bin=iin_bin,
        name_result=contractor.name if contractor else None,
        tax_status_result=tax_status,
        vat_status_result="vat" if tax_status == "our_vat" else "no_vat",
        status=status,
        source=source,
        raw_response_json=raw_response,
        error_message=None if status in {"success", "manual"} else message,
        manual_set_by_user_id=manual_set_by_user_id,
        checked_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(check)


def write_audit_log(
    db: Session,
    user_id: int | None,
    entity_type: str,
    entity_id: int,
    action: str,
    before_json: dict | None,
    after_json: dict | None,
):
    log = AuditLog(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=before_json,
        after_json=after_json,
        created_at=datetime.utcnow(),
    )
    db.add(log)


@router.post("/event-items/{item_id}/tax/check", response_model=TaxResult)
def check_event_item_tax(
    item_id: int,
    payload: TaxCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Проверка BIN / ИИН через KGD service.

    KGD_MODE=stub:
    - безопасная тестовая заглушка

    KGD_MODE=live:
    - реальные запросы в КГД через X-Portal-Token
    """
    perf_started_at = time.perf_counter()
    perf_marks = {"start": perf_started_at}

    def mark_perf(name: str) -> None:
        perf_marks[name] = time.perf_counter()

    item = db.get(EventItem, item_id)
    mark_perf("item_sql")
    if item is None:
        raise HTTPException(status_code=404, detail="Event item not found")

    require_item_event_edit(db, current_user, item)
    mark_perf("auth")

    try:
        kgd_result = check_taxpayer(payload.iin_bin)
    except ValueError as exc:
        mark_perf("kgd_error")
        logger.warning(
            "PERF kgd-tax-check item_id=%s user_id=%s role=%s iin_bin=%s error=validation item_sql=%.3fs auth=%.3fs kgd=%.3fs total=%.3fs",
            item_id,
            getattr(current_user, "id", None),
            getattr(current_user, "role", None),
            _mask_iin_bin(payload.iin_bin),
            _perf_delta(perf_marks, "start", "item_sql"),
            _perf_delta(perf_marks, "item_sql", "auth"),
            _perf_delta(perf_marks, "auth", "kgd_error"),
            perf_marks["kgd_error"] - perf_started_at,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    mark_perf("kgd_check")

    before = {
        "iin_bin": item.iin_bin,
        "iin_bin_locked": item.iin_bin_locked,
        "tax_check_status": item.tax_check_status,
        "vat_amount": str(item.vat_amount),
        "deduction_amount": str(item.deduction_amount),
    }

    amount_base = get_amount_base(item)
    vat_amount, deduction_amount = calculate_tax_values(amount_base, kgd_result.tax_status)
    mark_perf("tax_values")

    if kgd_result.tax_status == "not_found":
        item.iin_bin = kgd_result.iin_bin
        item.iin_bin_locked = False
        item.tax_check_status = "not_found"
        item.vat_amount = Decimal("0.00")
        item.deduction_amount = Decimal("0.00")
        item.updated_at = datetime.utcnow()

        write_taxpayer_check(
            db=db,
            contractor=None,
            iin_bin=kgd_result.iin_bin,
            tax_status=kgd_result.tax_status,
            source=kgd_result.source,
            status="not_found",
            message=kgd_result.message,
            raw_response=kgd_result.raw_response,
        )
    else:
        contractor = upsert_contractor(
            db=db,
            iin_bin=kgd_result.iin_bin,
            tax_status=kgd_result.tax_status,
            vat_amount=vat_amount,
            deduction_amount=deduction_amount,
            source=kgd_result.source,
            contractor_name=kgd_result.contractor_name,
        )

        item.iin_bin = kgd_result.iin_bin
        item.iin_bin_locked = True
        item.tax_check_status = kgd_result.tax_status
        item.vat_amount = vat_amount
        item.deduction_amount = deduction_amount
        item.updated_at = datetime.utcnow()

        write_taxpayer_check(
            db=db,
            contractor=contractor,
            iin_bin=kgd_result.iin_bin,
            tax_status=kgd_result.tax_status,
            source=kgd_result.source,
            status="success",
            message=kgd_result.message,
            raw_response=kgd_result.raw_response,
        )

    after = {
        "iin_bin": item.iin_bin,
        "iin_bin_locked": item.iin_bin_locked,
        "tax_check_status": item.tax_check_status,
        "vat_amount": str(item.vat_amount),
        "deduction_amount": str(item.deduction_amount),
    }

    mark_perf("db_prepare")

    write_audit_log(
        db=db,
        user_id=None,
        entity_type="event_item",
        entity_id=item.id,
        action=f"tax_checked_{kgd_result.source}",
        before_json=before,
        after_json=after,
    )
    mark_perf("audit")

    result_payload = TaxResult(
        item_id=item.id,
        iin_bin=item.iin_bin,
        iin_bin_locked=item.iin_bin_locked,
        tax_check_status=item.tax_check_status,
        vat_amount=item.vat_amount,
        deduction_amount=item.deduction_amount,
        source=kgd_result.source,
        message=kgd_result.message,
    )

    db.add(item)
    db.commit()
    mark_perf("commit")
    # Не делаем db.refresh(item): все поля для ответа уже известны.
    # На Railway это стабильно экономило около 0.4–0.5 секунды на каждой КГД-проверке.
    mark_perf("refresh")

    kgd_perf = getattr(kgd_result, "perf", None) or {}
    logger.warning(
        "PERF kgd-tax-check item_id=%s user_id=%s role=%s iin_bin=%s source=%s tax_status=%s "
        "item_sql=%.3fs auth=%.3fs kgd=%.3fs tax_values=%.3fs db_prepare=%.3fs audit=%.3fs commit=%.3fs refresh=%.3fs total=%.3fs "
        "client_total=%.3fs snr_http=%.3fs vat_http=%.3fs http_total=%.3fs detect=%.3fs snr_ok=%s vat_ok=%s",
        result_payload.item_id,
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
        _mask_iin_bin(kgd_result.iin_bin),
        kgd_result.source,
        kgd_result.tax_status,
        _perf_delta(perf_marks, "start", "item_sql"),
        _perf_delta(perf_marks, "item_sql", "auth"),
        _perf_delta(perf_marks, "auth", "kgd_check"),
        _perf_delta(perf_marks, "kgd_check", "tax_values"),
        _perf_delta(perf_marks, "tax_values", "db_prepare"),
        _perf_delta(perf_marks, "db_prepare", "audit"),
        _perf_delta(perf_marks, "audit", "commit"),
        _perf_delta(perf_marks, "commit", "refresh"),
        perf_marks["refresh"] - perf_started_at,
        float(kgd_perf.get("total_sec") or 0),
        float(kgd_perf.get("snr_http_sec") or 0),
        float(kgd_perf.get("vat_http_sec") or 0),
        float(kgd_perf.get("http_total_sec") or 0),
        float(kgd_perf.get("detect_sec") or 0),
        kgd_perf.get("snr_ok"),
        kgd_perf.get("vat_ok"),
    )

    return result_payload


@router.post("/events/{event_id}/items/tax/check", response_model=EventItemTaxCheckCreateResult)
def create_event_item_and_check_tax(
    event_id: int,
    payload: EventItemTaxCheckCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создаёт новую позицию и сразу делает live-проверку КГД одним запросом.

    Важно: это НЕ кэш. КГД всё равно вызывается live каждый раз.
    Экономия только на том, что фронт больше не делает два отдельных round-trip:
    POST /events/{id}/items + POST /event-items/{id}/tax/check.
    """
    started_at = time.perf_counter()

    event = get_event_or_404(db, event_id)
    require_event_edit(current_user, event)
    auth_sec = time.perf_counter() - started_at

    item_payload = payload.item
    normalized_iin_bin = "".join(ch for ch in (payload.iin_bin or item_payload.iin_bin or "") if ch.isdigit())
    if len(normalized_iin_bin) != 12:
        raise HTTPException(status_code=400, detail="BIN / ИИН должен содержать 12 цифр")

    item = EventItem(
        event_id=event_id,
        item_type=item_payload.item_type,
        external_name=item_payload.external_name,
        external_price=item_payload.external_price,
        external_quantity=item_payload.external_quantity,
        external_days=item_payload.external_days,
        external_amount=calculate_external_amount_from_item_payload(item_payload),
        external_note=item_payload.external_note,
        amount_fact=item_payload.amount_fact,
        paid_amount=item_payload.paid_amount,
        payment_method="invoice",
        iin_bin=normalized_iin_bin,
        iin_bin_locked=False,
        tax_check_status=None,
        vat_amount=Decimal("0.00"),
        deduction_amount=Decimal("0.00"),
        internal_note=item_payload.internal_note,
        sort_order=item_payload.sort_order,
        is_deleted=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(item)
    db.flush()
    create_flush_sec = time.perf_counter() - started_at - auth_sec

    tax_started_at = time.perf_counter()
    tax_result = check_event_item_tax(
        item.id,
        TaxCheckRequest(iin_bin=normalized_iin_bin),
        db,
        current_user,
    )
    tax_sec = time.perf_counter() - tax_started_at

    # check_event_item_tax уже сделал commit; item содержит актуальные tax-поля.
    item_read = EventItemRead.model_validate(item)

    logger.warning(
        "PERF event-item-create-tax-check event_id=%s item_id=%s user_id=%s role=%s auth=%.3fs create_flush=%.3fs tax_total=%.3fs total=%.3fs",
        event_id,
        item.id,
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
        auth_sec,
        create_flush_sec,
        tax_sec,
        time.perf_counter() - started_at,
    )

    return EventItemTaxCheckCreateResult(item=item_read, tax=tax_result)


@router.patch("/event-items/{item_id}/tax/manual", response_model=TaxResult)
def set_event_item_tax_manual(
    item_id: int,
    payload: ManualTaxRequest,
    admin_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ручная правка налогового режима админом.

    Используется, если КГД не ответил или BIN не найден.
    """
    item = db.get(EventItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Event item not found")

    allowed = {"our_vat", "our_no_vat", "simplified", "snr", "self_employed", "not_found"}
    if payload.tax_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail="tax_status должен быть our_vat, our_no_vat, simplified, snr, self_employed или not_found",
        )

    if not item.iin_bin:
        raise HTTPException(status_code=400, detail="Сначала укажи BIN / ИИН в позиции или через tax/check")

    before = {
        "iin_bin": item.iin_bin,
        "iin_bin_locked": item.iin_bin_locked,
        "tax_check_status": item.tax_check_status,
        "vat_amount": str(item.vat_amount),
        "deduction_amount": str(item.deduction_amount),
    }

    amount_base = get_amount_base(item)
    vat_amount, deduction_amount = calculate_tax_values(amount_base, payload.tax_status)

    contractor = upsert_contractor(
        db=db,
        iin_bin=item.iin_bin,
        tax_status=payload.tax_status,
        vat_amount=vat_amount,
        deduction_amount=deduction_amount,
        source="manual",
        contractor_name=None,
    )

    item.iin_bin_locked = True
    item.tax_check_status = payload.tax_status
    item.vat_amount = vat_amount
    item.deduction_amount = deduction_amount
    item.updated_at = datetime.utcnow()

    write_taxpayer_check(
        db=db,
        contractor=contractor,
        iin_bin=item.iin_bin,
        tax_status=payload.tax_status,
        source="manual",
        status="manual",
        message="Налоговый режим проставлен вручную админом",
        raw_response={"manual": True},
        manual_set_by_user_id=admin_user_id,
    )

    after = {
        "iin_bin": item.iin_bin,
        "iin_bin_locked": item.iin_bin_locked,
        "tax_check_status": item.tax_check_status,
        "vat_amount": str(item.vat_amount),
        "deduction_amount": str(item.deduction_amount),
    }

    write_audit_log(
        db=db,
        user_id=admin_user_id,
        entity_type="event_item",
        entity_id=item.id,
        action="tax_set_manual",
        before_json=before,
        after_json=after,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return TaxResult(
        item_id=item.id,
        iin_bin=item.iin_bin,
        iin_bin_locked=item.iin_bin_locked,
        tax_check_status=item.tax_check_status,
        vat_amount=item.vat_amount,
        deduction_amount=item.deduction_amount,
        source="manual",
        message="Налоговый режим проставлен вручную админом",
    )
