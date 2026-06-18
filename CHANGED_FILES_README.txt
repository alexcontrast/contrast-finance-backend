Contrast Finance v0.40.76

Changed files:
- app/web/app.js
- app/README.md
- app/CHANGED_FILES_README.txt
- CHANGED_FILES_README.txt

Changes:
- Admin event edit mode can always edit BIN/IIN for invoice positions.
- Admin can rerun live KGD checks from the edit modal even when BIN is locked by an active invoice request.
- Editing BIN in admin mode resets local tax status and recalculates VAT/deductions after live KGD check.
- Manual tax note updated to reflect that admin can re-enter BIN/IIN and recheck KGD.
- Web app version log updated to v0.40.76.

Checks:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
