v0.40.34: hide customer paid metric from department-head event modal

Contrast Finance v0.40.27

Изменено:
- Во вкладке "Обзор" админки менеджеры внутри каждого отдела сортируются по выполнению личного плана: сверху самый высокий процент, затем факт дохода, затем количество мероприятий.
- Во вкладке "Обзор" главдепа менеджеры отдела сортируются по тому же принципу.
- Для первого менеджера в списке добавлен компактный значок 🏆, если есть положительное выполнение плана.
- Обновлены версии и cache-bust фронта.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
## v0.40.29

- Admin overview now shows total monthly events as green badges for the whole company and separately for each department.
- Department-head overview now shows the department monthly event count as a badge near the department plan.
- Counts include all events returned for the selected month, including completed/archive events.
