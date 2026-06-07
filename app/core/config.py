import os
from functools import lru_cache


class Settings:
    SERVICE_NAME: str = "contrast-finance-api"
    VERSION: str = "0.18.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # Keep secrets on Railway Variables, never in GitHub.
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-change-me")

    # KGD integration.
    # stub = safe fake mode for development
    # live = real KGD calls, when KGD endpoint details are connected
    KGD_MODE: str = os.getenv("KGD_MODE", "stub")
    KGD_API_KEY: str | None = os.getenv("KGD_API_KEY")
    KGD_BASE_URL: str | None = os.getenv("KGD_BASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
