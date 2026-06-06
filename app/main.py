from fastapi import FastAPI

from app.api.routes.departments import router as departments_router
from app.api.routes.events import router as events_router
from app.api.routes.event_items import router as event_items_router
from app.api.routes.health import router as health_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Contrast Finance API",
    version=settings.VERSION,
)

app.include_router(health_router)
app.include_router(departments_router)
app.include_router(users_router)
app.include_router(events_router)
app.include_router(event_items_router)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": settings.SERVICE_NAME,
        "message": "Contrast Finance API is running",
    }
