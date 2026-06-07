from pydantic import BaseModel


class AuthLoginRequest(BaseModel):
    # Same as old site: manager enters name + PIN.
    name: str | None = None

    # Optional future login by phone.
    phone: str | None = None

    pin: str


class AuthUserRead(BaseModel):
    id: int
    name: str
    phone: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    role: str
    is_active: bool
    legacy_user_id: str | None = None
    auth_source: str


class AuthTokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserRead
