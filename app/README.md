# Contrast Finance v0.40.10

Хотфикс статуса денег: индивидуальное «Деньги в кассе» по заявке больше не поднимает статус денег на всё мероприятие и не трогает соседние заявки. Массовое направление сохраняется только сверху вниз: кнопка «Деньги в кассе» на мероприятии помечает все его активные заявки.

Новых миграций нет.


## v0.40.12
- Added one-time legacy migration importer for Apps Script / Google Sheets export JSON.
- Added legacy identifiers for idempotent event/item/payment imports.
- Added /legacy-migration upload page protected by LEGACY_MIGRATION_TOKEN.


v0.40.12: Legacy migration dry-run now uses fast JSON validation without touching PostgreSQL; migration page handles non-JSON upstream errors clearly.
