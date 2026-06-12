Contrast Finance Backend v0.40.7 — changed files only

Base: v0.40.6.

Reason:
Website-side payment status/money-status changes must update Telegram cards for manager, admin and Tatiana and trigger the same delete/update flows as Telegram button actions.

Changed files:
- app/api/routes/payment_requests.py
  - Added mark_payment_request_for_telegram_sync().
  - Status and money-status PATCH endpoints now mark active Telegram messages for immediate background sync.
- app/telegram_bot/main.py
  - BOT_VERSION -> CONTRAST_FINANCE_BOT_V0.40.7_NEW_SITE.
  - Successful edits now advance telegram_messages.updated_at.
  - Telegram "message is not modified" is treated as a successful sync.
- app/core/config.py
- app/app/core/config.py
- README.md
- CHANGED_FILES_README.txt

Behavior:
- Site changes update admin, manager and Tatiana Telegram cards via bot background polling.
- Admin/manager cards are deleted on rejected/cancelled or paid + cash_received.
- new/to_pay + cash_received still stays visible because payment status and money status are separate.
- Tatiana notification remains controlled by TELEGRAM_TATYANA_ENABLED; when enabled her card is updated but not deleted.

Checks passed:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py

No migrations.
