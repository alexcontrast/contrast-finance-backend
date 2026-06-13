# Contrast Finance v0.40.10

Хотфикс статуса денег: индивидуальное «Деньги в кассе» по заявке больше не поднимает статус денег на всё мероприятие и не трогает соседние заявки. Массовое направление сохраняется только сверху вниз: кнопка «Деньги в кассе» на мероприятии помечает все его активные заявки.

Новых миграций нет.


## v0.40.13
- Legacy migration status mapping updated: legacy `Новая` and `На оплату` both import as `new`; legacy `Отклонено` and `Отменено` both import as `cancelled`. Dry-run status preview now reflects this merged mapping before production import.

## v0.40.12
- Added one-time legacy migration importer for Apps Script / Google Sheets export JSON.
- Added legacy identifiers for idempotent event/item/payment imports.
- Added /legacy-migration upload page protected by LEGACY_MIGRATION_TOKEN.


v0.40.12: Legacy migration dry-run now uses fast JSON validation without touching PostgreSQL; migration page handles non-JSON upstream errors clearly.


## v0.40.18

- Admin event modal: added pencil edit mode for admin to edit event fields and estimates without changing manager restrictions.
- Admin event modal: accepted events can be returned to revision / rework.

## v0.40.17
- Improved legacy migration page file handling for Safari/browser cache: explicit selected-file indicator, button event listeners, and clearer messages when the JSON file is not selected/read.


v0.40.17: added no-JavaScript fallback multipart validation/import page for legacy migration; background import job with status page; added python-multipart.


## v0.40.27
- Сортировка менеджеров в обзоре админки и главдепа по выполнению плана от большего к меньшему.
