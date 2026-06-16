Contrast Finance v0.40.55

Изменения:
- Исправлен дубль загрузок при переключении месяца в админке.
- /users теперь не стартует повторный запрос, если первый ещё в процессе.
- /admin-dashboard для одного месяца теперь переиспользует уже запущенный in-flight запрос.
- app.js cache-buster обновлён до v0.40.55.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
