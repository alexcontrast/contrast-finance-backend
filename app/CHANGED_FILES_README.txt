Contrast Finance Backend v0.38.7 — changed files only

Base: v0.38.6.

Changed files:
- app/web/app.js
- app/web/index.html
- app/core/config.py
- app/app/core/config.py
- README.md
- CHANGED_FILES_README.txt
- app/README.md
- app/CHANGED_FILES_README.txt

Fix:
- «Мои оплаты» у менеджера больше не попадает под широкий стиль модалки мероприятия на 1280px.
- Причина была в CSS-специфичности общего селектора eventModalBackdrop.
- Общий широкий стиль теперь не применяется к `manager-payments-modal` и `manager-requests-modal-mode`.

No DB migrations.
