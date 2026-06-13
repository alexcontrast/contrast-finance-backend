Contrast Finance v0.40.28

Changed:
- app/web/app.js
- app/web/index.html
- app/core/config.py
- app/app/core/config.py
- app/telegram_bot/main.py

Fix:
- Admin event-level "Деньги в кассе" button no longer disables just because one payment request already has money_status=cash_received.
- Button disables only when the event itself is already cash_received.

Contrast Finance v0.40.28

Изменено:
- Во вкладке "Обзор" админки менеджеры внутри каждого отдела сортируются по выполнению личного плана: сверху самый высокий процент, затем факт дохода, затем количество мероприятий.
- Во вкладке "Обзор" главдепа менеджеры отдела сортируются по тому же принципу.
- Для первого менеджера в списке добавлен компактный значок 🏆, если есть положительное выполнение плана.
- Обновлены версии и cache-bust фронта.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
