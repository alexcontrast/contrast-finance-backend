Contrast Finance Backend v0.35.3 — changed files only

Backend fix создания мероприятия.

Проблема:
POST /events создавал Event со строкой:

    status=payload.status

Но в схеме EventCreate поля status нет, поэтому создание мероприятия падало.

Исправлено:

    status="draft"

Теперь новое мероприятие из кабинета менеджера создаётся как Черновик.

Дополнительно:
- index.html подключает app.js/styles.css с ?v=0.35.3

Миграций нет.
