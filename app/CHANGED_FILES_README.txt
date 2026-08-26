v0.5.74 changed files

app/services/payment_totals.py
app/web/app.js
app/web/index.html
CHANGELOG.md
README.md
app/CHANGED_FILES_README.txt

Fixes frequent false optimistic-lock conflicts after payment/request status
changes. Derived paid_amount updates no longer advance EventItem.updated_at.
The web editor safely auto-rebases non-overlapping event/item changes once,
while true same-field conflicts remain blocked. No migration is required.

Deploy over v0.5-2.73.
