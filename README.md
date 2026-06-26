# Contrast Finance 2.0 — v0.5.16

Patch over v0.5.15.

Purpose: allow admin to manually set department-head salary percent for a specific month in the desktop Admin closing tab.

## Changed

- Admin → “Закрыть месяц”: pencil button next to each department in the calculation block.
- Admin can enter a custom head salary percent for the selected month.
- Empty value resets the department back to automatic 10% / 15% calculation.
- Overrides are stored per month and per department.
- Closing and recalculation use the override.
- Closed month snapshot updates if the override is changed after closing.

## Changed files

- `app/api/routes/monthly_closings.py`
- `app/models/monthly_closing.py`
- `app/schemas/monthly_closing.py`
- `app/schemas/admin_dashboard.py`
- `app/api/routes/admin_dashboard.py`
- `app/web/app.js`
- `app/web/styles.css`
- `app/web/index.html`
- `alembic/versions/0010_monthly_closing_head_percent_overrides.py`
