# Changelog

## v0.5.107 — e-Salyq parser actually wired

- Реально подключён runtime parser fix в `app/main.py`.
- Backend version поднята до `0.5.107`.
- Исправлен выбор даты чека из KGD: русские/казахские строки, ISO, Unix, Java/Jackson arrays/objects.
- Технические create/upload/response timestamps не считаются датой чека.
- Полная Unicode-обработка ФИО, включая казахские буквы.
- Резервный Tesseract worker теперь запускается с `kaz+rus+eng`, с fallback на `rus+eng`.
- Усилен поиск ИИН исполнителя; исключается БИН заказчика.
- Номер чека выбирается из `check/receipt number` или печатной строки `Чек №...`; `check_id`/`ip_reg_id` исключены.
- Обновлены browser cache-busters.
- БД/Alembic не менялись.
