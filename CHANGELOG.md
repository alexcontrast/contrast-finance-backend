# CHANGELOG

## v0.5.3 — Admin expenses performance and warning fix

- Исправлено предупреждение Pydantic `Expected date but got str`: в быстрых payload-заявках `manager_name` ошибочно передавался четвёртым позиционным аргументом и попадал в `event_date`. Теперь передаются и `event_date`, и `manager_name` в правильные поля.
- Ускорен `GET /monthly-expenses`: вместо `extract(year/month)` используется прямой фильтр `MonthlyExpense.month == month_date`; план месяца загружается один раз, а не по одному SQL-запросу на каждый расход.
- Диагностические `PERF`-логи сохранены; лог `monthly-expenses` теперь отдельно показывает `query`, `plan`, `response`, `total`.
- Cache-bust обновлён до `0.5.3`.
- Backend-логика расчётов, Telegram-бот, Google Sheets экспорт и интерфейсные раскладки не менялись.
