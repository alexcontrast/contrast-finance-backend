from pydantic import BaseModel, ConfigDict


class AuthLoginRequest(BaseModel):
    # Manager / department head: name + PIN.
    # Admin: auth_mode=admin and PIN only.
    name: str | None = None
    phone: str | None = None
    pin: str
    auth_mode: str | None = None


class AuthChangePinRequest(BaseModel):
    old_pin: str
    new_pin: str


class AuthProfileUpdateRequest(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    department_id: int | None = None


class AuthPermissionsRead(BaseModel):
    can_view_admin: bool = False
    can_manage_users: bool = False
    can_manage_settings: bool = False
    can_manage_monthly_plans: bool = False
    can_manage_monthly_expenses: bool = False
    can_view_department_dashboard: bool = False
    can_create_events: bool = False
    can_edit_events: bool = False
    can_create_payment_requests: bool = False
    can_manage_payment_requests: bool = False


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
    permissions: AuthPermissionsRead | None = None


class AuthTokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserRead
