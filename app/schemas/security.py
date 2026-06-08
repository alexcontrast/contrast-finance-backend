from pydantic import BaseModel


class SecurityCheckRead(BaseModel):
    ok: bool
    user_id: int
    role: str
    department_id: int | None = None
