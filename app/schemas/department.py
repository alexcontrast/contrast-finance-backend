from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DepartmentCreate(BaseModel):
    name: str


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
