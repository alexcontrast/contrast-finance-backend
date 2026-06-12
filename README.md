# Contrast Finance Backend v0.40.5

Telegram bot hotfix: cancelled/rejected payment requests are now always terminal for admin/manager Telegram cards, even if the request already had money_status=cash_received. New/to_pay + cash_received still stays visible because payment status and money status are separate.

Changed files only.

Telegram bot hotfix for the new v0.40 site.

What changed:

- The Telegram payment flow no longer shows old legacy/test event months such as June 2022 by default.
- The bot now filters manager events by `event_date >= January 1` of `TELEGRAM_MIN_EVENT_YEAR`.
- `TELEGRAM_MIN_EVENT_YEAR` defaults to the current calendar year.
- For temporary import/testing cases, the year can be overridden in Railway:
  - `TELEGRAM_MIN_EVENT_YEAR=2025`
  - or another required year.

This keeps current-year events visible and prevents old imported duplicates from appearing in the bot month picker.

No DB migrations.
