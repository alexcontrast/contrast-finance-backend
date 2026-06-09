Contrast Finance Backend v0.35.38 — changed files only

Фикс сохранения новых строк сметы в черновиках.

Причина:
- backend route `event_items.py` ожидал `payload.external_amount`
- но схема `EventItemCreate` не содержит `external_amount`
- правильная логика: backend сам считает сумму позиции:
  external_amount = external_price × external_quantity × external_days
- из-за этого новые строки сметы не сохранялись в базе, после обновления страницы всё сбрасывалось
- КГД по новым строкам также ломался, потому что строка не получала нормальный database id / сумму

Исправлено:
- POST `/events/{event_id}/items` теперь сам считает external_amount
- PATCH `/event-items/{item_id}` тоже пересчитывает external_amount
- защита удаления позиции с активными оплатами сохранена
- index.html cache-bust до ?v=0.35.38

Проверено:
- Python файлы компилируются
- app.js прошёл node --check

Миграций нет.
