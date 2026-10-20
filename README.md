# Contrast Finance 2.0 — 0.6.8

Исправление сметы менеджера, безопасности, расчётов и сохранения АВР поверх точной версии 0.6.5.

Инструкция установки, результаты проверок, соответствие технической ревизии и ограничения: [Contrast-Finance-RELEASE.md](Contrast-Finance-RELEASE.md).

## Запуск

Python 3.12, PostgreSQL, зависимости из `requirements.txt` с `requirements.lock.txt`. `DATABASE_URL` указывает на базу Finance. В production обязателен приватный `JWT_SECRET_KEY` не короче 32 символов. Не публикуйте его в репозитории.

```sh
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

Бот — отдельный процесс того же исходного кода:

```sh
python -m app.telegram_bot.main
```

На Railway используйте существующий `scripts/start.sh` для сайта. Он применяет миграции и убирает только известный устаревший дубликат миграции, как прежние стабильные сборки. Для обновления бота используйте ту же версию исходников и ту же базу; миграции должны завершиться до старта новой версии бота.

## Проверки

```sh
pip install -r tests/requirements.txt
python -m pytest tests -q
node tests/test_manager_editor.cjs .
node tests/test_accounting_date_parser_v0109.js
npm ci --prefix tests/web
node tests/web/manager-dom.cjs .
```

Для PostgreSQL выделен `scripts/verify_postgres.py`; точный порядок запуска и защита от подключения к рабочей базе описаны в release-документе. Внешние SIGEX, KGD, Telegram и Google в регрессиях подменены.

Исторические миграции остаются обязательной частью сборки. Неподключённые старые обработчики архивированы в `archive/legacy`; прежний README сохранён там же. Contrast Base разворачивается отдельно.
