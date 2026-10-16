from datetime import datetime

from pydantic import BaseModel, Field


class NativeUserCreate(BaseModel):
    name: str = Field(max_length=150)
    phone: str | None = Field(default=None, max_length=64)
    department_id: int | None = None
    role: str = "manager"
    pin: str = Field(min_length=4, max_length=12)
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
