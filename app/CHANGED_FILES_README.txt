Contrast Finance v0.5.114

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
- SIGEX `eGovMobileLaunchLink` is validated and preserved as the official HTTPS launcher.
- QR payload `mobileSign:` is not exposed to Safari as an iOS URL scheme.
- Existing active v0.5.113 sessions persisted as `mobileSign:` are reconstructed into the official HTTPS launcher without recreating the AVR.
- `mgovSign` is preserved/restored for the eGov web launcher.
- The mobile signing page keeps the current session alive and offers the same-session QR fallback if iOS Universal Link handling is broken on a particular device.

No database migration. Alembic head remains 0021_avr_signed_ddc.
