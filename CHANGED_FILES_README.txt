Contrast Finance v0.40.15 — changed files only

Changed files:
- app/api/routes/legacy_migration.py
- app/core/config.py
- app/app/core/config.py
- README.md
- app/README.md

Fix:
- Legacy migration page now shows an explicit selected JSON file indicator.
- Buttons are bound with addEventListener instead of inline onclick.
- File is parsed immediately after selection, so Safari/cache issues are visible before dry-run/import.
- Clearer message when the selected file is missing or invalid.
