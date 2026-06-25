# v0.5.8 — Login hotfix after legacy dry-run

## Fixed
- Fixed frontend crash on login after v0.5.7: `ReferenceError: Can't find variable: CF_PERF_LOGS_ENABLED`.
- Added explicit global frontend flag `const CF_PERF_LOGS_ENABLED = false;` before any calls to `timedApi`, `timedAction`, `perfLog` or other guarded PERF logs.
- Updated cache-bust to `0.5.8`.

## Not changed
- Business logic is unchanged.
- Legacy 2026 dry-run page and endpoint are preserved.
- Backend, Telegram bot, calculations and import behavior are unchanged.
