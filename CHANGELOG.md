# CHANGELOG

## v0.5.19 — Alembic stale migration cleanup start hotfix

- Fixed Railway startup failure: `Multiple head revisions are present for given argument 'head'`.
- Cause: a stale v0.5.16 migration file (`0010_monthly_closing_head_percent_overrides.py`) could remain in deployments made with changed-only patches, creating a second Alembic head alongside the valid short migration.
- Added `scripts/start.sh` that removes the stale long migration file before running Alembic.
- Changed `Procfile` to run `sh scripts/start.sh`.
- Alembic now upgrades explicitly to `0010_head_pct_overrides`.
- Kept the admin month-closing head department percent override feature.
- No changes to Telegram bot, imports, payments, Google Sheets export, manager cabinet, or calculations beyond the existing head percent override.
