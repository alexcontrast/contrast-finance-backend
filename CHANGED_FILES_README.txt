Contrast Finance v0.40.83

Telegram quick expenses:
- Admins can add monthly expenses from Telegram with one message, e.g. "Кофе 54900".
- Access is checked by linked Telegram user in PostgreSQL: only active users with role=admin can create/delete expenses.
- Managers and department heads cannot create expenses through Telegram.
- Bot supports confirmation before saving and an undo/delete button after saving.
- Admin binding by phone + PIN is allowed, while manager payment-flow access still remains manager-only.
- Expense month uses Astana timezone (Asia/Almaty), current month by default.
- No KGD/cache/payment logic changed.
