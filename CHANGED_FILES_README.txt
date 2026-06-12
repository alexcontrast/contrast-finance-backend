Contrast Finance Backend v0.40.8 — changed files only

Base: v0.40.7.

Reason:
When a manager or admin cancelled/rejected a payment request, some Telegram cards could remain visible.

Exact cause:
The bot deleted only messages that were stored as active rows in `telegram_messages`. Cards sent from the ad-hoc `Мои заявки` view were not stored there, and handlers did not explicitly delete the clicked callback message as a fallback. Therefore the database status changed correctly, but the visible Telegram card could remain in chat.

Changed files:
- app/telegram_bot/main.py
  - BOT_VERSION -> CONTRAST_FINANCE_BOT_V0.40.8_NEW_SITE.
  - `Мои заявки` cards are now saved as `manager_payment_card` rows.
  - `sync_request_cards()` accepts `extra_messages` for the clicked callback message.
  - Admin reject/cancel and manager cancel pass the clicked card as a delete fallback.
  - If Telegram reports an already-deleted message, the DB row is marked deleted, not failed.
- app/core/config.py
- app/app/core/config.py
- README.md
- CHANGED_FILES_README.txt

Behavior:
- Manager/admin cancellation now deletes saved admin/manager cards plus the clicked callback card.
- Multiple manager cards for the same request from `Мои заявки` are cleaned up together.
- Tatiana cards, when enabled, are updated and not deleted.

Checks passed:
- python3 -m py_compile app/telegram_bot/main.py
- python3 -m compileall -q app
