Contrast Finance v0.40.77

Fixes:
- Admin payment requests manager filter now compares against resolved manager name, not a hard-coded table column / request.manager_name only.
- Archive payment requests uses the same manager filter fix.
- Payment request creation timestamp is rendered in Astana time (Asia/Almaty) in requests tables and event modal.

Changed files:
- app/web/app.js
