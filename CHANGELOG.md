# CHANGELOG

## v0.5.2 — Admin diagnostics import hotfix

Base: stable Contrast Finance 2.0 `0.5` + diagnostic patch `v0.5.1`.

### Fixed
- Fixed backend startup crash in `app/api/routes/monthly_expenses.py`.
- Added missing imports `logging` and `time` required by the diagnostic performance logger.

### Notes
- This is a hotfix for diagnostics only.
- No business logic, UI behavior, Telegram bot logic, admin calculations, manager cabinet, or department-head cabinet behavior was changed.
