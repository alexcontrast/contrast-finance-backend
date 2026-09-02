Contrast Finance v0.5.109

Changed files:
- app/api/routes/self_employed_accounting.py
- app/web/app.js
- app/web/index.html
- app/core/config.py
- scripts/start.sh
- tests/test_accounting_receipt_v0108.py
- tests/test_accounting_date_parser_v0109.js
- README.md
- CHANGELOG.md

Behavior:
- QR date remains authoritative when present.
- Missing QR date is recovered from the printed receipt header/image.
- OCR date text is re-parsed on the backend with common digit-confusable repair.
- Undated receipts remain visible after a bulk refresh.

No database migration. Alembic head remains 0021_avr_signed_ddc.
