# CHANGELOG

## v0.40.95 — Department head mobile request cards exact fix

- Fixed mobile department-head request cards by changing their render to use the same mobile-aware position/method cells as the main admin request cards.
- Fixed the real cause of method/KGD text gluing: desktop and mobile method spans were both visible in department-head mobile cards.
- Removed the negative-margin layout that glued amount and manager together.
- Kept the compact card layout while preserving separate amount and manager lines.
- Updated frontend cache version to 0.40.95.

