Contrast Finance Backend v0.38.5 — changed files only

База: v0.38.4

Изменённые файлы:
- README.md
- CHANGED_FILES_README.txt
- app/core/config.py
- app/app/core/config.py
- app/web/index.html
- app/web/app.js
- app/web/styles.css

Что сделано:
1. В кабинете главдепа центрирован `План/Цель` в верхней шкале отдела.
2. Расходы отдела убраны из нижнего блока вкладки `Итог`.
3. Карточка `Расходы` стала кнопкой, открывающей отдельную независимую модалку.
4. Добавлен новый DOM-контейнер `departmentExpensesModalBackdrop`, не переиспользующий event/plans модалки.
5. Таблица расходов в модалке сделана компактной, суммы выровнены по центру.

Backend/миграции:
- Не менялись.

Проверки:
- node --check app/web/app.js
- python3 -m compileall -q app
