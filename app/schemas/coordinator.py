from decimal import Decimal

from pydantic import BaseModel, Field


class CoordinatorCreate(BaseModel):
    external_name: str = Field(default="Координатор")
    external_amount: Decimal
    external_note: str | None = None
    sort_order: int = 999
