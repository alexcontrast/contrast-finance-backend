# Contrast Finance v0.5.9

Hotfix for the legacy Jan-Apr 2026 dry-run page.

After deploy:
1. Open `/legacy-events-2026`.
2. Enter `LEGACY_MIGRATION_TOKEN`.
3. Keep manager as `Тест`.
4. Select the `.xlsx` report.
5. The page should immediately show the selected file name and size.
6. Press `Запустить dry-run`.

This version does not write anything to the database. It only reads the XLSX and displays detected events/budgets.
