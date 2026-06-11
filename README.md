Contrast Finance Backend v0.37.00 — changed files only

Большой технический фикс: разделение рабочего статуса и статуса денег.

Новая логика:
1. Мероприятие:
   - status: draft / review / accepted / revision / cancelled
   - money_status: waiting_money / cash_received

2. Заявка на оплату:
   - status: new / to_pay / paid / rejected / tax_check_needed
   - money_status: waiting_money / cash_received

Что исправлено:
- `Деньги в кассе` больше не является рабочим статусом мероприятия.
- `Деньги в кассе` больше не является статусом оплаты подрядчику.
- Кнопка `Деньги в кассе` по мероприятию теперь:
  - ставит event.money_status = cash_received;
  - ставит payment_requests.money_status = cash_received;
  - НЕ меняет event.status;
  - НЕ меняет payment_requests.status.
- `Вернуть в работу` меняет только event.status на revision.
  Статус денег по мероприятию и заявкам не трогается.
- Заявка может быть `Новая`, но при этом `Деньги в кассе`.
- Мероприятие может быть `На доработке`, но при этом `Деньги в кассе`.
- Активные/архивные заявки больше не завязаны на `Деньги в кассе`.
- Архив мероприятий теперь смотрит на money_status, а не на status.

Миграция:
- добавляет events.money_status;
- добавляет payment_requests.money_status;
- старые events.status='cash_received' переводит в:
  status='accepted', money_status='cash_received';
- старые payment_requests.status='cash_received' переводит в:
  money_status='cash_received',
  status='paid' если paid_at не пустой, иначе status='new'.

Изменён backend:
- app/models/event.py
- app/models/payment_request.py
- app/schemas/event.py
- app/schemas/payment_request.py
- app/schemas/admin_dashboard.py
- app/schemas/manager_dashboard.py
- app/api/routes/events.py
- app/api/routes/payment_requests.py
- app/api/routes/admin_dashboard.py
- app/api/routes/manager_dashboard.py
- alembic/versions/0007_split_money_status.py

Проверки:
- app.js прошёл node --check
- Python-файлы компилируются
