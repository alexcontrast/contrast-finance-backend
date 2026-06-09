Contrast Finance Backend v0.35.19 — changed files only

Реальная КГД-проверка без случайной заглушки.

Изменения:
- KGD_MODE по умолчанию теперь `live`, а не `stub`
- если переменная KGD_MODE вообще не задана, backend сразу ходит в реальный КГД
- заглушка остаётся только как явный dev-режим, если специально поставить:
  KGD_MODE=stub
- если KGD_API_KEY не задан, backend вернёт честный статус:
  `KGD_API_KEY is not configured`

Для Railway должны быть переменные:

KGD_MODE=live
KGD_API_KEY=<секретный ключ КГД>
KGD_BASE_URL=https://portal.kgd.gov.kz

Что проверить после деплоя:
1. Railway → Variables
2. Убедиться, что KGD_MODE=live
3. Убедиться, что KGD_API_KEY задан
4. Перезапустить deploy
5. Внутренняя смета → По счету → БИН/ИИН → галочка КГД

index.html подключает app.js/styles.css с ?v=0.35.19

Миграций нет.
