Contrast Finance v0.40.58

Изменения:
- Усилена защита фронтенда от дублей запросов при переключении месяцев в кабинете менеджера.
- Добавлен debounce на переключатель месяц/год, чтобы одно действие не запускало несколько одинаковых загрузок.
- Добавлен single-flight/cache для manager-dashboard, payment-requests и деталей открытого мероприятия.
- /payment-requests теперь принимает month=YYYY-MM и для менеджеров загружает заявки актуального месяца, а не весь список.
- В admin-dashboard убран лимит 50 заявок: во вкладках заявок показываются все заявки выбранного месяца.
- app.js cache-buster обновлён до v0.40.58.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
