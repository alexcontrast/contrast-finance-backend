Contrast Finance v0.40.84

Telegram quick expense admin access fix:
- Quick expenses no longer require admin binding by phone.
- Admin access is allowed if Telegram user id is listed in Railway secrets/env: TELEGRAM_ADMIN_USER_IDS / TELEGRAM_ADMIN_IDS / ADMIN_TELEGRAM_IDS, or positive TELEGRAM_ADMIN_CHAT_ID.
- If env Telegram id matches, the bot uses the first active admin user from PostgreSQL as created_by_user_id.
- Existing linked admin via users.telegram_id still works.
- Managers and department heads are still blocked from quick expenses.
- No site/KGD/payment logic changed.
