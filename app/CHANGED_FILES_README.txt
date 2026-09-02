Contrast Finance v0.5.110

Changed files:
- app/api/routes/self_employed_accounting.py
- app/web/index.html
- app/core/config.py
- app/README.md
- scripts/start.sh
- tests/test_accounting_receipt_v0108.py
- README.md
- CHANGELOG.md
- VERIFY_INSTALL.txt

Behavior:
- Missing IINs are restored from historical receipts by exact full-name match.
- Existing rows are repaired on accounting page load and before AVR generation.
- Conflicting historical IINs never auto-fill.
- QR date remains authoritative when present.
- Missing QR date is recovered from the printed receipt header/image.
- OCR date text is re-parsed on the backend with common digit-confusable repair.
- Undated receipts remain visible after a bulk refresh.

No database migration. Alembic head remains 0021_avr_signed_ddc.
