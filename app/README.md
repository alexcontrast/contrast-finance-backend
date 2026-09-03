Contrast Finance v0.5.118

Main deployment and verification instructions are in the root `README.md`.

v0.5.118:
- Kaspi: если чек содержит ИИН без ФИО, сначала используется локальная история Contrast Finance;
- если локального совпадения нет, выполняется best-effort поиск ФИО по ИИН на фиксированных публичных сервисах ba.prg.kz и pk.adata.kz;
- найденное ФИО сохраняется в строке и становится локальным источником для следующих чеков;
- казахские буквы сохраняются, результат можно вручную исправить перед Р-1;
- no database migration.
