# Contrast Finance Backend v0.16

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

v0.16:

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


## v0.16

Исправлено короткое имя Alembic revision: `0002_payments_tax_audit`, чтобы помещалось в `alembic_version.version_num`.


## v0.16

Добавлены таблицы:

- monthly_plans
- monthly_expenses
- monthly_closings
- exports
- telegram_messages

После деплоя `/db/tables` должен показать полный базовый набор таблиц.


## v0.16

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


## v0.16

Исправлена неоднозначная связь `users -> payment_requests`.
База не меняется, новых миграций нет.


## v0.16

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


## v0.16

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


## v0.16

Добавлены правила валидации по способам оплаты:

```text
invoice / По счету:
- BIN / ИИН обязателен на позиции

card / На карту:
- номер карты обязателен
- проверка на 16 цифр

self_employed / Самозанятый:
- фамилия обязательна в комментарии

cash / Налик:
- без дополнительных обязательных полей
```

Способы оплаты можно передавать как:

```text
invoice
card
cash
self_employed
```

Также принимаются русские алиасы:

```text
По счету
На карту
Налик
Самозанятый
```

Новых миграций нет, база не меняется.


## v0.16

Добавлена тестовая налоговая механика без реального КГД:

```text
POST  /event-items/{item_id}/tax/check
PATCH /event-items/{item_id}/tax/manual
```

Тестовая логика `tax/check`:

```text
BIN заканчивается на 1 -> our_vat / ОУР с НДС
BIN заканчивается на 2 -> our_no_vat / ОУР без НДС
BIN заканчивается на 3 -> simplified / Упрощенка
другое -> not_found, BIN не фиксируется, НДС 0, Вычеты 0
```

Ручная правка админом:

```text
PATCH /event-items/{item_id}/tax/manual?admin_user_id=1
```

Body:

```json
{
  "tax_status": "our_vat"
}
```

Варианты tax_status:

```text
our_vat
our_no_vat
simplified
self_employed
not_found
```

Новых миграций нет, база не меняется.


## v0.16

Усилена логика заявок "По счету":

```text
invoice / По счету:
- BIN / ИИН обязателен
- BIN / ИИН должен быть проверен и зафиксирован
- налоговый статус должен быть подтверждён
- not_found не проходит
```

Добавлены:

```text
GET /payment-requests/{request_id}
GET /payment-requests/{request_id}/card
```

`/card` отдаёт лаконичную карточку заявки:

- Позиция
- Сумма по смете
- Факт
- Остаток
- Сумма заявки
- Способ оплаты
- BIN / ИИН
- налоговый статус типа "ОУР с НДС"
- без сумм НДС и Вычетов


## v0.16

Исправлена ошибка ответа `PaymentRequestRead`: поле `tax_status_label` теперь необязательное.
База не меняется, миграций нет.


## v0.16

Добавлена сводка мероприятия:

```text
GET /events/{event_id}/summary
```

Считает:

- внешнюю смету
- факт
- оплачено
- НДС
- вычеты
- внутренний налог
- банковские/налоговые платежи для Упрощенки
- базу ЗП менеджера
- ЗП менеджера
- координатора
- итоговый доход компании

Координатор:
- 50% от суммы по смете = факт координатора
- 50% = доля компании
- доля компании добавляется после ЗП менеджера


## v0.16

Добавлен быстрый endpoint для теста координатора:

```text
POST /events/{event_id}/coordinator
```

Body:

```json
{
  "external_name": "Координатор",
  "external_amount": "200000.00",
  "external_note": "Координатор проекта",
  "sort_order": 999
}
```

Правило:

```text
50% от суммы по смете = факт координатора
50% от суммы по смете = доля компании
Координатор не участвует в ЗП менеджера
Доля компании от координатора добавляется в final_company_income после ЗП менеджера
```


## v0.16

Добавлены планы месяца и первый дашборд:

```text
POST /monthly-plans
GET  /monthly-plans
GET  /monthly-dashboard?month=2026-06&include_drafts=true
```

Логика:

- админ задаёт план компании
- Санжар по умолчанию 66.67%
- Рауфаль по умолчанию 33.33%
- личный план менеджера по умолчанию 12.5% от плана компании
- факт отдела считается по final_company_income мероприятий
- отменённые мероприятия не входят
- черновики можно исключить через include_drafts=false
- расходы отдела показываются, если они уже внесены в monthly_expenses


## v0.16

Добавлены расходы месяца:

```text
POST /monthly-expenses
GET  /monthly-expenses
GET  /monthly-expenses/summary
```

Типы распределения:

```text
default_split — 2/3 Санжар, 1/3 Рауфаль
sanzhar_only — 100% Санжар
raufal_only — 100% Рауфаль
custom — вручную, сумма Санжар + Рауфаль должна равняться общей сумме
```

Месячный дашборд `/monthly-dashboard` уже подтягивает эти расходы.


## v0.16

Добавлено закрытие месяца:

```text
GET  /monthly-closings/calculate?month=2026-06
POST /monthly-closings/close?month=2026-06&closed_by_user_id=1
GET  /monthly-closings
GET  /monthly-closings/by-month?month=2026-06
```

Логика:

```text
Доход отдела = сумма final_company_income мероприятий отдела
Расходы отдела = monthly_expenses по распределению
База руководителя = доход отдела - расходы отдела
Руководитель = 10%, либо 15% если отдел выполнил план
Остаток отдела = доход - расходы - ЗП руководителя
Учредители = остатки двух отделов / 3
```

`calculate` только считает.
`close` сохраняет snapshot в `monthly_closings`.


## v0.16

Добавлен API кабинета руководителя отдела:

```text
GET /department-head-dashboard?department_id=1&month=2026-06&include_drafts=true
```

Показывает только один отдел:

- план отдела
- факт отдела
- процент выполнения
- остаток до плана
- расходы отдела
- менеджеров отдела
- мероприятия отдела
- закрытие месяца по отделу, если есть

Не показывает:

- деньги учредителей
- расчёт другого отдела
- общую собственническую часть
