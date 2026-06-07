import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User


security = HTTPBearer(auto_error=False)


def legacy_apps_script_pin_hash(pin: str, legacy_user_id: str) -> str:
    """
    Apps Script logic:
    hashPin_(pin, salt):
      raw = `${salt}:${pin}`
      SHA-256 hex
    where salt = User ID.
    """
    raw = f"{legacy_user_id}:{pin}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def native_pin_hash(pin: str, user_id: int) -> str:
    raw = f"native:{user_id}:{pin}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_pin(user: User, pin: str) -> bool:
    pin = str(pin or "").strip()

    if user.legacy_user_id and user.legacy_pin_hash:
        return legacy_apps_script_pin_hash(pin, user.legacy_user_id) == user.legacy_pin_hash

    if user.pin_hash:
        return native_pin_hash(pin, user.id) == user.pin_hash

    return False


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "role": user.role,
        "department_id": user.department_id,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    user_id = int(payload.get("user_id") or payload.get("sub") or 0)

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user

    return checker


def normalize_phone(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def find_login_user(db: Session, name: str | None, phone: str | None) -> User | None:
    name_clean = str(name or "").strip()
    phone_digits = normalize_phone(phone)

    query = select(User).where(User.is_active == True)  # noqa: E712

    if name_clean and phone_digits:
        query = query.where(
            or_(
                User.name.ilike(name_clean),
                User.phone == phone_digits,
                User.phone == phone,
            )
        )
    elif name_clean:
        query = query.where(User.name.ilike(name_clean))
    elif phone_digits:
        query = query.where(or_(User.phone == phone_digits, User.phone == phone))
    else:
        return None

    return db.execute(query).scalars().first()
