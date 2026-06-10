Contrast Finance Backend v0.35.89 — changed files only

Шлифовка вкладки админки `Мероприятия`.

Исправлено:
1. Заливка статуса мероприятия теперь цельная по всей строке,
   а не кусками по отдельным ячейкам/полям.

2. Во вкладке `Мероприятия` теперь отображается `ЗП менеджера`.

3. Во вкладке `Мероприятия` теперь отображается количество заявок:
   - active_payment_requests_count
   - fallback payment_requests_count

Точная причина отсутствия ЗП/заявок:
- frontend уже пытался читать `event.manager_salary` и `event.active_payment_requests_count`
- но backend `admin-dashboard` эти поля не отдавал
- schema админки тоже не содержала эти поля, поэтому они не попадали в JSON

Изменён backend:
- app/api/routes/admin_dashboard.py
- app/schemas/admin_dashboard.py

Миграций нет.

Проверки:
- app.js прошёл node --check
- Python-файлы компилируются
