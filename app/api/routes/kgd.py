from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.kgd import KgdStatusRead


router = APIRouter(tags=["kgd"])


@router.get("/kgd/status", response_model=KgdStatusRead)
def get_kgd_status():
    settings = get_settings()
    return KgdStatusRead(
        mode=settings.KGD_MODE,
        api_key_configured=bool(settings.KGD_API_KEY),
        base_url_configured=bool(settings.KGD_BASE_URL),
    )
