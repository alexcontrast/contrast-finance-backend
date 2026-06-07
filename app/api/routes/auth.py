from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthLoginRequest, AuthTokenRead, AuthUserRead
from app.services.auth import create_access_token, find_login_user, get_current_user, verify_pin


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
