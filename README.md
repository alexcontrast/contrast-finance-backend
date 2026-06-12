# Contrast Finance Backend v0.40.6

Telegram bot/payment request hotfix for the stable v0.40 site.

## Changes

- Telegram self-employed requests no longer fail with a generic create error when surname is missing: the bot asks for the surname and continues the same request.
- If a self-employed surname is already saved on the site or from a previous Telegram request, Telegram uses it automatically.
- Invoice Telegram cards now show the contractor legal name from KGD as `Подрядчик`.
- Extra positions created from Telegram are fact-only expenses: `Сумма по смете = 0`, `Факт = сумма заявки`.
- Manager payment modal no longer saves the whole event before creating a payment request, so extra-position payment requests can be created for events on review/accepted as fact-only expenses.
- Site payment request snapshots for invoice requests now store the KGD legal name when available.

No migrations.
