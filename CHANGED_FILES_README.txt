Contrast Finance 2.0 v0.6.4 patch over v0.6.3

Functional files:
- app/api/routes/users_manage.py
- app/web/app.js
- app/web/styles.css
- tests/test_add_manager_v064.py

Version and documentation:
- app/web/index.html
- app/core/config.py
- README.md
- CHANGELOG.md
- CHANGED_FILES_README.txt
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Change: add one `+ Менеджер` action beside `Сменить PIN`; name, phone, department and PIN are entered while the manager role is assigned automatically.
No database migration. Alembic head: 0021_avr_signed_ddc.
