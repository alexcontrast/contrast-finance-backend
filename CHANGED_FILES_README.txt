Contrast Finance v0.40.56

Изменения:
- Кабинет менеджера: добавлена защита от дублей параллельных запросов manager-dashboard и payment-requests.
- Кабинет менеджера: добавлены frontend PERF-логи render-manager-dashboard и in-flight reuse.
- Backend /manager-dashboard: добавлены PERF-логи в Railway Logs.
- Backend /manager-dashboard: список пользователей для соавторства теперь грузит только нужных пользователей, а не всех активных.
- app.js cache-buster обновлён до v0.40.56.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
