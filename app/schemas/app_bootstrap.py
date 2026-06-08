from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.auth import AuthPermissionsRead, AuthUserRead


class DepartmentOptionRead(BaseModel):
    id: int
    name: str
    is_active: bool


class EconomicsSettingsBootstrapRead(BaseModel):
    vat_rate: Decimal
    contractor_deduction_rate: Decimal
    contrast_internal_tax_rate: Decimal
    simplified_tax_rate: Decimal


class AppBootstrapRead(BaseModel):
    user: AuthUserRead
    permissions: AuthPermissionsRead
    departments: list[DepartmentOptionRead]
    active_month: date
    economics: EconomicsSettingsBootstrapRead
    default_screen: str
