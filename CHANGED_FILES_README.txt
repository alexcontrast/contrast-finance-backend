Contrast Finance Backend v0.40.9 — changed files only

Base: v0.40.8.

Reason:
After bot redeploy, the new Telegram worker could send existing active payment requests again if those requests did not have active `admin_payment_card` rows in `telegram_messages`.

Exact cause:
`poll_site_requests()` selected every active request without an active admin Telegram card. After a redeploy or after old test cards created before message persistence, those old requests looked like "not notified" and were republished.

Changed files:
- app/telegram_bot/main.py
  - BOT_VERSION -> CONTRAST_FINANCE_BOT_V0.40.9_NEW_SITE.
  - Added `BOT_STARTED_AT`.
  - Added env flag `TELEGRAM_PUBLISH_EXISTING_REQUESTS_ON_START` (default false).
  - `poll_site_requests()` now publishes only requests created after this bot worker started, unless the env flag is explicitly enabled.
  - Startup logs show bot start time and whether existing-request publication is enabled.
- app/core/config.py
- app/app/core/config.py
- README.md
- CHANGED_FILES_README.txt

Behavior:
- Redeploying the bot no longer spams old active requests.
- New requests created on the site while the bot is running are still sent to Telegram.
- Status synchronization for existing saved cards is unchanged.
- To intentionally backfill old requests once, set `TELEGRAM_PUBLISH_EXISTING_REQUESTS_ON_START=true`, redeploy, then set it back to false.

Checks passed:
- python3 -m py_compile app/telegram_bot/main.py
- python3 -m compileall -q app
