Contrast Finance v0.40.72

Изменения:
- Добавлен backend endpoint POST /events/{event_id}/items/tax/check: новая позиция + live КГД одним запросом.
- Проверка КГД в смете для новой строки больше не делает два round-trip: создание позиции и проверка объединены.
- Проверка КГД в модалке оплаты для новой invoice-позиции также объединена в один запрос.
- Кэш КГД не добавлен: каждая проверка остается live.
- После успешной live-КГД проверки позиция на фронте помечается как backend-synced, чтобы создание invoice-заявки не делало лишний PATCH.
- Версия web app обновлена до v0.40.72.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
