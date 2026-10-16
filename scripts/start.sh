#!/usr/bin/env sh
set -e
# Compatibility: pre-0.6.6 startup removed this obsolete shadow migration.
# Changed-only installs can still retain it in Git even though FULL has none.
# Keep the canonical 0010_head_pct_overrides.py and every real migration.
rm -f alembic/versions/0010_monthly_closing_head_percent_overrides.py
# Print exact revision IDs and file paths if an unrelated extra branch remains.
alembic heads --verbose
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
