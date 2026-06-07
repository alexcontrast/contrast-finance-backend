from datetime import datetime

from pydantic import BaseModel


class NativeUserCreate(BaseModel):
    name: str
    phone: str | None = None
    department_id: int | None = None
    role: str = "manager"
    pin: str
    is_active: bool = True


class UserRoleUpdate(BaseModel):
    role: str
    department_id: int | None = None
    is_active: bool | None = None


class UserPinUpdate(BaseModel):
    pin: str


class UserRead(BaseModel):
    id: int
    name: str
    phone: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    role: str
    is_active: bool
    legacy_user_id: str | None = None
    auth_source: str
    created_at: datetime
    updated_at: datetime
