Contrast Finance v0.40.78

Changed files:
- app/api/routes/payment_requests.py
- app/web/app.js
- app/CHANGED_FILES_README.txt
- app/README.md

Notes:
- Added admin-only refund endpoint for paid payment requests.
- Archive "Вернуть" now reverses paid requests atomically instead of calling ordinary cancel.
- Ordinary cancel still blocks paid requests; manager behavior is unchanged.
- Refund recalculates event item paid_amount and marks Telegram sync dirty.
