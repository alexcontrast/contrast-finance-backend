v0.5.1 — Google Sheets archive export, stage 1

Changed/added files:
- app/core/config.py
- app/main.py
- app/api/routes/google_sheets_export.py
- app/services/google_sheets_archive_export.py
- app/web/app.js
- app/web/styles.css
- tools/google_sheets_export_webapp.gs

What this version adds:
- Admin tab “Google архив”.
- Manual export button for selected month.
- Dry-run button that checks data count without sending to Google.
- Backend endpoint POST /google-sheets/export-month.
- Export payload for monthly sheet + clean “Заявки на оплату” sheet.
- Apps Script web app receiver template for Google Sheets formatting.
- No technical sheets are exported.

Required Railway secrets before real export:
- GOOGLE_SHEETS_EXPORT_WEBHOOK_URL
- optional GOOGLE_SHEETS_EXPORT_TOKEN
- optional GOOGLE_SHEETS_ARCHIVE_URL
