## v0.40.34

- Скрыт блок «Оплачено / Остаток» в модалке мероприятия для роли главдепа.
- Блок оплат заказчика остаётся доступен только админу.

# Contrast Finance v0.40.10

## v0.40.33
- Compact event-modal payment request table/buttons so action buttons fit inside the modal.
- Added admin-only emergency event delete endpoint/button for test/broken events: cancels the event and all its payment requests even if money was marked cash received.


## v0.40.32

- Added admin emergency manual override for event item VAT and deductions in admin event edit mode.
- Intended only for legacy/migration corrections where invoice item tax fields were imported as zero but payment method/BIN are locked by active payment requests.
- Does not unlock payment method, BIN/IIN, paid amount, or deletion restrictions.


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


## v0.40.28
- Сортировка менеджеров в обзоре админки и главдепа по выполнению плана от большего к меньшему.
## v0.40.31
- Added admin customer prepayment box in event modal and admin edit summary: paid/remaining against event turnover.
- Added event.customer_paid_amount with Alembic migration 0009.
- Admin can add customer prepayments from the event modal; amounts are accumulated and capped at turnover.
- Event-level “Деньги в кассе” now fills customer paid amount to full turnover and remaining becomes 0.

## v0.40.29

- Admin overview now shows total monthly events as green badges for the whole company and separately for each department.
- Department-head overview now shows the department monthly event count as a badge near the department plan.
- Counts include all events returned for the selected month, including completed/archive events.