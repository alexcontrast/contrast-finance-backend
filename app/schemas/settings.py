from decimal import Decimal

from pydantic import BaseModel


class EconomicsSettingsRead(BaseModel):
    vat_rate: Decimal
    contractor_deduction_rate: Decimal
    contrast_internal_tax_rate: Decimal
    simplified_tax_rate: Decimal
