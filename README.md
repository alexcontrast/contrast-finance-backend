# Contrast Finance 2.0 Backend

Первый минимальный backend для Contrast Finance 2.0.

## Что уже есть

- FastAPI-приложение
- `/` — корневой endpoint
- `/health` — проверка, что сервер жив
- `/docs` — автоматическая документация API
- готовность к деплою на Railway

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Открыть:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## Railway

В Railway нужно подключить GitHub repo и убедиться, что есть переменная:

```text
DATABASE_URL
```

Если PostgreSQL создан внутри того же Railway project, Railway обычно сам даёт переменные подключения.

## Проверка после деплоя

Открыть публичный Railway URL:

```text
https://...railway.app/health
```

Ожидаемый ответ:

```json
{
  "ok": true,
  "service": "contrast-finance-api",
  "version": "0.1.0",
  "environment": "dev",
  "database_configured": true
}
```

Если `database_configured` = `false`, значит backend пока не видит `DATABASE_URL`.
