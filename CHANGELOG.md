# v0.5.18 — Legacy import cleanup, keep head percent override

Base: v0.5.17.

## What changed
- Removed temporary legacy import web routes/pages after the January–April 2026 import was completed.
- Removed legacy import services/scripts used only for one-time data transfer.
- Removed `openpyxl` dependency because XLSX import page is no longer needed.
- Kept the admin closing-month feature for manual department-head salary percent override.
- Kept Alembic migration `0010_head_pct_overrides` because it is required for the new monthly override fields.
- Updated web cache-bust to `0.5.18`.

## Not changed
- Existing imported events remain in the database.
- Manager/admin/department-head dashboards are not functionally changed except the head percent override feature already introduced in v0.5.16/v0.5.17.
- Telegram bot, Google Sheets export, payment requests and calculations were not changed.
