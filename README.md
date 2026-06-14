## v0.40.36

Telegram bot card and amount prompt refinement.

Changes:
- In Telegram payment cards, `Подрядчик` is shown only for `По счету` and `Самозанятый` requests.
  - `По счету`: legal entity name from KGD/contractor snapshot.
  - `Самозанятый`: surname from the self-employed flow/snapshot.
  - `На карту` and `Нал`: contractor line is hidden.
- Telegram payment cards now show:
  - `Сумма заявки`
  - `Цена по смете`
  - `Факт`
  - `Оплачено`
  - `Остаток`
- During bot request creation, the amount-entry step now shows the selected position financial context:
  - `Факт`
  - `Оплачено`
  - `Остаток`

Checks:
- `python3 -m compileall -q app`
- `python3 -m py_compile app/telegram_bot/main.py`
- `node --check app/web/app.js`
