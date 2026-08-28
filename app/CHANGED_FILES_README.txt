v0.5.76 changed files

CHANGELOG.md
README.md
scripts/start.sh
app/core/config.py
app/CHANGED_FILES_README.txt

Fixes the HTTP 500 in the new self-employed accounting workspace. v0.5-2.75
shipped migration 0014_self_employed_accounting but startup was still pinned to
0013_manager_bonus, so production never created the new table. Startup now runs
`alembic upgrade head` before uvicorn.

Deploy over v0.5-2.75. No new migration file is added; the existing 0014 migration
will be applied automatically on restart.
