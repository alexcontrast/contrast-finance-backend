v0.5.55 changed files

- app/api/routes/event_items.py
- app/api/routes/coordinator.py
- alembic/versions/0011_coordinator_singleton.py
- scripts/start.sh
- README.md
- CHANGELOG.md
- app/CHANGED_FILES_README.txt

Deploy normally. Migration 0011_coord_singleton runs automatically and removes existing active coordinator duplicates safely.
