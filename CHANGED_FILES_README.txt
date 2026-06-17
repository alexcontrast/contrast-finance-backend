Contrast Finance v0.40.70

Changed files:
- app/web/app.js
- app/web/index.html
- app/api/routes/event_items.py

Changes:
- Draft save deletes event items through one bulk-delete request instead of multiple DELETE requests.
- Added backend PERF logs for event item create/update/delete/bulk-delete.
- Event item create/update/delete avoid extra db.refresh by returning a validated response built before commit.
- Invoice payment creation skips redundant PATCH after successful KGD check when item is already saved and unchanged.
- KGD stays live-only: no BIN cache was added.
