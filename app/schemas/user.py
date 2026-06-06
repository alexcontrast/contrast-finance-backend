from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str
    role: str = Field(default="manager", description="manager / admin / department_head")
    department_id: int | None = None
    phone: str | None = None
    email: str | None = None
    telegram_id: str | None = None
    telegram_username: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int | None
    name: str
    phone: str | None
    email: str | None
    telegram_id: str | None
    telegram_username: str | None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
