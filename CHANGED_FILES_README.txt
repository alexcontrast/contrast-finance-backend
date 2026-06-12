Contrast Finance Backend v0.38.6 — changed files only

База: v0.38.5

Изменённые файлы:
- README.md
- CHANGED_FILES_README.txt
- app/core/config.py
- app/app/core/config.py
- app/web/index.html
- app/web/styles.css

Что сделано:
1. Исправлена реальная причина смещения `План/Цель` в кабинете главдепа.
2. Предыдущая grid-схема `1fr / 1fr / 72px` центрировала план внутри второй колонки, а не по центру всей шкалы.
3. Верхняя шкала отдела теперь использует независимое позиционирование: факт слева, план по центру, процент справа.
4. Строки менеджеров отдела получили такую же фиксацию: факт слева, план по центру, процент справа.

Backend/миграции:
- Не менялись.

Проверки:
- node --check app/web/app.js
- python3 -m compileall -q app
