# Contrast Finance v0.40.9

Hotfix for Telegram bot redeploy behavior.

## Changes
- Telegram bot no longer republishes old active payment requests after Railway redeploy just because their Telegram message rows are missing.
- By default `poll_site_requests` publishes only payment requests created after the current bot worker started.
- Existing cards still sync normally: status changes update/delete saved manager/admin cards, and Tatiana cards update when enabled.
- Added optional env override `TELEGRAM_PUBLISH_EXISTING_REQUESTS_ON_START=true` for one-time recovery/backfill if old cards must be republished manually.
- Bot startup logs now include start timestamp and the backfill flag.

No database migrations.
