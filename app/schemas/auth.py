from pydantic import BaseModel


class AuthLoginRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    pin: str


class AuthBootstrapAdminRequest(BaseModel):
    name: str
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


class AuthPermissionsRead(BaseModel):
    role: str
    department_id: int | None = None
    can_view_admin_dashboard: bool
    can_manage_users: bool
    can_view_department_dashboard: bool
    can_edit: bool



class AuthChangePinRequest(BaseModel):
    old_pin: str
    new_pin: str


class AuthChangePinRead(BaseModel):
    ok: bool
    message: str
