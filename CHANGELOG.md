# v0.5.29 — Admin statistics perf log output fix

## Исправлено
- PERF-лог загрузки годовой статистики теперь гарантированно попадает в Railway logs:
  - через `contrast.performance` logger;
  - через `uvicorn.error` logger;
  - через `print(..., flush=True)`.
- Добавлен браузерный замер в консоль: `PERF web admin-year-statistics year=... retried=... total=...s`.
- Cache-bust обновлён до `0.5.29`.

## Не менялось
- Расчёты статистики.
- БД/Alembic.
- Telegram-бот.
- Заявки.
- Google Sheets export.
- Менеджерский кабинет и закрытие месяца.
