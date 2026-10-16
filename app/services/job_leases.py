"""Short database transactions elect one worker across API and bot replicas."""
import secrets
import logging
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from sqlalchemy import select, update
from app.db.session import SessionLocal
from app.models.background_state import BackgroundState

logger = logging.getLogger(__name__)


def acquire_lease(key: str, seconds: int = 600, factory=None) -> str | None:
    factory = factory or SessionLocal
    if factory is None:
        return None
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    now, owner = datetime.utcnow(), secrets.token_hex(16)
    with factory() as db:
        insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
        stmt = insert(BackgroundState).values(key=key, owner=owner, lease_until=now + timedelta(seconds=seconds))
        stmt = stmt.on_conflict_do_update(index_elements=[BackgroundState.key],
            set_={"owner": owner, "lease_until": now + timedelta(seconds=seconds)},
            where=BackgroundState.lease_until <= now).returning(BackgroundState.owner)
        won = db.execute(stmt).scalar_one_or_none()
        db.commit()
        return owner if won == owner else None


def release_lease(key: str, owner: str, factory=None, *, delay=0):
    factory = factory or SessionLocal
    if factory is None:
        return
    with factory() as db:
        db.execute(update(BackgroundState).where(BackgroundState.key == key, BackgroundState.owner == owner)
            .values(owner=None, lease_until=datetime.utcnow() + timedelta(seconds=delay)))
        db.commit()


def renew_lease(key: str, owner: str, seconds: int, factory=None) -> bool:
    factory = factory or SessionLocal
    if factory is None:
        return False
    with factory() as db:
        changed = db.execute(update(BackgroundState).where(
            BackgroundState.key == key, BackgroundState.owner == owner
        ).values(lease_until=datetime.utcnow() + timedelta(seconds=seconds))).rowcount
        db.commit()
        return bool(changed)


@contextmanager
def job_lease(key: str, *, seconds=90, delay=0, factory=None):
    """Keep a short shared lease alive while I/O runs without holding SQL locks.

    A killed process stops renewing, so recovery waits at most one short lease
    instead of the maximum duration of an eGov or archive operation.
    """
    owner = acquire_lease(key, seconds=seconds, factory=factory)
    if not owner:
        yield False
        return
    stopped = threading.Event()

    def heartbeat():
        while not stopped.wait(max(1, seconds / 3)):
            try:
                if not renew_lease(key, owner, seconds, factory=factory):
                    logger.error("Background lease ownership lost: %s", key)
                    return
            except Exception:
                logger.exception("Background lease renewal failed: %s", key)

    worker = threading.Thread(target=heartbeat, name="lease-heartbeat", daemon=True)
    worker.start()
    try:
        yield True
    finally:
        stopped.set()
        worker.join(timeout=2)
        try:
            release_lease(key, owner, factory=factory, delay=delay() if callable(delay) else delay)
        except Exception:
            # Cleanup must not mask the original failure or prevent the local
            # active-worker flag from being cleared. The lease still expires.
            logger.exception("Background lease release failed: %s", key)


def persistent_watermark(db, key: str, initial: datetime) -> datetime:
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    db.execute(insert(BackgroundState).values(key=key, lease_until=datetime.min, watermark=initial)
        .on_conflict_do_nothing(index_elements=[BackgroundState.key]))
    value = db.execute(select(BackgroundState.watermark).where(BackgroundState.key == key)).scalar_one()
    db.commit()
    return value or initial
