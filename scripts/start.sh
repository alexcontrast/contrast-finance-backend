#!/usr/bin/env sh
set -e
# Cleanup stale Alembic migration file from v0.5.16 if a changed-only deploy left it in place.
rm -f alembic/versions/0010_monthly_closing_head_percent_overrides.py
alembic upgrade 0011_coord_singleton
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
