v0.40.35: hide customer paid metric from manager event modal

Changed:
- app/web/app.js
- app/web/index.html
- app/core/config.py
- app/app/core/config.py
- app/telegram_bot/main.py

Fix:
- Блок «Оплачено / Остаток» теперь отображается только админу: в обычной админской модалке и в режиме админ-редактирования.
- У менеджера во внутренней смете блок больше не показывается.
- У главдепа блок был скрыт в v0.40.34 и остаётся скрытым.
