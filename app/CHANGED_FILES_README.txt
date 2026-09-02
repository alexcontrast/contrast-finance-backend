Contrast Finance v0.5.113

Changed files:
- app/services/sigex_signing.py
- app/web/sign_avr.html
- app/web/index.html
- app/core/config.py
- tests/test_sigex_mobile_link_v0113.py
- README.md
- CHANGELOG.md
- VERIFY_INSTALL.txt

Behavior:
- SIGEX's `m.egov.kz/mobileSign` web launcher is no longer opened on a phone.
- The backend validates the nested SIGEX service URL and creates the direct `mobileSign:` URI used by the QR itself.
- The web-only `mgovSign` marker is removed from the application URI.
- iOS no longer receives an automatic App Store redirect; the same one-time signing session opens directly in eGov Mobile.

No database migration. Alembic head remains 0021_avr_signed_ddc.
