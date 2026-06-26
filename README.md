# Contrast Finance v0.5.19

Hotfix for Alembic startup after the admin head department percent override patch.

Use the full archive for deploy. It removes the temporary legacy import code and includes a startup script that deletes the stale long Alembic migration file if it exists from an earlier changed-only deploy.

Expected startup path:

```bash
sh scripts/start.sh
```

The script runs:

```bash
rm -f alembic/versions/0010_monthly_closing_head_percent_overrides.py
alembic upgrade 0010_head_pct_overrides
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```
