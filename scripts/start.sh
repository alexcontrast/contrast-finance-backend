#!/usr/bin/env sh
set -e
# Exact cleanup keeps changed-only deployments safe when old v0.5.107 files
# remain in the repository. The full v0.5.112 archive does not contain them.
rm -f alembic/versions/0010_monthly_closing_head_percent_overrides.py
rm -f app/web/accounting-receipt-fix.js app/web/accounting-date-fix.js
rm -f app/services/accounting_receipt_date_fix.py
rm -f app/app/api/routes/auth.py app/app/core/config.py app/app/schemas/auth.py app/app/services/auth.py
rm -f CHANGELOG_v0.40.55.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
