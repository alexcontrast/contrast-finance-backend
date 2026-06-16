Contrast Finance 2.0 — v0.40.52

Цель:
- Добавить performance-диагностику первой загрузки админки /admin-dashboard.

Изменения:
- app/api/routes/admin_dashboard.py:
  - добавлены PERF-логи по этапам загрузки admin-dashboard;
  - логируются counts: events/items/requests/shares;
  - логируются timings: base_sql, events_sql, events_calc, departments_calc, payments_sql, payments_rows, closing_sql, response_model, total.
- app/core/config.py:
  - версия обновлена до 0.40.52.
- app/web/index.html:
  - cache-bust app.js/styles.css обновлён до 0.40.52.

После деплоя:
1. Открыть админку.
2. В Railway web-service → Logs найти строку:
   PERF admin-dashboard month=...
3. Прислать эту строку для следующего точечного ускорения.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
