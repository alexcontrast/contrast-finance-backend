from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine


router = APIRouter()


@router.get("/health")
def health_check():
    settings = get_settings()
    return {
        "ok": True,
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_configured": engine is not None,
    }


@router.get("/db/health")
def database_health_check():
    if engine is None:
        return {
            "ok": False,
            "database_connected": False,
            "error": "DATABASE_URL is not configured",
        }

    try:
        with engine.connect() as connection:
            result = connection.execute(text("select 1 as value"))
            value = result.scalar_one()

        return {
            "ok": value == 1,
            "database_connected": True,
        }
    except Exception as exc:
        return {
            "ok": False,
            "database_connected": False,
            "error": str(exc),
        }


@router.get("/db/tables")
def database_tables_check():
    if engine is None:
        return {
            "ok": False,
            "tables": [],
            "error": "DATABASE_URL is not configured",
        }

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    select table_name
                    from information_schema.tables
                    where table_schema = 'public'
                    order by table_name
                    """
                )
            )
            tables = [row[0] for row in result.fetchall()]

        return {
            "ok": True,
            "tables": tables,
        }
    except Exception as exc:
        return {
            "ok": False,
            "tables": [],
            "error": str(exc),
        }
