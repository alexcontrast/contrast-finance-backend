from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthBootstrapAdminRequest, AuthLoginRequest, AuthPermissionsRead, AuthTokenRead, AuthUserRead
from app.services.auth import create_access_token, find_login_user, get_current_user, native_pin_hash, normalize_phone, verify_pin


router = APIRouter(prefix="/auth", tags=["auth"])


def user_to_auth_read(user: User) -> AuthUserRead:
    return AuthUserRead(
        id=user.id,
        name=user.name,
        phone=user.phone,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role=user.role,
        is_active=user.is_active,
        legacy_user_id=user.legacy_user_id,
        auth_source=user.auth_source or "legacy_apps_script",
    )


@router.post("/login", response_model=AuthTokenRead)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)):
    user = find_login_user(db, payload.name, payload.phone)

    if user is None:
        raise HTTPException(status_code=401, detail="Неверное имя/телефон или PIN")

    if not verify_pin(user, payload.pin):
        raise HTTPException(status_code=401, detail="Неверное имя/телефон или PIN")

    token = create_access_token(user)

    return AuthTokenRead(
        access_token=token,
        token_type="bearer",
        user=user_to_auth_read(user),
    )


@router.get("/me", response_model=AuthUserRead)
def me(user: User = Depends(get_current_user)):
    return user_to_auth_read(user)



@router.post("/bootstrap-admin", response_model=AuthTokenRead)
def bootstrap_admin(payload: AuthBootstrapAdminRequest, db: Session = Depends(get_db)):
    """
    One-time helper for first admin creation.

    Works only if there is no active admin in the database.
    After that it returns 403.
    """
    existing_admin = db.execute(
        select(User).where(User.role == "admin", User.is_active == True)  # noqa: E712
    ).scalars().first()

    if existing_admin is not None:
        raise HTTPException(status_code=403, detail="Admin already exists")

    name = str(payload.name or "").strip()
    pin = str(payload.pin or "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    if len(pin) < 4:
        raise HTTPException(status_code=400, detail="PIN должен быть минимум 4 символа")

    user = User(
        name=name,
        phone=normalize_phone(payload.phone) or None,
        department_id=None,
        role="admin",
        is_active=True,
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

    token = create_access_token(user)

    return AuthTokenRead(
        access_token=token,
        token_type="bearer",
        user=user_to_auth_read(user),
    )



@router.get("/permissions", response_model=AuthPermissionsRead)
def permissions(user: User = Depends(get_current_user)):
    return AuthPermissionsRead(
        can_view_admin_dashboard=user.role == "admin",
        can_manage_users=user.role == "admin",
        can_view_department_dashboard=user.role in {"admin", "department_head"},
        can_edit=user.role in {"admin", "manager"},
    )
