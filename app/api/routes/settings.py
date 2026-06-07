from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.settings import EconomicsSettingsRead


router = APIRouter(tags=["settings"])


@router.get("/settings/economics", response_model=EconomicsSettingsRead)
def get_economics_settings():
    settings = get_settings()
    return EconomicsSettingsRead(
        vat_rate=settings.VAT_RATE,
        contractor_deduction_rate=settings.CONTRACTOR_DEDUCTION_RATE,
        contrast_internal_tax_rate=settings.CONTRAST_INTERNAL_TAX_RATE,
        simplified_tax_rate=settings.SIMPLIFIED_TAX_RATE,
    )
