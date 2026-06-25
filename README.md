# Contrast Finance 2.0 — v0.5.5

`v0.5.5` — чистовой патч после диагностики производительности вкладок админки.

Патч убирает временный диагностический шум из браузерной консоли и Railway logs, но оставляет найденные и проверенные ускорения.

## Проверка после деплоя
- Сайт должен загрузиться с `Contrast Finance web app v0.5.5 loaded`.
- В Railway не должно быть `PERF monthly-expenses`, `PERF monthly-plans`, `PERF monthly-closing-calculate`.
- Во вкладке `Закрыть месяц` не должно быть лишнего запроса `/monthly-closings/by-month` при первом открытии.
