# v0.5.1 — Admin plans and closing diagnostics

База: стабильная версия Contrast Finance 2.0 / 0.5.

Диагностический патч без изменения бизнес-логики.

Что добавлено:
- Browser console PERF-логи для вкладок админки `Задать планы` и `Закрыть месяц`.
- Browser console PERF-логи для этапов render/attach, загрузки планов, загрузки расходов, расчёта закрытия месяца.
- Backend PERF-логи для `/monthly-plans`, `/monthly-expenses`, `/monthly-closings/calculate`.
- Cache-bust фронта обновлён до `0.5.1`.

Что не менялось:
- расчёты;
- интерфейс;
- Telegram-бот;
- мобильные кабинеты;
- Google Sheets export.
