Contrast Finance Backend v0.35.99 — changed files only

Шлифовка вкладки админки `Мероприятия`.

Изменено:
- добавлен столбец `Оплата` в строках мероприятий;
- столбец расположен между `Мероприятие` и `Статус`;
- в нём показывается тип расчёта с заказчиком:
  - Contrast Event
  - ОУР без НДС
  - Упрощенка
  - Нал

Изменён backend:
- app/api/routes/admin_dashboard.py
- app/schemas/admin_dashboard.py

Миграций нет.

Проверки:
- app.js прошёл node --check
- Python-файлы компилируются
