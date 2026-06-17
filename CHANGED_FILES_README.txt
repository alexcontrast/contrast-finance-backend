Contrast Finance v0.40.57

Changed files:
- app/web/app.js
  * Removed duplicate month-switch/dashboard loads by cleaning stale month/year listeners.
  * Added loadDashboard in-flight guard by role+month.
- app/web/index.html
  * Updated app.js cache-buster to v0.40.57.
- app/api/routes/payment_requests.py
  * Optimized GET /payment-requests: one joined SQL query instead of per-row db.get(Event/User).
  * Added PERF payment-requests log.
