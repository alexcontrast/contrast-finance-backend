v0.5.78 changed files

CHANGELOG.md
README.md
alembic/versions/0015_self_employed_accounting_groups.py
app/core/config.py
app/web/app.js
app/web/index.html
app/CHANGED_FILES_README.txt

Shortens the pending 0015 revision identifier from 36 to 25 characters so it
fits Alembic's production VARCHAR(32) version column. PostgreSQL rolled the
failed v0.5-2.77 attempt back to 0014, so redeploying this patch is sufficient;
no manual SQL or data repair is required.
