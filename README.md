# Contrast Finance 2.0 — v0.5.18

Clean build after completing the January–April 2026 historical events import.

This version removes the temporary import pages and scripts, while keeping the admin feature for manually overriding department-head salary percent in the `Закрыть месяц` tab.

## Important
Use the full archive when deploying this version, so temporary import files are physically absent from the deployment.

## Checks
- `node --check app/web/app.js`
- `py_compile` for changed/affected backend files
