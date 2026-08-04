v0.5.70 changed files

app/api/routes/coordinator.py
app/api/routes/event_items.py
app/api/routes/events.py
app/api/routes/manager_dashboard.py
app/api/routes/payment_requests.py
app/api/routes/tax.py
app/schemas/event.py
app/schemas/event_item.py
app/schemas/manager_dashboard.py
app/schemas/tax.py
app/services/payment_totals.py
app/web/app.js
app/web/index.html
CHANGELOG.md
README.md

The manager cabinet now starts from a compact month payload, loads one full
estimate on demand, protects event/item revisions across browsers, serializes
autosave and manual saves, and makes temporary row creation idempotent and
atomic. Live sync covers item, KGD, coordinator and payment-request changes.

Deploy over v0.5.69. No migration is required.
