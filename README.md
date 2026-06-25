# Contrast Finance 2.0 — v0.5.11

Patch: **Legacy import creates editable drafts**.

This version changes only the real legacy import behavior for January–April 2026. Historical events imported from `/legacy-events-2026` are assigned to manager `Тест` as editable drafts (`status=draft`, `money_status=waiting_money`) so they can be checked and corrected through the manager cabinet before being accepted or transferred.

The import still does not create payment requests, Telegram cards, payment queues, or any live payment workflow.
