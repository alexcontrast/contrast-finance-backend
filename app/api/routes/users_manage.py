from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.users_manage import NativeUserCreate, UserPinUpdate, UserRead, UserRoleUpdate
from app.services.auth import native_pin_hash, normalize_phone, require_roles


router = APIRouter(tags=["users_manage"])


ALLOWED_ROLES = {"admin", "manager", "department_head", "accountant"}


def validate_role(role: str) -> str:
    role = str(role or "").strip()

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="role должен быть admin, manager, department_head или accountant",
        )

    return role


def user_to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        phone=user.phone,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role=user.role,
        is_active=user.is_active,
        legacy_user_id=user.legacy_user_id,
        auth_source=user.auth_source or "legacy_apps_script",
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def ensure_department_exists(db: Session, department_id: int | None) -> None:
    if department_id is None:
        return

    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=400, detail="Department not found")


def find_user_by_name_or_phone(db: Session, name: str, phone: str | None) -> User | None:
    conditions = [User.name == name]
    if phone:
        conditions.append(User.phone == phone)

    return db.execute(select(User).where(or_(*conditions))).scalars().first()


@router.get("/users", response_model=list[UserRead])
def list_users(
    role: str | None = None,
    department_id: int | None = None,
    include_inactive: bool = True,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    query = select(User)

    if role:
        query = query.where(User.role == role)

    if department_id is not None:
        query = query.where(User.department_id == department_id)

    if not include_inactive:
        query = query.where(User.is_active == True)  # noqa: E712

    users = db.execute(query.order_by(User.department_id, User.role, User.name)).scalars().all()
    return [user_to_read(user) for user in users]


@router.post("/users/native", response_model=UserRead)
def create_native_user(
    payload: NativeUserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    role = validate_role(payload.role)
    ensure_department_exists(db, payload.department_id)

    name = str(payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    pin = str(payload.pin or "").strip()
    if len(pin) < 4:
        raise HTTPException(status_code=400, detail="PIN должен быть минимум 4 символа")

    phone = normalize_phone(payload.phone) or None

    existing = find_user_by_name_or_phone(db, name, phone)

    if existing is not None and existing.is_active:
        raise HTTPException(status_code=400, detail="Активный пользователь с таким именем или телефоном уже есть")

    if existing is not None and not existing.is_active:
        user = existing
        user.name = name
        user.phone = phone or user.phone
        user.department_id = payload.department_id
        user.role = role
        user.is_active = payload.is_active

        user.legacy_user_id = None
        user.legacy_pin_hash = None
        user.auth_source = "native"
        user.updated_at = datetime.utcnow()

        db.add(user)
        db.flush()

        user.pin_hash = native_pin_hash(pin, user.id)
        db.add(user)
        db.commit()
        db.refresh(user)

        return user_to_read(user)

    user = User(
        name=name,
        phone=phone,
        department_id=payload.department_id,
        role=role,
        is_active=payload.is_active,
        legacy_user_id=None,
        legacy_pin_hash=None,
        auth_source="native",
        pin_hash=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(user)
    db.flush()

    user.pin_hash = native_pin_hash(pin, user.id)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user_to_read(user)


@router.patch("/users/{user_id}/role", response_model=UserRead)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    role = validate_role(payload.role)
    ensure_department_exists(db, payload.department_id)

    user.role = role
    user.department_id = payload.department_id

    if payload.is_active is not None:
        user.is_active = payload.is_active

    user.updated_at = datetime.utcnow()

    db.add(user)
    db.commit()
    db.refresh(user)

    return user_to_read(user)


@router.patch("/users/{user_id}/pin", response_model=UserRead)
def update_user_pin(
    user_id: int,
    payload: UserPinUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    pin = str(payload.pin or "").strip()
    if len(pin) < 4:
        raise HTTPException(status_code=400, detail="PIN должен быть минимум 4 символа")

    user.pin_hash = native_pin_hash(pin, user.id)
    user.auth_source = "native" if not user.legacy_user_id else user.auth_source
    user.updated_at = datetime.utcnow()

    db.add(user)
    db.commit()
    db.refresh(user)

    return user_to_read(user)
