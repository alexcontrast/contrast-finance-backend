# CHANGELOG

## v0.5.11 — Legacy import creates editable drafts

- Changed real legacy import for January–April 2026: imported events are now created as editable drafts.
- Event status is now `draft` instead of `accepted`.
- Money status is now `waiting_money` instead of `cash_received`.
- Target manager remains `Тест` by default.
- Import still creates only events and event_items.
- No payment requests, Telegram cards, payment queues or live payment workflow are created.
- Duplicate protection by `legacy_event_id` is preserved.
- Cache-bust updated to `0.5.11`.
