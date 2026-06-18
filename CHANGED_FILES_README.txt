Contrast Finance 2.0 — v0.40.86

Hotfix после v0.40.85:
- точная причина падения dashboard: в app.js функция overviewEventsBadge начала вызывать pluralizeRu(), но helper не был объявлен; при рендере админки/главдепа возникал ReferenceError, из-за чего данные не показывались.
- добавлен helper pluralizeRu().
- восстановлен fallback учёта мероприятий без соавторства в личных строках менеджеров главдепа.
- версии cache-bust обновлены до v0.40.86.
