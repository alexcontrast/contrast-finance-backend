v0.5.75 changed files

CHANGELOG.md
README.md
alembic/versions/0014_self_employed_accounting.py
app/core/config.py
app/main.py
app/models/__init__.py
app/models/self_employed_accounting.py
app/schemas/self_employed_accounting.py
app/api/routes/self_employed_accounting.py
app/web/app.js
app/web/index.html
app/web/styles.css
app/CHANGED_FILES_README.txt

Adds the first self-employed accounting workspace: automatic rows from payment
requests, persistent receipt upload, image QR/OCR extraction, manual review,
amount checks, and an accountant-only web workspace. R-1/SIGEX signing is
reserved for the next stage after testing recognition on real e-Salyq receipts.
Migration 0014_self_employed_accounting is required.

Deploy over v0.5-2.74.
