# Contrast Finance 2.0 — v0.5.17

Hotfix build for the admin monthly closing head percent override feature.

## Why this build exists
v0.5.16 added the correct feature, but its Alembic migration revision id was longer than the production `alembic_version.version_num VARCHAR(32)` field:

`0010_monthly_closing_head_percent_overrides`

PostgreSQL rejected the version update with `StringDataRightTruncation`.

## Fix
- Migration file is renamed to `alembic/versions/0010_head_pct_overrides.py`.
- Migration revision id is now `0010_head_pct_overrides`.
- The column changes are idempotent.

## Feature kept
In admin web → `Закрыть месяц`, the department head salary percent can be manually overridden per month/department through the pencil button near the department name. Blank value resets to auto 10%/15%.
