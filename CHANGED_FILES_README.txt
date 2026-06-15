Contrast Finance v0.40.40

База: v0.40.39.

Правка:
- Исправлена рассинхронизация: заявки могли быть paid, но EventItem.paid_amount оставался 0, из-за чего в смете колонка «Оплата» показывала 0.
- Добавлен единый source-of-truth пересчёт paid_amount из payment_requests со status='paid'.
- Пересчёт вызывается при смене статуса заявки на сайте, при Telegram-действиях, а также перед чтением сметы/summary мероприятия, чтобы починить уже накопленные старые рассинхроны.

Проверки:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js
