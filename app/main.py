from fastapi import FastAPI

from app.api.routes.departments import router as departments_router
from app.api.routes.events import router as events_router
from app.api.routes.event_summary import router as event_summary_router
from app.api.routes.coordinator import router as coordinator_router
from app.api.routes.monthly import router as monthly_router
from app.api.routes.monthly_expenses import router as monthly_expenses_router
from app.api.routes.monthly_closings import router as monthly_closings_router
from app.api.routes.department_head_dashboard import router as department_head_dashboard_router
from app.api.routes.admin_dashboard import router as admin_dashboard_router
from app.api.routes.event_items import router as event_items_router
from app.api.routes.payment_requests import router as payment_requests_router
from app.api.routes.tax import router as tax_router
from app.api.routes.kgd import router as kgd_router
from app.api.routes.settings import router as settings_router
from app.api.routes.auth import router as auth_router
from app.api.routes.security import router as security_router
from app.api.routes.app_bootstrap import router as app_bootstrap_router
from app.api.routes.manager_dashboard import router as manager_dashboard_router
from app.api.routes.web import router as web_router
from app.api.routes.users_import import router as users_import_router
from app.api.routes.users_manage import router as users_manage_router
from app.api.routes.health import router as health_router
from app.api.routes.legacy_migration import router as legacy_migration_router
from app.api.routes.google_sheets_export import router as google_sheets_export_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Contrast Finance API",
    version=settings.VERSION,
)

app.include_router(health_router)
app.include_router(legacy_migration_router)
app.include_router(google_sheets_export_router)
app.include_router(departments_router)
app.include_router(events_router)
app.include_router(event_summary_router)
app.include_router(coordinator_router)
app.include_router(monthly_router)
app.include_router(monthly_expenses_router)
app.include_router(monthly_closings_router)
app.include_router(department_head_dashboard_router)
app.include_router(admin_dashboard_router)
app.include_router(event_items_router)
app.include_router(payment_requests_router)
app.include_router(tax_router)
app.include_router(kgd_router)
app.include_router(settings_router)
app.include_router(auth_router)
app.include_router(security_router)
app.include_router(app_bootstrap_router)
app.include_router(manager_dashboard_router)
app.include_router(users_import_router)
app.include_router(users_manage_router)


@app.get("/api/status")
def root():
    return {
        "ok": True,
        "service": settings.SERVICE_NAME,
        "message": "Contrast Finance API is running",
        "version": get_settings().VERSION,
    }

app.include_router(web_router)
