v0.5.17 — Admin head percent migration id hotfix

Changed files:
- alembic/versions/0010_head_pct_overrides.py
- app/web/app.js
- app/web/index.html
- CHANGELOG.md
- README.md
- app/CHANGED_FILES_README.txt

Reason:
- v0.5.16 migration revision id was too long for alembic_version.version_num VARCHAR(32).
- v0.5.17 uses short revision id 0010_head_pct_overrides and keeps the same feature.
