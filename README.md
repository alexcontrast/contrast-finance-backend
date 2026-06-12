# Contrast Finance Backend v0.38.10

Changed files only.

Hotfix: корректная видимость мероприятий у главдепов после смены отдела менеджера.

- кабинет главдепа больше не считает `events.department_id` главным источником истины, если менеджер уже переведён в другой отдел;
- для обычного мероприятия отдел определяется по текущему отделу основного менеджера;
- для соавторского мероприятия отдел определяется по текущим `event_shares`;
- старый `event.department_id` используется только как fallback для orphan legacy events без менеджера;
- доступ к карточке, общий `/events` и `/payment-requests` приведены к той же логике.

No DB migrations.
Frontend layout changes are not included.
