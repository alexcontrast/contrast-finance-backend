Contrast Finance v0.5.122

Changed files:
- app/api/routes/monthly_expenses.py
- app/web/index.html
- app/core/config.py
- tests/test_monthly_expense_order_v0122.py
- README.md
- CHANGELOG.md
- CHANGED_FILES_README.txt
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Feature: expenses in `Закрыть месяц` are sorted by creation time from newest to oldest.
Stable tie-breaker: id DESC.
No database migration.
