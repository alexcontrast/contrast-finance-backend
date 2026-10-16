import hashlib
from sqlalchemy import text


def lock_business_keys(db, namespace: str, *values):
    """Serialize creation when the row to lock does not exist yet (PostgreSQL)."""
    if getattr(getattr(db, "bind", None), "dialect", None) is None or db.bind.dialect.name != "postgresql":
        return
    keys = {int.from_bytes(hashlib.sha256(f"{namespace}:{value}".encode()).digest()[:8], "big", signed=True)
            for value in values if value}
    for key in sorted(keys):
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
