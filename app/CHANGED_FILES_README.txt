Contrast Finance v0.40.71

Changed files:
- app/web/app.js
- app/web/index.html
- app/api/routes/event_items.py
- app/api/routes/payment_requests.py

Changes:
- Invoice payment after successful live KGD now marks the item as locally saved, so creating the invoice request does not send a redundant PATCH /event-items/{id}.
- Draft item save uses a local saved-payload fingerprint to avoid false dirty states after backend-side KGD writes.
- Bulk-delete now uses a direct SQL UPDATE instead of loading every deleted item into ORM first.
- Bulk-delete PERF log now separates active_sql, update, commit and total.
- Invoice payment request creation skips legacy invoice restoration for already checked/locked invoice items.
- Contractor snapshot lookup for invoice requests now avoids a duplicate contractor query.
- Invoice payment request creation avoids db.refresh(request) after commit; response is built from the flushed object.
- KGD remains live-only: no BIN cache was added.
