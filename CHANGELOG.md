# v0.40.109 — reset old dashboard on role switch

- Исправлен визуальный flash старого кабинета после выхода и входа в другую роль.
- При logout/login теперь очищается видимая разметка кабинета: summary, tabs, dashboard content, модалки и role-specific state.
- Старые незавершённые dashboard-запросы больше не могут дорисовать предыдущий кабинет после смены пользователя/роли: увеличивается `dashboardRequestSeq`.
- Глобальный GET in-flight cache теперь учитывает текущий auth token, поэтому `/app/bootstrap` не переиспользует ответ старого пользователя.
- Dashboard in-flight key теперь включает роль, user id, department id и месяц.
- Backend и Apps Script не менялись.
