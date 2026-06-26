v0.5.16 — Admin closing head percent override

Copy/replace changed files from this archive over v0.5.15.

Important: this patch includes a database migration:
- alembic/versions/0010_monthly_closing_head_percent_overrides.py

Railway startup/alembic must apply the migration before the app uses the new fields.

Changed files:
- app/api/routes/monthly_closings.py
- app/models/monthly_closing.py
- app/schemas/monthly_closing.py
- app/schemas/admin_dashboard.py
- app/api/routes/admin_dashboard.py
- app/web/app.js
- app/web/styles.css
- app/web/index.html
- alembic/versions/0010_monthly_closing_head_percent_overrides.py
- CHANGELOG.md
- README.md
