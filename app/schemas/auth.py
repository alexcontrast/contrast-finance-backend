from pydantic import BaseModel, ConfigDict


class AuthLoginRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    pin: str
    auth_mode: str | None = None


class AuthUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    role: str
    is_active: bool
    legacy_user_id: str | None = None
    auth_source: str | None = None


class AuthTokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserRead
