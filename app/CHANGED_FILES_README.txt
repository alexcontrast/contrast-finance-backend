Contrast Finance v0.5.112

Changed files:
- app/api/routes/self_employed_accounting.py
- app/web/index.html
- app/core/config.py
- nixpacks.toml
- app/README.md
- scripts/start.sh
- tests/test_accounting_receipt_v0108.py
- README.md
- CHANGELOG.md
- VERIFY_INSTALL.txt

Behavior:
- If browser OCR supplies no date, the backend reads the stored image through local Tesseract before leaving the receipt undated.
- The observed e-Salyq OCR variants `aprycta` and `aBrycta` are parsed as August only inside a complete printed date.
- A Latin OCR year suffix `r.` is accepted and the printed time is preserved.
- Missing IINs are restored from historical receipts by exact full-name match.
- Existing rows are repaired on accounting page load and before AVR generation.
- Conflicting historical IINs never auto-fill.
- QR date remains authoritative when present.
- Missing QR date is recovered from the printed receipt header/image.
- OCR date text is re-parsed on the backend with common digit-confusable repair.
- Undated receipts remain visible after a bulk refresh.

No database migration. Alembic head remains 0021_avr_signed_ddc.
