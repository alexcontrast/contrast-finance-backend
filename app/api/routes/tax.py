from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.contractor import Contractor
from app.models.event_item import EventItem
from app.models.taxpayer_check import TaxpayerCheck
from app.schemas.tax import ManualTaxRequest, TaxCheckRequest, TaxResult
from app.services.kgd.client import check_taxpayer


router = APIRouter(tags=["tax"])


def calculate_tax_values(amount_base: Decimal, tax_status: str) -> tuple[Decimal, Decimal]:
    """
    Возвращает:
    - НДС
    - Вычеты
    """
    if amount_base is None:
        amount_base = Decimal("0.00")

    if tax_status == "our_vat":
        # Подрядчик ОУР с НДС:
        # НДС в Казахстане = 16%.
        # Если сумма позиции уже включает НДС:
        # - сумма без НДС = amount / 1.16
        # - НДС = amount - сумма без НДС
        # - Вычеты = 10% от суммы без НДС
        amount_without_vat = amount_base / Decimal("1.16")
        vat = amount_base - amount_without_vat
        deduction = amount_without_vat * Decimal("0.10")
        return vat.quantize(Decimal("0.01")), deduction.quantize(Decimal("0.01"))

    if tax_status == "our_no_vat":
        return Decimal("0.00"), (amount_base * Decimal("0.10")).quantize(Decimal("0.01"))

    if tax_status == "self_employed":
        return Decimal("0.00"), (amount_base * Decimal("0.10")).quantize(Decimal("0.01"))

    # simplified / snr / not_found
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
):
    """
    Проверка BIN / ИИН через KGD service.

    KGD_MODE=stub:
    - безопасная тестовая заглушка

    KGD_MODE=live:
    - реальные запросы в КГД через X-Portal-Token
    """
    item = db.get(EventItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Event item not found")

    try:
        kgd_result = check_taxpayer(payload.iin_bin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    before = {
        "iin_bin": item.iin_bin,
        "iin_bin_locked": item.iin_bin_locked,
        "tax_check_status": item.tax_check_status,
        "vat_amount": str(item.vat_amount),
        "deduction_amount": str(item.deduction_amount),
    }

    amount_base = get_amount_base(item)
    vat_amount, deduction_amount = calculate_tax_values(amount_base, kgd_result.tax_status)

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

    write_audit_log(
        db=db,
        user_id=None,
        entity_type="event_item",
        entity_id=item.id,
        action=f"tax_checked_{kgd_result.source}",
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
        source=kgd_result.source,
        message=kgd_result.message,
    )


@router.patch("/event-items/{item_id}/tax/manual", response_model=TaxResult)
def set_event_item_tax_manual(
    item_id: int,
    payload: ManualTaxRequest,
    admin_user_id: int,
    db: Session = Depends(get_db),
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
