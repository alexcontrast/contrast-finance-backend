# Contrast Finance 2.0 — v0.40.125

Patch: Mobile manager payments modal hard fix.

Changed files:
- `app/web/app.js`
- `app/web/styles.css`
- `app/web/index.html`
- `CHANGELOG.md`
- `README.md`
- `app/CHANGED_FILES_README.txt`

Notes:
- The previous v0.40.124 rules did not win against old modal/card sizing and the global mobile `button { width: 100%; }` rule.
- v0.40.125 adds a later injected override so the modal header and payment cards are forced into the intended mobile layout.
