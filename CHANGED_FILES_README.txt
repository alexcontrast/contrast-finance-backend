v0.40.63

Изменения:
- Добавлен /admin-dashboard-bundle: админка получает dashboard + полные payload'ы мероприятий одним запросом.
- Добавлен /department-head-dashboard-bundle: главдепы получают dashboard + полные payload'ы мероприятий одним запросом.
- В админке и кабинете главдепа модалка мероприятия теперь открывается из локального кэша, если данные уже приехали в bundle.
- Добавлены PERF-логи для admin-dashboard-bundle и department-head-dashboard-bundle.
- Версия web app обновлена до v0.40.63.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
