Contrast Finance v0.5.121

Changed files:
- app/api/routes/act_signing.py
- app/web/app.js
- app/web/index.html
- app/core/config.py
- app/services/self_employed_identity_lookup.py
- tests/test_accounting_whatsapp_preview_v0120.py
- README.md
- CHANGELOG.md
- CHANGED_FILES_README.txt
- VERIFY_INSTALL.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Feature: WhatsApp/Open Graph title for public AVR signing links now contains contractor surname + first name.
Title format: АВР Contrast-{Фамилия} {Имя} на сумму {Сумма} ₸ от {ДД.ММ.ГГГГ}.
Patronymic is not included.
No database migration.
