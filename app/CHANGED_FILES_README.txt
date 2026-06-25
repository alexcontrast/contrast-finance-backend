v0.5.7 — Legacy events 2026 dry-run

Изменённые/добавленные файлы:
- requirements.txt
- app/main.py
- app/api/routes/legacy_events_2026.py
- app/services/legacy_events_2026_importer.py
- app/web/index.html
- app/web/app.js
- CHANGELOG.md
- README.md
- app/CHANGED_FILES_README.txt

Назначение:
- Добавлена отдельная страница /legacy-events-2026 и dry-run endpoint для проверки импорта исторических мероприятий из старого XLSX за Январь-Апрель 2026.
- База в dry-run не меняется.
- Оплаты/заявки/Telegram не импортируются.
