v0.5.11 — Legacy import creates editable drafts

Changed files:
- app/services/legacy_events_2026_importer.py
- app/web/index.html
- app/web/app.js
- CHANGELOG.md
- README.md

Historical legacy import now creates editable draft events assigned to manager Тест: status=draft, money_status=waiting_money. No payments, requests, Telegram messages or payment queues are created.
