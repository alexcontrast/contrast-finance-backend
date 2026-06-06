# Contrast Finance Backend v0.2

Минимальный backend Contrast Finance 2.0 с подключением к PostgreSQL и первыми таблицами.

## Что внутри

- FastAPI
- SQLAlchemy
- Alembic migrations
- PostgreSQL
- `/health`
- `/db/health`
- `/db/tables`

## Таблицы в первой миграции

- departments
- users
- events
- event_items

## Railway

Start command уже указан в `railway.json`:

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

Ожидаемо:

```json
{
  "ok": true,
  "database_connected": true
}
```

`/db/tables` должен показать:

```text
departments
users
events
event_items
alembic_version
```

## Важно

Секреты не хранить в GitHub.

В Railway Variables должны быть:

```text
DATABASE_URL
JWT_SECRET_KEY
ENVIRONMENT
```
