Contrast Finance Backend v0.37.08 — changed files only

Фикс пустого поля `Заказчик` в таблицах `Заявки` и `Архив заявок`.

Точная причина:
- в v0.37.06 frontend уже начал читать client_name;
- но backend фактически не отдавал client_name в AdminPaymentRequestRowRead;
- предыдущий автопатч не сработал, потому что искал строки:
  event_title: str
  и event_title=event.title if event else ""
- а в реальном коде были другие строки:
  event_title: str | None
  и event_title=event_title_by_id.get(request.event_id)

Исправлено:
1. В app/schemas/admin_dashboard.py в AdminPaymentRequestRowRead добавлено:
   client_name: str | None = None

2. В app/api/routes/admin_dashboard.py вместо event_title_by_id теперь используется:
   event_by_id = {event.id: event for event in events}

3. В payment_rows теперь явно отдаётся:
   client_name=event_by_id.get(request.event_id).client_name ...

Миграций нет.

Проверки:
- app.js прошёл node --check
- Python-файлы компилируются
- проверено, что client_name реально есть в схеме и backend-конструкторе строки заявки
