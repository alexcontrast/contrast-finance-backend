v0.5.5 — Admin diagnostics cleanup

Изменённые файлы:
- app/web/app.js
- app/web/index.html
- app/api/routes/monthly_expenses.py
- app/api/routes/monthly.py
- app/api/routes/monthly_closings.py
- CHANGELOG.md
- README.md
- app/CHANGED_FILES_README.txt

Смысл патча:
- убрать временные диагностические PERF-логи после успешной оптимизации;
- сохранить ускорения v0.5.3/v0.5.4;
- обновить cache-bust до 0.5.5.
