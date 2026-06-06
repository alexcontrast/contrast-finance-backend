import os
from functools import lru_cache


class Settings:
    SERVICE_NAME: str = "contrast-finance-api"
    VERSION: str = "0.13.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # Keep secrets on Railway Variables, never in GitHub.
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-change-me")


@lru_cache
def get_settings() -> Settings:
    return Settings()
