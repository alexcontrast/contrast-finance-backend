# v0.5.12 — Legacy import page route hotfix

Base: v0.5.11.

Fixed:
- Updated `/legacy-events-2026` server-rendered page version/title from old dry-run text to v0.5.12 import page.
- Changed visible copy to say real import creates editable draft events.
- Ensured changed-only package includes `app/api/routes/legacy_events_2026.py`, because v0.5.11 changed-only omitted the route file and could leave the migration page stuck at v0.5.9/v0.5.10 while the main app loaded v0.5.11.
- Updated web cache-bust to 0.5.12.

No business logic changes beyond existing v0.5.11 behavior: import creates draft events/items only, no payments/requests/Telegram.
