v0.5.77 changed files

CHANGELOG.md
README.md
alembic/env.py
alembic/versions/0015_self_employed_accounting_groups.py
app/api/routes/self_employed_accounting.py
app/core/config.py
app/models/__init__.py
app/models/self_employed_accounting.py
app/models/self_employed_accounting_request.py
app/schemas/self_employed_accounting.py
app/web/app.js
app/web/index.html
app/web/styles.css
app/CHANGED_FILES_README.txt

Adds one-receipt-to-many-requests accounting groups for self-employed payments and
removes cancelled/rejected requests from the accounting workspace at the API
level. Deploy over v0.5-2.76; migration 0015 is applied automatically by
`alembic upgrade head`.
