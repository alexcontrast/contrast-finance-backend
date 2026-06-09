Contrast Finance Backend v0.35.50 — changed files only

Фикс основной карточки после назначения соавтора.

Точная причина:
- миникарточка берёт данные напрямую из свежего manager-dashboard
- основная карточка использует getDraftEvent(event)
- getDraftEvent создавал draft event один раз и потом возвращал старую копию
- поэтому после назначения соавтора новые поля dashboard:
  is_coauthored / coauthor_name / coauthor_user_id / share_percent
  не попадали в state.currentManagerEvent
- результат: миникарточка уже с бейджем, а основная карточка всё ещё со старой кнопкой `Соавтор` и без бейджа

Исправлено:
- getDraftEvent теперь обновляет служебные поля соавторства в существующем draft event
- добавлен setCoauthorStateForEvent(eventId, managerId, managerName)
- после POST /coauthor локальное состояние обновляется сразу
- после loadDashboard основная карточка перерисовывается уже с:
  - кнопкой `Удалить соавтора`
  - синим бейджем `Соавтор: имя`
  - share_percent=50 для live-preview
- app.js прошёл node --check

Backend не трогался.
Миграций нет.
