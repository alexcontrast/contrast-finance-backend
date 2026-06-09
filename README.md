Contrast Finance Backend v0.35.40 — changed files only

Фикс окна входа.

Причина:
- вкладка `Админ` была сделана на frontend как “только PIN”, но backend всё ещё искал пользователя по имени
- frontend пробовал имена Admin / Админ / admin, что не работает, если реальный админ в базе называется иначе
- обработчики входа также сделаны безопаснее, чтобы повторный показ окна входа не отваливал кнопку/Enter

Backend:
- AuthLoginRequest получил `auth_mode`
- `/auth/login` теперь понимает:
  - `auth_mode=manager`: обычный вход имя + PIN
  - `auth_mode=admin`: вход только по PIN среди активных пользователей role=admin
  - `auth_mode=department_head`: вход глав депа по имени + PIN среди role=department_head

Frontend:
- больше не гадает Admin / Админ / admin
- отправляет `auth_mode`
- обработчики кнопки входа, вкладок и Enter навешиваются безопасно
- вкладка Админ фокусирует PIN
- index.html cache-bust до ?v=0.35.40

Проверено:
- Python файлы компилируются
- app.js прошёл node --check

Миграций нет.
