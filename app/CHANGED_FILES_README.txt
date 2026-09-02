Contrast Finance v0.5.115

Changed files:
- app/api/routes/act_signing.py
- app/web/sign_avr.html
- app/web/index.html
- app/core/config.py
- README.md
- CHANGELOG.md
- VERIFY_INSTALL.txt

Behavior:
- iPhone primary launch uses a local Contrast recovery page with Apple Smart App Banner.
- Smart App Banner targets current eGov Mobile App Store id 1476128386 and receives the exact active SIGEX eGovMobileLaunchLink as app-argument.
- Official SIGEX HTTPS deeplink remains available as a secondary fallback; same-session QR remains available.
- No mobileSign: URL is exposed to Safari and the one-time SIGEX session is never recreated merely because iOS failed to open the app.

No database migration. Alembic head remains 0021_avr_signed_ddc.
