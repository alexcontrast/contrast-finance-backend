# v0.40.110 — Admin paid instant update + manager percent lock

## Fixed
- Admin event modal customer payment (`Оплачено`) now updates immediately in the open modal after saving, without requiring a page refresh.
- The open event modal payload now patches `customer_paid_amount` and `customer_remaining_amount` locally after `/events/{id}/customer-payment` succeeds.
- Manager-side event PATCH no longer overwrites `manager_percent`; only admin actions can change the manager percent.
- This prevents a manager sending a draft/revision event to review from accidentally resetting an admin-set manager percent back to 21%.

## Scope
- Changed `app/web/app.js`, `app/web/index.html`, `app/api/routes/events.py`.
- No Apps Script changes.
