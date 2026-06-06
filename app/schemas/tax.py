from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TaxCheckRequest(BaseModel):
    iin_bin: str = Field(description="BIN / ИИН подрядчика")


class ManualTaxRequest(BaseModel):
    # our_vat / our_no_vat / simplified / self_employed / not_found
    tax_status: str = Field(description="our_vat / our_no_vat / simplified / self_employed / not_found")


class TaxResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    iin_bin: str
    iin_bin_locked: bool
    tax_check_status: str | None
    vat_amount: Decimal
    deduction_amount: Decimal
    source: str
    message: str
