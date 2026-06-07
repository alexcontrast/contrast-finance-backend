from pydantic import BaseModel


class LegacyUserImportRow(BaseModel):
    legacy_user_id: str
    name: str
    department_id: int | None = None
    department_name: str | None = None
    phone: str | None = None
    role: str = "manager"
    is_active: bool = True
    legacy_pin_hash: str


class LegacyUsersImportRequest(BaseModel):
    users: list[LegacyUserImportRow]


class LegacyUsersImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
