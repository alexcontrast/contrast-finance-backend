# Contrast Finance 2.0 — v0.5.2

Hotfix for `v0.5.1 — Admin plans and closing diagnostics`.

Fixes backend startup crash caused by missing imports in `monthly_expenses.py`:

- `import logging`
- `import time`

Deploy this version instead of v0.5.1, then open admin tabs `Задать планы` and `Закрыть месяц` and collect `PERF ...` logs from browser console and Railway logs.
