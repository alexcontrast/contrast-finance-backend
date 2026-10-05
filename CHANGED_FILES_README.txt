Contrast Finance 2.0 v0.6.1 patch over v0.6

Functional files:
- app/services/event_calculator.py
- app/api/routes/payment_requests.py
- app/api/routes/tax.py
- app/web/app.js
- app/telegram_bot/main.py
- tests/test_self_employed_deduction_v061.py

Version and documentation:
- app/web/index.html
- app/core/config.py
- README.md
- CHANGELOG.md
- CHANGED_FILES_README.txt
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Change: self-employed deductions are calculated strictly from amount_fact. Empty or zero fact never falls back to the external estimate.
No database migration. Alembic head: 0021_avr_signed_ddc.
