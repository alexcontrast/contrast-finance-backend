v0.5.57 changed files

- app/api/routes/event_items.py
- app/api/routes/payment_requests.py
- app/api/routes/tax.py
- alembic/versions/0012_invoice_tax_context_repair.py
- scripts/start.sh
- README.md
- CHANGELOG.md
- app/CHANGED_FILES_README.txt

Deploy normally. `scripts/start.sh` applies migration `0012_invoice_tax_repair` automatically.
