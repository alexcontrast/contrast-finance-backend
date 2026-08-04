v0.5.68 changed files

app/api/routes/admin_dashboard.py
app/api/routes/manager_dashboard.py
app/api/routes/monthly.py
app/api/routes/monthly_closings.py
app/schemas/admin_dashboard.py
app/web/app.js
app/web/index.html
CHANGELOG.md
README.md

The admin first screen now uses a compact monthly bundle. Users, expenses and
the canonical closing preview are included without extra requests; full event
cards and yearly plans prefetch after the first render.

Deploy over v0.5.67. No migration is required.
