Contrast Finance Backend v0.37.13 — changed files only

Точечный фикс модалки менеджера `Мои оплаты` после v0.37.12.

Проблема:
- модалка всё ещё могла открываться слишком широкой;
- внутри оставалась пустота по бокам;
- класс `manager-payments-modal` добавлялся через `plansModalBackdrop || eventModalBackdrop`, поэтому при наличии `plansModalBackdrop` класс мог попасть не на реальную модалку `Мои оплаты`.

Исправлено:
1. В `openManagerPaymentRequestsModal()` класс `manager-payments-modal` теперь добавляется именно на `eventModalBackdrop`.
2. С `plansModalBackdrop` этот класс снимается, чтобы не оставлять stale-состояние.
3. Ширина модалки `Мои оплаты` больше не фиксированная `860px`:
   - `width: fit-content`;
   - `max-width: calc(100vw - 32px)`;
   - содержимое центрируется и не растягивает окно.
4. Горизонтальные отступы модалки уменьшены до 18px, чтобы убрать лишнюю пустоту по бокам.

Миграций нет.
Backend-логика не менялась относительно v0.37.12.

Проверки:
- app.js прошёл node --check
- Python-файлы компилируются
