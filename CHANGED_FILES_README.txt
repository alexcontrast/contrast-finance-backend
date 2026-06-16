Contrast Finance v0.40.46

Fix:
- app/api/routes/payment_requests.py: added missing import for sync_item_paid_amount_from_requests.

Root cause:
- PATCH /payment-requests/{id}/status called sync_item_paid_amount_from_requests after v0.40.40, but the function was not imported in this route module.
- Telegram had this import, web API route did not. Therefore the site returned HTTP 500 when admin changed a request status to paid/rejected.

Checks:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
