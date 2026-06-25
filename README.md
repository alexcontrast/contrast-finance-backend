# Contrast Finance 2.0 — v0.5.4

Patch over stable 0.5 / v0.5.3.

This patch reduces extra requests in the admin `Закрыть месяц` tab. It does not change calculations or business logic.

## Deploy

Deploy as usual on Railway. Then hard-refresh the browser.

## Check

Open admin → `Закрыть месяц` and check browser console:

- `PERF web closing/monthly-expenses` should remain around the v0.5.3 value.
- There should be no initial `PERF web closing/by-month` line.
- There should be no `PERF web closing/by-month-refresh` line during background calculation.
- `PERF web closing/refresh-panel total` should be closer to `/monthly-expenses` time.
