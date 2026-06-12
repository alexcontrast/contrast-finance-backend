# Contrast Finance Backend v0.38.10

Changed files only.

Hotfix: корректная видимость мероприятий у главдепов после смены отдела менеджера.

- кабинет главдепа больше не считает `events.department_id` главным источником истины, если менеджер уже переведён в другой отдел;
- для обычного мероприятия отдел определяется по текущему отделу основного менеджера;
- для соавторского мероприятия отдел определяется по текущим `event_shares`;
- старый `event.department_id` используется только как fallback для orphan legacy events без менеджера;
- доступ к карточке, общий `/events` и `/payment-requests` приведены к той же логике.

No DB migrations.
Frontend layout changes are not included.

## v0.40.1 Telegram bot worker

Run the new Telegram bot as a separate Railway worker/process:

```bash
python -m app.telegram_bot.main
```

Required env for the test bot:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...
TELEGRAM_TATYANA_CHAT_ID=1896781134
TELEGRAM_TATYANA_ENABLED=false
```

Tatiana notifications are implemented for `invoice` and `self_employed`, but disabled by default to avoid test spam.
