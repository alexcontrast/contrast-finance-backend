Contrast Finance v0.40.68 — KGD performance diagnostics

Changed files:
- app/api/routes/tax.py
- app/services/kgd/client.py
- app/web/app.js
- app/web/index.html

Purpose:
- Add detailed backend PERF logs for /event-items/{id}/tax/check.
- Add detailed backend PERF logs inside KGD client: SNR request, VAT request, parsing/detection, total.
- Add frontend PERF logs for KGD checks from payment modal and estimate row.
- Update frontend cache-buster/version to v0.40.68.
