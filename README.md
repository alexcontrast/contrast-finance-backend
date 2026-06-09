Contrast Finance Backend v0.35.55 — changed files only

Фикс PIN и редактирования данных менеджера.

Точные причины:
1. Кнопка `Сменить PIN` во frontend вызывала `PATCH /auth/change-pin`,
   но такого endpoint в текущем backend не было.
   В auth.py были только:
   - POST /auth/login
   - GET /auth/me

2. Модель User уже содержит `name`, `phone`, `email`, `department_id`,
   но AuthUserRead не отдавал `email`, и не было endpoint для обновления своего профиля.

Исправлено:
- добавлен backend endpoint:
  - `PATCH /auth/change-pin`
- PIN проверяет старый PIN, новый PIN минимум 4 цифры, сохраняется как native pin_hash
- добавлен backend endpoint:
  - `PATCH /auth/me/profile`
- менеджер может обновить:
  - имя
  - телефон
  - email
  - отдел
- AuthUserRead теперь отдаёт email
- в кабинете менеджера добавлена кнопка `✎ Данные менеджера`
- кнопка открывает отдельную модалку профиля через eventModalBackdrop, не через plansModalBackdrop
- после сохранения обновляются userBadge/pageSubtitle и dashboard
- кнопка `Сменить PIN` теперь показывает loader и работает с новым endpoint
- app.js прошёл node --check
- Python-файлы компилируются

Миграций нет.
