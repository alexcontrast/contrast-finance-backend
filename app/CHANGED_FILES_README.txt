v0.5.69 changed files

app/api/routes/admin_dashboard.py
app/api/routes/web.py
app/main.py
app/web/app.js
app/web/index.html
CHANGELOG.md
README.md

The compact admin bundle now selects only first-screen fields, reuses already
loaded paid requests, restores the last successful month immediately and
refreshes it in the background. Versioned web assets use browser caching and
GZip; detailed event cards load on demand instead of prefetching the full month.

Deploy over v0.5.68. No migration is required.
