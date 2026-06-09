Contrast Finance Backend v0.35.35 — changed files only

Аварийный фикс работы сметы после v0.35.34.

Причина:
- live-обновление миникарточки вызывало `getManagerDashboardEvent(...)`
- этой функции в текущем app.js не было
- из-за ReferenceError ломалась цепочка:
  выбор способа оплаты → пересчёт → КГД → обновление НДС/Вычетов

Исправлено:
- добавлена функция `getManagerDashboardEvent(eventId)`
- `updateCurrentManagerMiniCardLive()` обёрнута в try/catch
- теперь ошибка миникарточки не может сломать работу сметы, выбора способа оплаты или КГД
- app.js проверен через `node --check`

index.html подключает app.js/styles.css с ?v=0.35.35

Миграций нет.
