# CHANGELOG

## v0.40.117 — Mobile manager event card readable layout

- Mobile manager only: increased event card text readability after the previous ultra-compact pass.
- Rebuilt manager event card action buttons into two rows:
  - row 1: `Оплатить` / `Мои оплаты` / `Удалить`;
  - row 2: `Передать` / `Соавтор` or `Удалить соавтора`.
- Fixed the mobile event `Дата` field so it stays inside the card width.
- Compressed the internal summary boxes below the estimate table to the height of their text.
- Bumped frontend cache-bust to `0.40.117`.

No backend, admin, department-head or Telegram bot logic was changed.
