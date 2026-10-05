Contrast Finance 2.0 v0.6.1

Changed files:
- app/services/event_calculator.py
- app/api/routes/payment_requests.py
- app/api/routes/tax.py
- app/web/app.js
- app/telegram_bot/main.py
- tests/test_self_employed_deduction_v061.py
- app/web/index.html
- app/core/config.py
- README.md
- CHANGELOG.md
- CHANGED_FILES_README.txt
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Release: exact self-employed deduction base fix over stable v0.6.
Zero/empty amount_fact produces zero deductions; a positive fact produces 10% of that fact only.
No database migration. Alembic head: 0021_avr_signed_ddc.
