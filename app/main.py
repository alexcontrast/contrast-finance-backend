from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Contrast Finance API",
    version=settings.VERSION,
)

app.include_router(health_router)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": settings.SERVICE_NAME,
        "message": "Contrast Finance API is running",
    }
