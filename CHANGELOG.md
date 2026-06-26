# v0.5.16 — Admin closing head percent override

- Added manual monthly override for department-head salary percent in Admin → “Закрыть месяц”.
- Added pencil controls next to departments in the closing calculation.
- Added protected endpoint `PATCH /monthly-closings/head-percent`.
- Added persistent monthly override columns for `Санжар` and `Рауфаль` department-head salary percent.
- Closing calculation now uses manual override when set, otherwise keeps automatic 10% / 15% logic.
- If a month is already closed, changing the override recalculates and updates the saved closing snapshot.
- Added Alembic migration `0010_monthly_closing_head_percent_overrides`.
- Updated cache-bust to `0.5.16`.

No changes to Telegram bot, legacy import, payment requests, Google Sheets export, or manager calculations.
