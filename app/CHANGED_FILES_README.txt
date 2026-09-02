Contrast Finance v0.5.116

Changed files:
- app/api/routes/self_employed_accounting.py
- app/web/app.js
- app/web/styles.css
- app/web/index.html
- app/core/config.py
- tests/test_accounting_receipt_only_v0116.py
- README.md
- CHANGELOG.md

Behavior:
- Accounting is receipt-only: payment requests stay in their existing request tabs.
- Batch receipt import no longer auto-matches payment requests.
- Receipt edits, act generation, deletion, QR refresh and signature polling update rows in-place.
- Status filters: no act / unsigned / no self-employed signature.
- Historical request links remain stored but are hidden from the accounting UI.

No database migration. Alembic head remains 0021_avr_signed_ddc.
