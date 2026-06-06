# Contrast Finance Backend v0.7

Backend Contrast Finance 2.0 с PostgreSQL, миграциями и первым слоем таблиц для мероприятий, оплат, КГД и истории.

## Что внутри

- FastAPI
- SQLAlchemy
- Alembic migrations
- PostgreSQL
- `/health`
- `/db/health`
- `/db/tables`

## Уже создано

v0.2:

- departments
- users
- events
- event_items

v0.7:

- contractors
- taxpayer_checks
- payment_requests
- event_shares
- audit_log

## Railway

Start command в `railway.json`:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

При каждом деплое Railway сначала применит миграции, потом запустит backend.

## Проверка

После деплоя:

```text
/health
/db/health
/db/tables
```

`/db/tables` должен показать:

```text
alembic_version
audit_log
contractors
departments
event_items
event_shares
events
payment_requests
taxpayer_checks
users
```

## Важно

Для Railway backend-сервиса лучше использовать публичный PostgreSQL URL, если `.railway.internal` не резолвится при миграциях.


## v0.7

Исправлено короткое имя Alembic revision: `0002_payments_tax_audit`, чтобы помещалось в `alembic_version.version_num`.


## v0.7

Добавлены таблицы:

- monthly_plans
- monthly_expenses
- monthly_closings
- exports
- telegram_messages

После деплоя `/db/tables` должен показать полный базовый набор таблиц.


## v0.7

Добавлены первые API:

```text
GET  /departments
POST /departments
POST /departments/seed

GET  /users
POST /users

GET  /events
POST /events
```

Проверять удобно через:

```text
/docs
```

Порядок теста:

1. `POST /departments/seed`
2. `GET /departments`
3. `POST /users`
4. `GET /users`
5. `POST /events`
6. `GET /events`


## v0.7

Исправлена неоднозначная связь `users -> payment_requests`.
База не меняется, новых миграций нет.


## v0.7

Добавлены API позиций сметы:

```text
GET   /events/{event_id}/items
POST  /events/{event_id}/items
PATCH /event-items/{item_id}
```

Внешняя смета:

- external_name
- external_price
- external_quantity
- external_days
- external_amount
- external_note

Внутренняя смета:

- amount_fact
- paid_amount
- payment_method
- iin_bin
- iin_bin_locked
- tax_check_status
- vat_amount
- deduction_amount
- internal_note

Пока без КГД-интеграции. Только хранение и обновление позиций.


## v0.7

Добавлены заявки на оплату:

```text
GET   /payment-requests
GET   /events/{event_id}/payment-requests
POST  /event-items/{item_id}/payment-requests?created_by_user_id=1
PATCH /payment-requests/{request_id}/status
```

Что делает создание заявки:

- берёт позицию
- сохраняет snapshot:
  - позиция
  - сумма по смете
  - факт
  - оплачено
  - остаток
- сохраняет сумму заявки
- ставит warning_over_remaining=true, если сумма заявки больше остатка

При смене статуса на `paid` система увеличивает `paid_amount` у позиции.
