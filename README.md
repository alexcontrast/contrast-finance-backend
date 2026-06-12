Contrast Finance v0.40.19 — changed files only

Changed files:
- app/web/app.js
- app/web/index.html
- app/core/config.py
- app/app/core/config.py
- app/telegram_bot/main.py

v0.40.19:
- Added the missing "Комиссия" column in the event estimate table inside the event modal.
- The column is placed between "Оплата" and "НДС".
- This applies to the admin event modal and the department-head read-only event modal because they share the same event modal renderer.
- Bumped frontend cache-bust to /web/app.js?v=0.40.19.
