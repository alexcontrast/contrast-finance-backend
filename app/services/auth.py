import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.models.auth_attempt import AuthAttempt


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
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(pin).encode(), salt.encode(), 600_000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verify_native_pin(pin: str, user: User) -> bool:
    stored = user.pin_hash or ""
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt, expected = stored.split("$")
            if not 100_000 <= int(rounds) <= 1_000_000:
                return False
            actual = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), int(rounds)).hex()
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False
    legacy = hashlib.sha256(f"native:{user.id}:{pin}".encode()).hexdigest()
    return hmac.compare_digest(legacy, stored)


def verify_pin(user: User, pin: str) -> bool:
    pin = str(pin or "").strip()

    # Native PIN takes priority after user changes PIN in the new system.
    if user.auth_source == "native" and user.pin_hash:
        return verify_native_pin(pin, user)

    if user.legacy_user_id and user.legacy_pin_hash:
        return hmac.compare_digest(legacy_apps_script_pin_hash(pin, user.legacy_user_id), user.legacy_pin_hash)

    if user.pin_hash:
        return verify_native_pin(pin, user)

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
        "ver": user.token_version or 0,
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
    if int(payload.get("ver", 0)) != (user.token_version or 0):
        raise HTTPException(status_code=401, detail="PIN изменён. Войдите снова")

    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user

    return checker


def normalize_phone(value: str | None) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def require_unique_user_identity(db: Session, name: str, phone: str | None, exclude_id: int | None = None):
    from app.services.mutation_locks import lock_business_keys
    key_name, key_phone = name.strip().casefold(), normalize_phone(phone)
    lock_business_keys(db, "user-identity", key_name, key_phone)
    users = db.execute(select(User).where(User.is_active.is_(True))).scalars().all()
    if any(u.id != exclude_id and (u.name.strip().casefold() == key_name or (key_phone and normalize_phone(u.phone) == key_phone)) for u in users):
        raise HTTPException(status_code=409, detail="Активный пользователь с таким именем или телефоном уже есть")


def consume_login_attempt(db: Session, scope: str, limit: int) -> None:
    """Atomic shared limit: survives restarts and multiple API workers."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    now = datetime.utcnow()
    key = hashlib.sha256(scope.encode()).hexdigest()
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    expired = AuthAttempt.window_started_at < now - timedelta(minutes=15)
    stmt = insert(AuthAttempt).values(key=key, attempts=1, window_started_at=now)
    stmt = stmt.on_conflict_do_update(index_elements=[AuthAttempt.key], set_={
        "attempts": case((expired, 1), else_=AuthAttempt.attempts + 1),
        "window_started_at": case((expired, now), else_=AuthAttempt.window_started_at),
    }).returning(AuthAttempt.attempts)
    attempts = db.execute(stmt).scalar_one()
    db.commit()
    if attempts > limit:
        raise HTTPException(status_code=429, detail="Слишком много попыток входа. Повторите через 15 минут", headers={"Retry-After": "900"})


def find_login_user(db: Session, name: str | None, phone: str | None) -> User | None:
    name_clean = str(name or "").strip()
    phone_digits = normalize_phone(phone)

    if not name_clean and not phone_digits:
        return None

    # Names and historical phone formatting must be compared identically at
    # login and user creation. Python casefold also handles Cyrillic on SQLite.
    candidates = [u for u in db.execute(select(User).where(User.is_active == True)).scalars()
                  if (name_clean and u.name.strip().casefold() == name_clean.casefold())
                  or (phone_digits and normalize_phone(u.phone) == phone_digits)]
    # An ambiguous login must never silently select the first account.
    return candidates[0] if len(candidates) == 1 else None
