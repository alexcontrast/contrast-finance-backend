Contrast Finance Backend v0.35.46 — changed files only

Фикс кнопок `Передать` и `Соавтор`.

Точная причина:
- кнопки в карточке мероприятия были обычными пустыми кнопками:
  `<button class="ghost">Передать</button>`
  `<button class="ghost">Соавтор</button>`
- у них не было data-атрибутов
- в текущем frontend не было обработчиков открытия меню менеджеров
- поэтому меню не могло всплыть вообще

Исправлено:
- добавлены data-атрибуты:
  - `data-manager-event-transfer`
  - `data-manager-event-coauthor`
- добавлено меню выбора менеджера через существующую модалку
- frontend вызывает существующие backend endpoints:
  - `GET /events/action-managers`
  - `POST /events/{event_id}/transfer`
  - `POST /events/{event_id}/coauthor`
- добавлены обработчики кликов в `attachManagerCreateWorkspaceActions`
- добавлены минимальные стили списка менеджеров
- app.js прошёл node --check

Backend не трогался.
Миграций нет.
