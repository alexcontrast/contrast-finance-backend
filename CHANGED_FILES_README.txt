Contrast Finance 2.0 v0.6.2 patch over v0.6.1

Functional files:
- app/services/event_collaboration.py
- app/api/routes/events.py
- app/api/routes/manager_dashboard.py
- app/schemas/manager_dashboard.py
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

Change: an event can have one primary manager and up to two coauthors. Two participants split 50/50; three split 33.34/33.33/33.33, and every personal plan receives only its own share.
No database migration. Alembic head: 0021_avr_signed_ddc.
