# Contrast Finance Backend v0.24

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

v0.24:

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


## v0.24

Исправлено короткое имя Alembic revision: `0002_payments_tax_audit`, чтобы помещалось в `alembic_version.version_num`.


## v0.24

Добавлены таблицы:

- monthly_plans
- monthly_expenses
- monthly_closings
- exports
- telegram_messages

После деплоя `/db/tables` должен показать полный базовый набор таблиц.


## v0.24

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


## v0.24

Исправлена неоднозначная связь `users -> payment_requests`.
База не меняется, новых миграций нет.


## v0.24

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


## v0.24

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


## v0.24

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


## v0.24

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


## v0.24

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


## v0.24

Исправлена ошибка ответа `PaymentRequestRead`: поле `tax_status_label` теперь необязательное.
База не меняется, миграций нет.


## v0.24

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


## v0.24

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


## v0.24

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


## v0.24

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


## v0.24

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


## v0.24

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


## v0.24

Добавлен общий админский dashboard:

```text
GET /admin-dashboard?month=2026-06&include_drafts=true
```

Показывает:

- план компании
- факт компании
- процент выполнения
- расходы компании
- личный план менеджера
- отделы
- мероприятия
- последние заявки на оплату
- закрытие месяца
- учредительский расчёт

Это видит только админский кабинет. Руководитель отдела получает урезанный dashboard через `/department-head-dashboard`.


## v0.24

Подготовка к реальному КГД:

```text
KGD_MODE=stub/live
KGD_API_KEY хранится только в Railway Variables
KGD_BASE_URL хранится только в Railway Variables
services/kgd/client.py
GET /kgd/status
```

Важно:

- по умолчанию работает `KGD_MODE=stub`
- ключ КГД не хранится в GitHub
- `/kgd/status` показывает только факт настройки ключа, но не сам ключ
- `tax/check` теперь вызывает KGD service
- `live` режим подготовлен безопасно, но реальный endpoint mapping нужно добавить после подтверждения формата API КГД


## v0.24

Подключён реальный KGD live-клиент по схеме из Apps Script:

```text
KGD_MODE=live
KGD_API_KEY=<токен КГД>
KGD_BASE_URL=https://portal.kgd.gov.kz
```

Запросы:

```text
GET /services/isnaportalsync/public/snr-search/search?uin=<BIN/IIN>
GET /services/isnaportalsync/public/search-payer-data?taxpayerCode=<BIN/IIN>
Header: X-Portal-Token
```

Логика:

```text
ОУР + Плательщик НДС -> our_vat
ОУР + Без НДС / Снят с НДС -> our_no_vat
Упрощенка -> simplified
Другой СНР -> snr
Не найдено / ошибка -> not_found
```

Ключ КГД по-прежнему хранится только в Railway Variables.


## v0.24

Hotfix: исправлен `IndentationError` в `app/api/routes/tax.py`.

База не менялась, миграций нет.


## v0.24

Hotfix: исправлен расчёт НДС подрядчика для `our_vat`.

Было ошибочно:

```text
amount / 1.12
```

Стало правильно:

```text
amount / 1.16
НДС = amount - amount_without_vat
Вычеты = amount_without_vat * 10%
```

Для суммы 500 000:

```text
НДС = 68 965.52
Вычеты = 43 103.45
```

База не менялась, миграций нет.


## v0.24

Налоговые ставки вынесены в config/Railway Variables:

```text
VAT_RATE=0.16
CONTRACTOR_DEDUCTION_RATE=0.10
CONTRAST_INTERNAL_TAX_RATE=0.12
SIMPLIFIED_TAX_RATE=0.05
```

Добавлено:

```text
GET /settings/economics
```

База не менялась, миграций нет.


## v0.24

Добавлена авторизация и совместимость со старым Apps Script PIN.

Новые поля `users`:

```text
phone
legacy_user_id
legacy_pin_hash
auth_source
pin_hash
```

Новые endpoints:

```text
POST /auth/login
GET  /auth/me
POST /users/import-legacy
```

Логика legacy PIN:

```text
SHA256("<legacy_user_id>:<pin>")
```

Это повторяет Apps Script `hashPin_(pin, userId)`, поэтому менеджеры смогут входить тем же именем и PIN после импорта пользователей.

Новая зависимость:

```text
PyJWT==2.10.1
```


## v0.24

Hotfix Alembic: исправлен `down_revision` у миграции авторизации.

Было:

```text
down_revision = "0003"
```

Стало:

```text
down_revision = "0003_monthly_ops"
```

Логика авторизации не менялась.


## v0.24

Hotfix Alembic: миграция `0006_add_user_auth_fields` больше не использует `try/except` вокруг `create_index`.

Причина: в PostgreSQL ошибка внутри транзакции переводит всю транзакцию в aborted state, даже если Python её поймал.
Теперь миграция заранее проверяет наличие индекса через inspector.

Логика авторизации не менялась.


## v0.24

Hotfix SQLAlchemy mapper: возвращены relationship-связи в `User`.

Причина 500 на `/users/import-legacy`:
модель `Event` ожидает `User.events`, а в v0.21 эта связь была случайно удалена при добавлении auth-полей.

Миграций нет, база не менялась.


## v0.24

Hotfix SQLAlchemy mapper: точное имя relationship для PaymentRequest.

`PaymentRequest.created_by_user` ожидает:

```text
User.payment_requests_created
```

Миграций нет, база не менялась.


## v0.24

Добавлено управление пользователями для новой системы:

```text
GET   /users
POST  /users/native
PATCH /users/{user_id}/role
PATCH /users/{user_id}/pin
```

Зачем:

- создать Санжара и Рауфаля как `department_head`
- создать нативного админа
- поменять роль/отдел пользователю
- поменять PIN нативному пользователю

Миграций нет, база не менялась.


## v0.24

`POST /users/native` теперь умеет переиспользовать неактивного пользователя с тем же именем/телефоном.

Пример:
импортированный неактивный `Рауфаль` превращается в native-аккаунт:

```text
name = Рауфаль
role = department_head
department_id = 2
auth_source = native
legacy_user_id = null
legacy_pin_hash = null
```

Миграций нет, база не менялась.


## v0.24

Hotfix `GET /users`: модель `User` возвращена к старой структуре v0.20, auth-поля добавлены поверх неё.

Причина:
в v0.21 модель была переписана слишком грубо, из-за этого могли ломаться SQLAlchemy mapper relationships.

Миграций нет, база не менялась.


## v0.24

Исправлена и явно включена защита по ролям.

Проверка:

```text
GET /security/whoami
GET /security/admin-only
```

Ожидаем:

- без токена `/users` -> 401
- токен manager на `/users` -> 403
- токен department_head на свой `/department-head-dashboard` -> 200
- токен department_head на чужой department_id -> 403
- токен admin на `/admin-dashboard` и `/users` -> 200

Миграций нет, база не менялась.


## v0.24

Hotfix security: удалён конфликтующий старый `users_router`.

Причина:
в проекте были две ручки `GET /users`:

```text
app/api/routes/users.py          открытая старая
app/api/routes/users_manage.py   защищённая новая
```

FastAPI ловил старую открытую ручку первой, поэтому `/users` открывался без токена.

Исправлено:

```text
main.py больше не подключает старый users_router
старый routes/users.py перенесён на prefix /users-legacy и тоже закрыт admin-only
```

Миграций нет, база не менялась.


## v0.24

Добавлен слой прав для менеджеров и руководителей на основные event endpoints.

Правила:

```text
admin:
  всё

manager:
  видит только свои мероприятия
  создаёт мероприятия только на себя
  редактирует только свои мероприятия
  редактирует позиции только своих мероприятий
  проверяет BIN только по своим позициям

department_head:
  read-only
  видит мероприятия только своего отдела
  не создаёт/не редактирует
```

Защищены:

```text
/events
/events/{event_id}
/events/{event_id}/items
/event-items/{item_id}
/events/{event_id}/summary
/events/{event_id}/coordinator
/event-items/{item_id}/tax/check
/event-items/{item_id}/tax/manual
```

Миграций нет, база не менялась.

Payment requests будут закрыты следующим шагом v0.24.1, чтобы не сломать рабочую очередь.
