from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.users_import import LegacyUsersImportRequest, LegacyUsersImportResult
from app.services.auth import normalize_phone, require_roles


router = APIRouter(tags=["users_import"])


def role_from_legacy(value: str | None) -> str:
    raw = str(value or "").strip().lower()

    if raw in {"админ", "admin"}:
        return "admin"

    if raw in {"руководитель", "руководитель отдела", "department_head", "head"}:
        return "department_head"

    if raw in {"бухгалтер", "accountant"}:
        return "accountant"

    return "manager"


def active_from_legacy(value) -> bool:
    if isinstance(value, bool):
        return value

    raw = str(value or "").strip().lower()
    return raw not in {"удален", "удалён", "deleted", "inactive", "false", "0"}


def get_department_id(db: Session, department_id: int | None, department_name: str | None) -> int | None:
    if department_id:
        return department_id

    name = str(department_name or "").strip()
    if not name:
        return None

    department = db.execute(select(Department).where(Department.name == name)).scalar_one_or_none()
    return department.id if department else None


@router.post("/users/import-legacy", response_model=LegacyUsersImportResult)
def import_legacy_users(
    payload: LegacyUsersImportRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    created = 0
    updated = 0
    skipped = 0

    for row in payload.users:
        legacy_user_id = str(row.legacy_user_id or "").strip()
        name = str(row.name or "").strip()
        legacy_pin_hash = str(row.legacy_pin_hash or "").strip()

        if not legacy_user_id or not name or not legacy_pin_hash:
            skipped += 1
            continue

        department_id = get_department_id(db, row.department_id, row.department_name)

        user = db.execute(select(User).where(User.legacy_user_id == legacy_user_id)).scalar_one_or_none()
        if user is None:
            user = User(
                legacy_user_id=legacy_user_id,
                name=name,
                phone=normalize_phone(row.phone) or None,
                department_id=department_id,
                role=role_from_legacy(row.role),
                is_active=active_from_legacy(row.is_active),
                legacy_pin_hash=legacy_pin_hash,
                auth_source="legacy_apps_script",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            created += 1
        else:
            user.name = name
            user.phone = normalize_phone(row.phone) or user.phone
            user.department_id = department_id
            user.role = role_from_legacy(row.role)
            user.is_active = active_from_legacy(row.is_active)
            user.legacy_pin_hash = legacy_pin_hash
            user.auth_source = "legacy_apps_script"
            user.updated_at = datetime.utcnow()
            db.add(user)
            updated += 1

    db.commit()

    return LegacyUsersImportResult(created=created, updated=updated, skipped=skipped)
