v0.40.89
- Fixed intermittent duplicate Telegram request cards by adding a per-request publish lock.
- The bot now marks a request as recently published at the start of publishing, not only after sending/saving all cards.
- Telegram message records are saved immediately after each sent card, so the background poller cannot see a just-sent card as missing.
- Added a second recently-published check inside poll_site_requests before publishing.
