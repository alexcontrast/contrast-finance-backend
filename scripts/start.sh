#!/usr/bin/env sh
set -e
# Deploy the full source, or apply the 0.6.6 patch to the exact 0.6.5 base.
# Historical source cleanup belongs to deployment, never container startup.
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
