Contrast Finance Backend v0.40.3 — changed files only

Reason:
Telegram bot v0.40.1 created a request and then immediately removed its Telegram cards when the event/request money_status was already cash_received. It also did not fully mirror the site logic for fixed payment methods on estimate positions.

Changed:
- app/telegram_bot/main.py
  * Separates terminal Telegram card logic from money_status alone.
  * A card is terminal only when request.status is rejected/cancelled or when request.status=paid AND money_status=cash_received.
  * Manager active request list uses the same terminal rule.
  * Item list now includes fixedPaymentMethod/paymentMethodLocked metadata.
  * Telegram payment method keyboard shows only the fixed method when the position is locked.
  * Invoice fixed by checked BIN/IIN skips repeated BIN input and goes straight to amount.
  * Backend-side bot request creation enforces fixed method, so Telegram cannot bypass site rules.
  * Self-employed is fixed only by active request; draft self-employed values alone do not lock the menu.
  * Invoice/self-employed creation writes the same item tax/payment state as the site.
- app/core/config.py and app/app/core/config.py: VERSION = 0.40.3.
- README/CHANGED updated.

No DB migrations.
Railway commands are unchanged:
web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
bot: python -m app.telegram_bot.main
