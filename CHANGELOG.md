# v0.5.9 — Legacy dry-run page hard feedback fix

Base: v0.5.8.

## Fixed
- Reworked `/legacy-events-2026` dry-run page so the UI always shows whether the XLSX file is selected.
- Added explicit status messages before upload, during backend request, and on every error path.
- Made dry-run buttons `type="button"` and bound handlers directly to `#dryBtn` / `#fileInput`.
- Replaced `res.json()` with `res.text()` + guarded JSON parsing, so backend HTML/proxy/token errors are visible instead of silently failing.
- Added visible file name and size after file selection.

## Unchanged
- No database writes.
- No real import yet.
- No payment requests / Telegram / active queue import.
- Main web app, backend business logic, Telegram bot, admin/manager/head dashboards are unchanged.

## Local validation
- `python3 -m py_compile app/api/routes/legacy_events_2026.py`
- Local dry-run parser check on `Отчет по мероприятиям (1).xlsx`: 74 events found for Jan-Apr 2026.
