Contrast Finance Backend v0.40.5 — changed files only

Reason:
Telegram bot did not always remove admin/manager cards when an admin cancelled/rejected a request that already had money_status=cash_received. The terminal-state check was too narrow for mixed states like cancelled/rejected + cash_received.

Changed:
- app/telegram_bot/main.py
  * BOT_VERSION = CONTRAST_FINANCE_BOT_V0.40.5_NEW_SITE.
  * Telegram terminal-state logic now treats payment status rejected/cancelled as final regardless of money_status.
  * paid + cash_received still removes cards.
  * new/to_pay + cash_received still does NOT remove cards, because payment and money statuses are separate.
  * Added a proper display label for status=cancelled.
- app/core/config.py and app/app/core/config.py: VERSION = 0.40.5.
- README/CHANGED updated.

No DB migrations.
Railway commands are unchanged:
web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
bot: python -m app.telegram_bot.main
