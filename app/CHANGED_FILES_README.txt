Contrast Finance v0.5.108

Changed files:
- app/api/routes/self_employed_accounting.py
- app/api/routes/payment_requests.py
- app/api/routes/coordinator.py
- app/services/accounting_receipt_data_fix.py (parser utilities; runtime patch removed)
- app/telegram_bot/main.py
- app/web/app.js
- app/web/index.html
- app/main.py
- app/core/config.py
- scripts/start.sh
- README.md
- CHANGELOG.md

Removed obsolete files:
- alembic/versions/0010_monthly_closing_head_percent_overrides.py
- app/services/accounting_receipt_date_fix.py
- app/web/accounting-date-fix.js
- app/web/accounting-receipt-fix.js
- nested duplicate app/app sources
- CHANGELOG_v0.40.55.txt

No database migration. Alembic head remains 0021_avr_signed_ddc.
