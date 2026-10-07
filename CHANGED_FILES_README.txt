Contrast Finance 2.0 v0.6.3 patch over v0.6.2

Functional files:
- app/api/routes/events.py
- app/web/app.js
- tests/test_three_manager_collaboration_v062.py

Version and documentation:
- app/web/index.html
- app/core/config.py
- README.md
- CHANGELOG.md
- CHANGED_FILES_README.txt
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Change: fix the SQLAlchemy relationship replacement that prevented the third manager from being persisted. The UI now shows the recalculated share and reports failures instead of swallowing them.
No database migration. Alembic head: 0021_avr_signed_ddc.
