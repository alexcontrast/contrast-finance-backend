Contrast Finance Backend v0.35.42 — changed files only

Фикс окна входа после патча КГД.

Причина:
- в app.js после патча КГД появился лишний standalone `async` перед helper-функцией:
  async
  function syncDraftItemFromRowBeforeTax(...)
- браузер останавливал выполнение app.js до навешивания обработчиков входа
- поэтому не работали:
  - кнопка `Войти`
  - вкладки `Вход / Админ / Глав Деп`

Исправлено:
- удалён лишний standalone `async`
- `checkTaxForItem` оставлен как `async function`, потому что внутри используется await
- index.html cache-bust до ?v=0.35.42

Проверено:
- app.js прошёл node --check
- Python-файлы компилируются

Миграций нет.
