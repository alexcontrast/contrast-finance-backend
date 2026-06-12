Contrast Finance v0.40.1 — Telegram bot bridge for new site

Base: stable v0.40 / codebase v0.38.10.

Changed files:
- app/telegram_bot/__init__.py
- app/telegram_bot/main.py
- app/core/config.py
- requirements.txt
- Procfile
- .env.example
- README.md
- CHANGED_FILES_README.txt

What changed:
- Added a separate Telegram bot worker for the new PostgreSQL site.
- The old Apps Script mechanics were ported conceptually, but the bot now works directly with the new DB models.
- Test bot is supported through TELEGRAM_BOT_TOKEN.
- Tatiana notifications are built in for invoice and self-employed requests, but disabled by default via TELEGRAM_TATYANA_ENABLED=false.
- Payment status and money status are kept separate:
  - payment request status: new / paid / rejected / tax_check_needed
  - money status: waiting_money / cash_received / cancelled
- Admin buttons:
  - new/to_pay/tax_check_needed -> Оплачено / Отклонить
  - paid -> Деньги в кассе
- Admin/manager cards are deleted only for rejected or cash_received requests.
- Tatiana cards, when enabled, are updated but not deleted.
- Added Procfile worker: bot: python -m app.telegram_bot.main

No migrations.
