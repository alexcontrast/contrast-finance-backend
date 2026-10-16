"""Portable signed source + detached CMS, independent of SIGEX's paid DDC API."""
import hashlib
import io
import json
import zipfile
from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from app.models.self_employed_accounting import SelfEmployedAccounting
from app.models.self_employed_act_signature import SelfEmployedActSignature


def signed_archive_response(db, record):
    if record.act_status != "signed":
        raise HTTPException(status_code=409, detail="Нужны подтверждённые подписи обеих сторон")
    pdf = db.execute(select(SelfEmployedAccounting.act_data).where(SelfEmployedAccounting.id == record.id)).scalar_one()
    signatures = db.execute(select(SelfEmployedActSignature).where(
        SelfEmployedActSignature.accounting_id == record.id,
        SelfEmployedActSignature.status == "signed")).scalars().all()
    if not pdf or {s.signer_role for s in signatures} != {"customer", "contractor"}:
        raise HTTPException(status_code=409, detail="Подписанный комплект неполон. Обратитесь к администратору")
    files = {"AVR_original.pdf": bytes(pdf)}
    manifest = {"format": "Contrast Finance signed act package v1", "act_number": record.act_number,
                "sigex_document_id": record.act_sigex_document_id, "signatures": []}
    for signature in signatures:
        content = bytes(signature.signature_data or b"")
        if not content or hashlib.sha256(content).hexdigest() != signature.signature_sha256:
            raise HTTPException(status_code=409, detail="Не совпал контрольный хеш сохранённой подписи")
        filename = f"signature_{signature.signer_role}.cms"
        files[filename] = content
        manifest["signatures"].append({"file": filename, "role": signature.signer_role,
            "iin": signature.signer_iin, "name": signature.signer_name,
            "signed_at": signature.signed_at.isoformat() if signature.signed_at else None,
            "sigex_sign_id": signature.sigex_sign_id})
    pdf_hash = hashlib.sha256(files["AVR_original.pdf"]).hexdigest()
    if record.act_sha256 and pdf_hash != record.act_sha256:
        raise HTTPException(status_code=409, detail="Не совпал контрольный хеш исходного АВР")
    manifest["sha256"] = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    files["README.txt"] = (
        "Комплект электронного АВР\n"
        "AVR_original.pdf — неизменённый исходный документ.\n"
        "signature_customer.cms и signature_contractor.cms — отдельные электронные подписи.\n"
        "Проверяйте каждую CMS вместе с исходным PDF в совместимом проверочном сервисе НУЦ РК/SIGEX.\n"
        "Хеши в manifest.json служат для контроля целостности; сами по себе они не подтверждают ЭЦП.\n"
        "Исходный PDF без CMS не является полным подписанным комплектом.\n"
        "Этот ZIP не является визуальной карточкой DDC и не добавляет нарисованные подписи в PDF.\n"
    ).encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0)), data)
    return Response(output.getvalue(), media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="AVR_{record.id}_SIGNED_PACKAGE.zip"',
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
