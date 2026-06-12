# Contrast Finance Backend v0.40.3

Changed files only.

Telegram bot hotfix for the new v0.40 site.

What changed:

- Telegram cards are no longer removed just because `money_status = cash_received`; payment status and money status are independent.
- Admin/manager Telegram cards are terminal only when the request is rejected/cancelled or when payment is `paid` and money is `cash_received`.
- The bot now mirrors the site payment-method lock logic:
  - if a position already has a fixed payment method, Telegram offers only that method;
  - invoice is fixed after BIN/IIN is checked and locked;
  - self-employed is fixed only after an active payment request exists, not after a draft item value alone;
  - the backend side of the bot also enforces the same fixed method.
- When a bot request is created as invoice or self-employed, the item gets the same tax/payment data that the site writes.
- Tatiana notifications remain implemented for invoice and self-employed but stay disabled while `TELEGRAM_TATYANA_ENABLED=false`.

No DB migrations.
