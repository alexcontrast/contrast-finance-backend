v0.40.66 — FIX_LEGACY_INVOICE_BIN_PAYMENT_MODAL

Исправлено:
- В модалке менеджера «Оплатить» для позиции По счету больше не появляется ложный блокер «Сначала проверь БИН», если БИН уже закреплен за позицией или есть активная invoice-заявка с BIN/tax snapshot.
- Для старых импортированных позиций/заявок фронт восстанавливает invoice-контекст из самой позиции или последней активной invoice-заявки.
- Backend также восстанавливает контекст перед созданием заявки, чтобы обойти UI было безопасно и одинаково.
- Для старых закрепленных BIN без tax_check_status ставится технический статус legacy_checked / «Проверен ранее», без повторной проверки КГД.
- Telegram-бот получил такую же защиту для invoice-заявок.
- Обновлен cache-buster web app до v0.40.66.

Измененные файлы:
- app/web/app.js
- app/web/index.html
- app/api/routes/payment_requests.py
- app/telegram_bot/main.py
- app/core/config.py
- app/app/core/config.py

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
