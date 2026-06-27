from datetime import date, datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth import require_roles
from app.services.google_sheets_archive_export import (
    build_annual_stats_sheet,
    build_export_payload,
    build_month_export_sections,
    build_year_export_payload,
    build_year_export_payloads,
    build_year_statistics_sections,
    payload_updated_sheet_names,
    post_payload_sequence,
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
        archive_requests = payload["sheets"].get("payment_requests_archive") or {"rows": []}
        return {
            "ok": True,
            "dry_run": True,
            "export_type": "month",
            "month": payload["month"],
            "events_count": len(monthly["events"]),
            "active_payment_requests_count": len(requests["rows"]),
            "archive_payment_requests_count": len(archive_requests["rows"]),
            "payment_requests_count": len(requests["rows"]) + len(archive_requests["rows"]),
            "updated_sheets": payload_updated_sheet_names(payload),
        }
    return post_to_apps_script(payload)


@router.get("/google-sheets/year-statistics")
def get_google_sheets_year_statistics(
    year: int | None = Query(None, description="Year in YYYY format; defaults to selected/current year"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    export_year = int(year or datetime.now().year)
    month_sections, _statistics_meta = build_year_statistics_sections(db, export_year)
    annual_stats = build_annual_stats_sheet(export_year, month_sections)
    return {
        "ok": True,
        "year": export_year,
        "statistics": annual_stats,
    }


@router.post("/google-sheets/export-year")
def export_year_to_google_sheets(
    year: int | None = Query(None, description="Year in YYYY format; defaults to selected/current year"),
    dry_run: bool = Query(False, description="Build payload but do not send it to Google Apps Script"),
    phased: bool = Query(True, description="Post yearly export to Apps Script in separate safe steps"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    export_year = int(year or datetime.now().year)
    if phased:
        payloads = build_year_export_payloads(db, export_year, current_admin)
        if dry_run:
            updated: list[str] = []
            events_count = 0
            active_payment_requests_count = 0
            archive_payment_requests_count = 0
            for payload in payloads:
                sheets = payload.get("sheets") or {}
                if sheets.get("monthly"):
                    events_count += len((sheets["monthly"] or {}).get("events") or [])
                if sheets.get("payment_requests"):
                    active_payment_requests_count += len((sheets["payment_requests"] or {}).get("rows") or [])
                if sheets.get("payment_requests_archive"):
                    archive_payment_requests_count += len((sheets["payment_requests_archive"] or {}).get("rows") or [])
                for sheet_name in payload_updated_sheet_names(payload):
                    if sheet_name not in updated:
                        updated.append(sheet_name)
            return {
                "ok": True,
                "dry_run": True,
                "export_type": "year",
                "phased": True,
                "steps_count": len(payloads),
                "year": export_year,
                "months_count": 12,
                "events_count": events_count,
                "active_payment_requests_count": active_payment_requests_count,
                "archive_payment_requests_count": archive_payment_requests_count,
                "payment_requests_count": active_payment_requests_count + archive_payment_requests_count,
                "updated_sheets": updated,
            }
        return post_payload_sequence(payloads)

    payload = build_year_export_payload(db, export_year, current_admin)
    if dry_run:
        months = payload["sheets"]["months"]
        requests = payload["sheets"]["payment_requests"]
        archive_requests = payload["sheets"].get("payment_requests_archive") or {"rows": []}
        return {
            "ok": True,
            "dry_run": True,
            "export_type": "year",
            "phased": False,
            "year": payload["year"],
            "months_count": len(months),
            "events_count": sum(len(month.get("events") or []) for month in months),
            "active_payment_requests_count": len(requests["rows"]),
            "archive_payment_requests_count": len(archive_requests["rows"]),
            "payment_requests_count": len(requests["rows"]) + len(archive_requests["rows"]),
            "updated_sheets": payload_updated_sheet_names(payload),
        }
    return post_to_apps_script(payload)
