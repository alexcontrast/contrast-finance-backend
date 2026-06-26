# v0.5.17 — Admin head percent migration id hotfix

Hotfix over v0.5.16.

## Fixed
- Fixed Alembic startup failure caused by the too-long migration revision id `0010_monthly_closing_head_percent_overrides` not fitting into the existing `alembic_version.version_num VARCHAR(32)` column.
- Replaced it with the short revision id `0010_head_pct_overrides`.
- Made the migration idempotent with `ADD COLUMN IF NOT EXISTS` / `DROP COLUMN IF EXISTS` for extra safety after a failed deployment attempt.

## Unchanged from v0.5.16
- Admin web tab `Закрыть месяц`: head department salary percent can be overridden per month/department using the pencil near the department name.
- Empty prompt value resets override to automatic 10% / 15% logic.
- Existing closed month snapshot is recalculated after override changes.

## Not changed
- Telegram bot, legacy import, manager cabinet, payment requests, Google Sheets export and business calculations outside this feature.
