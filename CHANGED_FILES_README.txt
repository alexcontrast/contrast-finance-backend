Contrast Finance 2.0 — v0.40.54

Изменённые файлы:
- app/web/app.js
- app/web/index.html

Что изменено:
- Добавлен frontend cache для /users?include_inactive=true на 10 минут.
- При повторной загрузке админки users берутся из памяти/localStorage, без лишнего запроса 1+ сек.
- Убрана бесполезная карточка "Кабинет открыт" при первичной загрузке dashboard.
- app.js cache-buster обновлён до v0.40.54.

Проверки:
- node --check app/web/app.js
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
