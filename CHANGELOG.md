# v0.5.20 — Admin Statistics tab

Base: v0.5.19.

## Changes
- Renamed admin tab `Google архив` to `Статистика`.
- Moved `Статистика` tab to the right side of the admin tabs row.
- Kept archive actions at the top: `Выгрузить месяц` and `Выгрузить год`.
- Removed visible dry-run/check buttons from this tab.
- Added annual statistics view inside admin UI:
  - company yearly KPI cards;
  - monthly company dynamics table;
  - department income/plan table;
  - manager income/salary/plan table.
- Added admin endpoint `GET /google-sheets/year-statistics?year=YYYY`, reusing the same annual statistics builder as the Google sheet `Годовая статистика`.
- Updated cache-bust to `0.5.20`.

## Not changed
- Google Sheets export logic.
- Telegram bot.
- Payment requests.
- Manager and department head cabinets.
- Monthly closing calculations and head percent override logic.
- Database schema / Alembic migrations.
