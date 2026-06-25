# CHANGELOG

## v0.5.4 — Admin closing tab request reduction

Base: stable `0.5` + `v0.5.3` diagnostics/performance fix.

Scope: admin web UI only, tab `Закрыть месяц`.

Changes:
- Removed the redundant `/monthly-closings/by-month` request when opening the `Закрыть месяц` tab.
- The closing status is now taken from the already loaded `admin-dashboard-bundle` cache.
- Removed the second `/monthly-closings/by-month` refresh request that ran together with background calculation.
- The `Пересчитать` button now checks the cached closing status instead of doing an extra `/monthly-closings/by-month` request before recalculation.
- Updated web cache-bust to `0.5.4`.

Expected result:
- Initial `Закрыть месяц` tab load should be limited mainly by `/monthly-expenses` instead of waiting for `/monthly-expenses` + `/monthly-closings/by-month`.
- After v0.5.3 `/monthly-expenses` was around 0.9s, so the first visible panel should open close to that range.
- Background calculation remains separate and still depends on `/monthly-closings/calculate`.

Not changed:
- Backend calculations.
- Expenses logic.
- Month closing/reopening logic.
- Telegram bot.
- Manager/admin/department-head layout.
- Google Sheets export.
