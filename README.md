# Contrast Finance v0.5.30

Патч ускоряет первую загрузку годовой статистики в админской вкладке `Статистика`.

## Деплой

Достаточно `changed-only`: удалять файлы не нужно.

## Проверка

После открытия вкладки `Статистика` в Railway logs должна появиться строка:

```text
PERF admin-year-statistics-fast year=2026 months=12 events=... requests=0 load_sections=... build_stats=... total=... sources=... months_timing=...
```

Ожидаемо `total` должен стать намного меньше прежних ~19 секунд.
