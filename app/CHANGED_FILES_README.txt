Contrast Finance v0.5.120

Changed files:
- app/api/routes/act_signing.py
- app/web/sign_avr.html
- app/web/app.js
- app/web/index.html
- app/core/config.py
- app/services/self_employed_identity_lookup.py
- tests/test_accounting_whatsapp_preview_v0120.py
- README.md
- CHANGELOG.md
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Feature: dynamic WhatsApp/Open Graph title for public AVR signing links.
Title format: АВР Contrast-{Фамилия} на сумму {Сумма} ₸ от {ДД.ММ.ГГГГ}.
Packaging/docs cleanup included.
No database migration.
