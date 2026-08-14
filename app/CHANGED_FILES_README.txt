v0.5.73 changed files

app/api/routes/payment_requests.py
app/api/routes/tax.py
app/schemas/payment_request.py
app/schemas/tax.py
app/services/authorization.py
app/web/app.js
app/web/index.html
CHANGELOG.md
README.md
app/CHANGED_FILES_README.txt

Fixes payment-request creation for review/accepted events without reopening
ordinary estimate editing. The only forbidden combination is accepted +
cash_received. No migration is required.

Deploy over v0.5-2.72.
