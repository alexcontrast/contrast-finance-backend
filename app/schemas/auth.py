from pydantic import BaseModel, ConfigDict, Field


class AuthLoginRequest(BaseModel):
    # Manager / department head: name + PIN.
    # Admin: auth_mode=admin and PIN only.
    name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=64)
    pin: str = Field(min_length=4, max_length=32)
    auth_mode: str | None = None


class AuthChangePinRequest(BaseModel):
    old_pin: str = Field(max_length=32)
    new_pin: str = Field(min_length=4, max_length=32)


class AuthProfileUpdateRequest(BaseModel):
    name: str = Field(max_length=150)
    phone: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=255)
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
    email: str | None = None
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
