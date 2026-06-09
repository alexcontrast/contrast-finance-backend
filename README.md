Contrast Finance Backend v0.35.34 — changed files only

Миникарточка теперь живая мини-сводка основной карточки.

Frontend:
- миникарточка получила отдельные элементы:
  - `data-mini-title`
  - `data-mini-meta`
  - `data-mini-calc`
  - `data-mini-status`
- при изменении основной карточки в прямом эфире обновляются:
  - название мероприятия
  - заказчик
  - дата
  - тип расчёта
  - статус
  - бюджет
  - доход
- `setDraftEventValue()` теперь синхронизирует `state.currentManagerEvent`
- `updateCurrentManagerMiniCardLive()` обновляет не только бюджет/доход, а всю миникарточку текущего мероприятия
- app.js проверен через `node --check`

index.html подключает app.js/styles.css с ?v=0.35.34

Миграций нет.
