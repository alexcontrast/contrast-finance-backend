Contrast Finance v0.40.24 — changed files only

Base: v0.40.22

Changed files:
- app/web/app.js
- app/web/styles.css
- app/web/index.html
- app/core/config.py
- app/app/core/config.py
- app/telegram_bot/main.py
- app/README.md
- app/CHANGED_FILES_README.txt

Checks:
- python3 -m compileall -q app
- python3 -m py_compile app/telegram_bot/main.py
- node --check app/web/app.js

v0.40.24:
- Fixed admin/department-head event modal estimate table coloring.
- Removed stale nth-child based coloring that shifted after the Commission column was added.
- NDS is always blue, Deductions always purple, Commission and Method are neutral/gray.
