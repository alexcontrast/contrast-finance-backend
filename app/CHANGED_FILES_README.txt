v0.5.71 changed files

app/api/routes/event_items.py
app/api/routes/event_summary.py
app/api/routes/tax.py
app/schemas/tax.py
app/services/payment_totals.py
app/web/app.js
app/web/index.html
CHANGELOG.md
README.md

Fixes false same-browser estimate conflicts, keeps read endpoints revision-neutral,
refreshes event/item revisions after side effects, deduplicates temporary rows,
prevents blank-row leakage, and makes row reordering stable in manager and admin editors.

Deploy over v0.5-2.70. No migration is required.
