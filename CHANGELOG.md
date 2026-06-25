# CHANGELOG

## v0.40.125 — Mobile manager payments modal hard fix

- Fixed mobile manager `Мои оплаты` modal header: the title stays in the top-left and no longer collapses vertically.
- Fixed the `Закрыть` button: it is compact and pinned to the top-right, overriding the base mobile `button { width: 100%; }` rule.
- Fixed payment groups/cards in `Мои оплаты`: all groups and request rows now use the full modal width instead of `fit-content`, so cards no longer have different widths.
- Updated cache-bust to `0.40.125`.
- Scope: mobile manager payments modal only. Backend, Telegram bot, admin and department-head cabinets were not changed.
