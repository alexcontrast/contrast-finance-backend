Contrast Finance Backend v0.38.10 — changed files only

Purpose:
- Исправить баг: после смены отдела менеджера его мероприятие могло оставаться видимым у старого главдепа и одновременно появляться у нового.

Changed:
- app/api/routes/department_head_dashboard.py
  * event_visible_for_department() теперь ориентируется на текущий отдел менеджера/доли, а не на stale event.department_id.
- app/services/authorization.py
  * can_view_event() для department_head использует текущий отдел менеджера или shares; event.department_id только fallback для legacy orphan events.
- app/api/routes/events.py
  * список событий department_head фильтруется по текущему отделу менеджера/долям.
- app/api/routes/payment_requests.py
  * список заявок department_head использует ту же область видимости.
- app/web/index.html
  * cache-bust v0.38.10.
- app/core/config.py / app/app/core/config.py
  * VERSION = 0.38.10.
- README.md / CHANGED_FILES_README.txt

No DB migrations.
