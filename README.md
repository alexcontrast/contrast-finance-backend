Contrast Finance Backend v0.37.06 — changed files only

Фикс пустых полей в таблицах `Заявки` и `Архив заявок`.

Причина:
- frontend ожидал поля даты и заказчика под одними именами;
- backend admin-dashboard не отдавал часть этих полей явно в строке заявки.

Исправлено:
1. В AdminPaymentRequestRowRead добавлены:
   - created_at
   - client_name

2. В admin_dashboard backend-ответе по заявке теперь явно передаются:
   - request.created_at
   - event.client_name

3. Во frontend добавлены устойчивые helper-функции:
   - paymentRequestDateValue()
   - paymentRequestClientName()
   - paymentRequestManagerName()
   - paymentRequestEventTitle()

4. Таблицы `Заявки` и `Архив заявок` теперь берут:
   - Дату
   - Менеджера
   - Заказчика
   - Мероприятие
   из правильных/fallback-полей.

Миграций нет.

Проверки:
- app.js прошёл node --check
- Python-файлы компилируются
