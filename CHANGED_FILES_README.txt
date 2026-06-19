Contrast Finance v0.5.2

Base: v0.5.1.

Changed:
- app/services/google_sheets_archive_export.py
  - Google archive export now excludes deleted/cancelled events from monthly sheets and request archive.
  - Monthly summary now includes company income for old-style mini-summary.
  - schema_version bumped to contrast_google_archive_v0.5.2.
- app/web/app.js
  - Google archive tab text and version log updated to v0.5.2.
- tools/google_sheets_export_webapp.gs
  - Monthly sheet redesigned to match old bookkeeping visual format more closely:
    summary block A:B, yellow event headers, colored Cost/Expense/VAT/Deductions/Commission/Paid columns, totals/status row.
  - Payment requests sheet made more compact and readable with frozen header, filter, status colors and cleaner widths.
  - Technical sheets are removed from archive export (registry, positions, drafts, users, goals, dictionaries, old raw request sheet, default Sheet1).

Checks:
python3 -m compileall -q app
python3 -m py_compile app/telegram_bot/main.py
node --check app/web/app.js
node --check /tmp/google_sheets_export_webapp.js
