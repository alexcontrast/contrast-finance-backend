# CHANGELOG

## v0.5.13 — Admin event edit modal fresh refresh

- Исправлено поведение админской модалки редактирования мероприятия: после нажатия `Сохранить изменения` открытая модалка теперь перезагружает данные мероприятия принудительно из backend, а не берёт старый payload из локального cache.
- Перед повторным открытием модалки очищается `eventModalPayloadById[eventId]` и `currentEventModalPayload`, затем вызывается `openEventModal(eventId, { force: true })`.
- `openEventModal` получил опцию `force`, чтобы можно было явно обходить cache после операций сохранения.
- Cache-bust обновлён до `0.5.13`.
- Backend, импорт исторических мероприятий, Telegram-бот, расчёты, заявки и Google Sheets не менялись.
