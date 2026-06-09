Contrast Finance Backend v0.35.41 — changed files only

Аварийный фикс запуска после v0.35.40.

Причина падения:
- в v0.35.40 был заменён `app/schemas/auth.py`
- из него пропал класс `AuthPermissionsRead`
- `app/schemas/app_bootstrap.py` импортирует `AuthPermissionsRead`
- из-за этого backend падал при старте:
  ImportError: cannot import name 'AuthPermissionsRead'

Исправлено:
- возвращён `AuthPermissionsRead`
- сохранён `auth_mode` в `AuthLoginRequest`
- `AuthUserRead` снова совместим с bootstrap-схемами
- auth route дополнен `permissions_for_user(user)`
- index.html cache-bust до ?v=0.35.41

Проверено:
- Python-файлы компилируются
- app.js прошёл node --check

Миграций нет.
