Contrast Finance 2.0 v0.6.5 patch over v0.6.4

Functional files:
- app/api/routes/admin_dashboard.py
- app/schemas/admin_dashboard.py
- app/web/app.js
- app/web/styles.css
- tests/test_admin_tax_breakdown_v065.py

Version and documentation:
- app/web/index.html
- app/core/config.py
- README.md
- CHANGELOG.md
- CHANGED_FILES_README.txt
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Change: show accrued amount, deductions and final payable amount for VAT and taxes in the admin overview tooltip.
No database migration. Alembic head: 0021_avr_signed_ddc.
