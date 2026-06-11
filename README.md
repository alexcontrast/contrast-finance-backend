Contrast Finance Backend v0.37.01 — changed files only

Срочный фикс запуска после v0.37.00.

Причина падения:
- в app/api/routes/payment_requests.py появился роут:
  PATCH /payment-requests/{request_id}/money-status
- он использует схему PaymentRequestMoneyStatusUpdate;
- в боевом файле схема не была импортирована/подтянута корректно;
- из-за этого приложение падало при старте с NameError.

Исправлено:
- добавлен/проверен класс PaymentRequestMoneyStatusUpdate в app/schemas/payment_request.py;
- полностью заменён импортный блок app.schemas.payment_request в app/api/routes/payment_requests.py;
- проверено статически, что PaymentRequestMoneyStatusUpdate реально импортируется в payment_requests.py.

Миграция 0007 остаётся той же, новой миграции нет.

Проверки:
- app.js прошёл node --check
- Python-файлы компилируются
- AST-проверка подтверждает импорт PaymentRequestMoneyStatusUpdate
