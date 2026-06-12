# Contrast Finance v0.40.8

Hotfix for Telegram card deletion after cancelled/rejected payment requests.

## Changes
- Telegram now deletes the exact clicked callback message as a fallback after admin rejection or manager cancellation.
- Cards generated from `Мои заявки` are now saved into `telegram_messages`, so later cancellation/rejection deletes every visible manager card, not only the original creation card.
- If Telegram says a message to delete is already gone, the message row is marked as deleted instead of failed.
- Terminal rules are unchanged: rejected/cancelled always delete admin/manager cards; paid + cash_received deletes admin/manager cards; new/to_pay + cash_received stays visible.

No database migrations.
