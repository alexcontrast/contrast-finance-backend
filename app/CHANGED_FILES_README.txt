v0.5.18 — Legacy import cleanup, keep head percent override

Changed files:
- app/main.py
- app/web/index.html
- app/web/app.js
- requirements.txt
- CHANGELOG.md
- README.md
- app/CHANGED_FILES_README.txt

Deleted temporary import files from full archive:
- app/api/routes/legacy_events_2026.py
- app/api/routes/legacy_migration.py
- app/services/legacy_events_2026_importer.py
- app/services/legacy_importer.py

Kept required DB migration for the head percent override:
- alembic/versions/0010_head_pct_overrides.py

Deploy full archive to physically remove deleted files. Changed-only is safe for runtime because routes are no longer imported, but full archive is cleaner.
