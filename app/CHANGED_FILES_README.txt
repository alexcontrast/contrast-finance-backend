Contrast Finance v0.40.10 — changed files only

Изменено:
- app/api/routes/payment_requests.py
- app/api/routes/events.py
- app/telegram_bot/main.py
- app/core/config.py
- app/app/core/config.py
- README.md
- CHANGED_FILES_README.txt

Суть:
- Исправлено обратное распространение статуса денег: заявка -> мероприятие больше не работает.
- Индивидуальная смена money_status заявки на cash_received меняет только эту заявку.
- Массовое направление мероприятие -> все заявки сохранено через /events/{event_id}/cash-received.
- Массовая операция теперь дополнительно помечает Telegram-карточки всех затронутых заявок для синхронизации.
- Telegram admin action cashin больше не ставит event.money_status=cash_received, а меняет только выбранную заявку.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py


## v0.40.12
- Added one-time legacy migration importer for Apps Script / Google Sheets export JSON.
- Added legacy identifiers for idempotent event/item/payment imports.
- Added /legacy-migration upload page protected by LEGACY_MIGRATION_TOKEN.


v0.40.12: Legacy migration dry-run now uses fast JSON validation without touching PostgreSQL; migration page handles non-JSON upstream errors clearly.
