import os
from decimal import Decimal
from functools import lru_cache


class Settings:
    SERVICE_NAME: str = "contrast-finance-api"
    VERSION: str = "0.35.90"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))

    KGD_MODE: str = os.getenv("KGD_MODE", "live")
    KGD_API_KEY: str | None = os.getenv("KGD_API_KEY")
    KGD_BASE_URL: str = os.getenv("KGD_BASE_URL", "https://portal.kgd.gov.kz")

    VAT_RATE: Decimal = Decimal(os.getenv("VAT_RATE", "0.16"))
    CONTRACTOR_DEDUCTION_RATE: Decimal = Decimal(os.getenv("CONTRACTOR_DEDUCTION_RATE", "0.10"))
    CONTRAST_INTERNAL_TAX_RATE: Decimal = Decimal(os.getenv("CONTRAST_INTERNAL_TAX_RATE", "0.12"))
    SIMPLIFIED_TAX_RATE: Decimal = Decimal(os.getenv("SIMPLIFIED_TAX_RATE", "0.05"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
