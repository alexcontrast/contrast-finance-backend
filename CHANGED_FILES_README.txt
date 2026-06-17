Contrast Finance v0.40.61 CHANGED ONLY

Changes:
- Added /manager-dashboard-bundle endpoint.
- Manager cabinet now loads dashboard + monthly payment requests + full current-month event payloads in one backend request.
- Manager event switching uses cached event payloads from the initial bundle, so already loaded events open without intermediate loading/network requests.
- Updated web cache-buster and app version to 0.40.61.

Changed files:
- app/api/routes/manager_dashboard.py
- app/schemas/manager_dashboard.py
- app/web/app.js
- app/web/index.html
- app/core/config.py
