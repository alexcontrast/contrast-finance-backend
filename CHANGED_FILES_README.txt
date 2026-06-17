Contrast Finance v0.40.65 — CHANGED ONLY

Заменить файлы:
- app/web/app.js
- app/web/index.html
- app/api/routes/payment_requests.py

Изменения:
- Ускорено создание обычных заявок На карту/Налик: лишний PATCH позиции пропускается, если позиция уже сохранена и поля оплаты не меняются.
- Добавлен PERF web manager-payment-prepare-simple-skip-persist.
- Backend create payment request возвращает ответ быстрее и пишет PERF payment-request-create.

Проверки:
python3 -m compileall -q app
python3 -m py_compile app/telegram_bot/main.py
node --check app/web/app.js
