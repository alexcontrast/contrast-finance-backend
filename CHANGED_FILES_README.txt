Contrast Finance Backend v0.40.6 — changed files only

Base: v0.40.5.

Changed files:
- app/telegram_bot/main.py
  * BOT_VERSION = CONTRAST_FINANCE_BOT_V0.40.6_NEW_SITE.
  * Self-employed flow asks for surname instead of failing request creation.
  * Existing self-employed surname from item/internal note is reused automatically.
  * Self-employed surname is saved back to item internal_note after Telegram request.
  * Invoice cards use KGD legal entity name as contractor.
  * Extra Telegram positions are created with external estimate amount 0 and fact amount = request amount.
- app/api/routes/payment_requests.py
  * Invoice payment request snapshots store KGD legal name from contractors/taxpayer checks.
- app/web/app.js
  * Payment modal no longer PATCHes the whole event before creating payment requests.
  * This allows payment extra positions on review/accepted events without opening event editing.
- app/web/index.html
  * Cache-bust v0.40.6.
- app/core/config.py and app/app/core/config.py
  * VERSION = 0.40.6.

Checks:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js

No database migrations.
