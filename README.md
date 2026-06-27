# Contrast Finance v0.5.29

Патч для диагностики первой долгой загрузки вкладки админки «Статистика».

После деплоя при открытии статистики в Railway logs должна появиться строка вида:

```text
PERF admin-year-statistics year=2026 months=12 events=... requests=... build_stats=... total=... timings=01:...,02:...
```

В браузерной консоли появится:

```text
PERF web admin-year-statistics year=2026 retried=false total=...s
```

Для деплоя достаточно changed-only.
