Contrast Finance Backend v0.38.9 — changed files only

Purpose:
- Закрыть баг авторизации: глава отдела мог войти через вкладку «Вход», хотя эта вкладка должна быть только для менеджеров.

Changed:
- app/api/routes/auth.py
  * /auth/login теперь проверяет соответствие auth_mode и user.role:
    - manager -> role manager
    - admin -> role admin
    - department_head -> role department_head
  * неизвестный auth_mode отклоняется.
- app/core/config.py
- app/app/core/config.py
- README.md / CHANGED_FILES_README.txt

No DB migrations.
No frontend behavior changes.
