from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.auth import AuthChangePinRequest, AuthLoginRequest, AuthPermissionsRead, AuthProfileUpdateRequest, AuthTokenRead, AuthUserRead
from app.services.auth import create_access_token, find_login_user, get_current_user, native_pin_hash, verify_pin, consume_login_attempt, normalize_phone, require_unique_user_identity


def permissions_for_user(user: User) -> AuthPermissionsRead:
    role = user.role

    if role == "admin":
        return AuthPermissionsRead(
            can_view_admin=True,
            can_manage_users=True,
            can_manage_settings=True,
            can_manage_monthly_plans=True,
            can_manage_monthly_expenses=True,
            can_view_department_dashboard=True,
            can_create_events=True,
            can_edit_events=True,
            can_create_payment_requests=True,
            can_manage_payment_requests=True,
        )

    if role == "department_head":
        return AuthPermissionsRead(
            can_view_department_dashboard=True,
        )

    if role == "manager":
        return AuthPermissionsRead(
            can_create_events=True,
            can_edit_events=True,
            can_create_payment_requests=True,
        )

    return AuthPermissionsRead()



router = APIRouter(prefix="/auth", tags=["auth"])


def user_to_auth_read(user: User) -> AuthUserRead:
    return AuthUserRead(
        id=user.id,
        name=user.name,
        phone=user.phone,
        email=user.email,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role=user.role,
        is_active=user.is_active,
        legacy_user_id=user.legacy_user_id,
        auth_source=user.auth_source or "legacy_apps_script",
        permissions=permissions_for_user(user),
    )


def find_admin_by_pin(db: Session, pin: str) -> User | None:
    admins = db.execute(
        select(User).where(User.role == "admin", User.is_active == True)  # noqa: E712
    ).scalars().all()

    for admin in admins:
        if verify_pin(admin, pin):
            return admin

    return None


def find_department_head_user(db: Session, name: str | None) -> User | None:
    name_clean = str(name or "").strip()
    if not name_clean:
        return None

    user = find_login_user(db, name_clean, None)
    return user if user and user.role == "department_head" else None


@router.post("/login", response_model=AuthTokenRead)
def login(payload: AuthLoginRequest, request: Request, db: Session = Depends(get_db)):
    auth_mode = str(payload.auth_mode or "manager").strip()
    if auth_mode not in {"manager", "admin", "department_head", "accountant"}:
        raise HTTPException(status_code=401, detail="Неверный тип входа")
    peer = request.client.host if request.client else "unknown"
    consume_login_attempt(db, f"ip:{peer}", 100)
    identity = normalize_phone(payload.phone) or str(payload.name or "").strip().casefold()
    consume_login_attempt(db, f"account:{auth_mode}:{identity}", 12)

    if auth_mode == "admin":
        user = find_admin_by_pin(db, payload.pin)
    elif auth_mode == "department_head":
        user = find_department_head_user(db, payload.name)
    else:
        user = find_login_user(db, payload.name, payload.phone)

    if user is None:
        raise HTTPException(status_code=401, detail="Неверное имя/телефон или PIN")

    if auth_mode != "admin" and not verify_pin(user, payload.pin):
        raise HTTPException(status_code=401, detail="Неверное имя/телефон или PIN")

    expected_role_by_mode = {
        "manager": "manager",
        "admin": "admin",
        "department_head": "department_head",
        "accountant": "accountant",
    }
    if user.role != expected_role_by_mode[auth_mode]:
        raise HTTPException(status_code=401, detail="Неверное имя/телефон или PIN")

    if not (user.pin_hash or "").startswith("pbkdf2_sha256$"):
        user.pin_hash = native_pin_hash(payload.pin, user.id)
        user.auth_source = "native"
        db.commit()
    token = create_access_token(user)

    return AuthTokenRead(
        access_token=token,
        token_type="bearer",
        user=user_to_auth_read(user),
    )


@router.get("/me", response_model=AuthUserRead)
def me(user: User = Depends(get_current_user)):
    return user_to_auth_read(user)


@router.patch("/change-pin")
def change_pin(
    payload: AuthChangePinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    old_pin = str(payload.old_pin or "").strip()
    new_pin = str(payload.new_pin or "").strip()

    if not old_pin:
        raise HTTPException(status_code=400, detail="Укажи старый PIN")
    consume_login_attempt(db, f"change-pin:{current_user.id}", 12)

    if not verify_pin(current_user, old_pin):
        raise HTTPException(status_code=400, detail="Старый PIN неверный")

    if len(new_pin) < 4:
        raise HTTPException(status_code=400, detail="Новый PIN должен быть минимум 4 цифры")

    if not new_pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN должен содержать только цифры")

    current_user.pin_hash = native_pin_hash(new_pin, current_user.id)
    current_user.auth_source = "native"
    current_user.token_version = (current_user.token_version or 0) + 1
    current_user.updated_at = datetime.utcnow()

    db.add(current_user)
    db.commit()

    return {"ok": True, "message": "PIN изменён", "access_token": create_access_token(current_user)}


def clean_optional_text(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None


@router.patch("/me/profile", response_model=AuthUserRead)
def update_my_profile(
    payload: AuthProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = str(payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Имя не может быть пустым")
    require_unique_user_identity(db, name, payload.phone, exclude_id=current_user.id)

    if payload.department_id is None:
        raise HTTPException(status_code=400, detail="Выбери отдел")

    department = db.get(Department, payload.department_id)
    if department is None or not department.is_active:
        raise HTTPException(status_code=400, detail="Отдел не найден")

    department_name = str(department.name or "").lower()
    if "санжар" not in department_name and "рауф" not in department_name:
        raise HTTPException(status_code=400, detail="Можно выбрать только отдел Санжар или Рауфаль")

    if current_user.role == "department_head" and department.id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Отдел главдепа может изменить только администратор")
    current_user.department_id = department.id

    current_user.name = name
    current_user.phone = normalize_phone(payload.phone) or None
    current_user.email = clean_optional_text(payload.email)
    current_user.updated_at = datetime.utcnow()

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return user_to_auth_read(current_user)

