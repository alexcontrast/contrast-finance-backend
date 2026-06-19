from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth import require_roles
from app.services.google_sheets_archive_export import (
    build_export_payload,
    build_year_export_payload,
    payload_updated_sheet_names,
    post_to_apps_script,
)


router = APIRouter(tags=["google_sheets_export"])


@router.post("/google-sheets/export-month")
def export_month_to_google_sheets(
    month: str = Query(..., description="Month in YYYY-MM format"),
    dry_run: bool = Query(False, description="Build payload but do not send it to Google Apps Script"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    payload = build_export_payload(db, month, current_admin)
    if dry_run:
        monthly = payload["sheets"]["monthly"]
        requests = payload["sheets"]["payment_requests"]
        return {
            "ok": True,
            "dry_run": True,
            "export_type": "month",
            "month": payload["month"],
            "events_count": len(monthly["events"]),
            "payment_requests_count": len(requests["rows"]),
            "updated_sheets": payload_updated_sheet_names(payload),
        }
    return post_to_apps_script(payload)


@router.post("/google-sheets/export-year")
def export_year_to_google_sheets(
    year: int | None = Query(None, description="Year in YYYY format; defaults to selected/current year"),
    dry_run: bool = Query(False, description="Build payload but do not send it to Google Apps Script"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    export_year = int(year or datetime.now().year)
    payload = build_year_export_payload(db, export_year, current_admin)
    if dry_run:
        months = payload["sheets"]["months"]
        requests = payload["sheets"]["payment_requests"]
        return {
            "ok": True,
            "dry_run": True,
            "export_type": "year",
            "year": payload["year"],
            "months_count": len(months),
            "events_count": sum(len(month.get("events") or []) for month in months),
            "payment_requests_count": len(requests["rows"]),
            "updated_sheets": payload_updated_sheet_names(payload),
        }
    return post_to_apps_script(payload)
