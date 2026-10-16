"""Optional isolated PostgreSQL regression run; requires pgserver, httpx, pytest.

No production database is used. Run from the repository root.
"""
import concurrent.futures
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session


@contextmanager
def isolated_database():
    uri = os.getenv("CF_TEST_POSTGRES_URL")
    if uri:
        from urllib.parse import urlparse
        if urlparse(uri).path != "/contrast_test":
            raise RuntimeError("CF_TEST_POSTGRES_URL must point to the isolated contrast_test database")
        yield uri
        return
    import pgserver
    with tempfile.TemporaryDirectory(prefix="contrast-v066-pg-") as root:
        os.chmod(root, 0o755)
        pg = pgserver.get_server(Path(root) / "data", cleanup_mode="stop")
        try:
            yield pg.get_uri()
        finally:
            pg.cleanup()


def run():
    with isolated_database() as uri:
        os.environ.update(DATABASE_URL=uri, ENVIRONMENT="test", JWT_SECRET_KEY="isolated-postgres-regression-secret", GOOGLE_SHEETS_DAILY_EXPORT_ENABLED="false")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        def migrate(target):
            subprocess.run([sys.executable, "-m", "alembic", "upgrade", target], env=env, check=True, timeout=90)
        engine = create_engine(uri)
        try:
            migrate("0021_avr_signed_ddc")
            with engine.begin() as db:
                db.execute(text("INSERT INTO departments(id,name,is_active,created_at,updated_at) VALUES (1,'Test',true,now(),now())"))
                db.execute(text("INSERT INTO users(id,name,role,department_id,is_active,auth_source,created_at,updated_at) VALUES (99,'Preserved','manager',1,true,'native',now(),now())"))
            migrate("head")
            migrate("head")
            with engine.connect() as db:
                assert db.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0023_durable_signing"
                assert db.execute(text("SELECT token_version FROM users WHERE id=99")).scalar_one() == 0
            from fastapi.testclient import TestClient
            from app.main import app
            from app.models import User, Event, EventItem, EventShare, PaymentRequest, MonthlyClosing
            from app.services.auth import native_pin_hash, create_access_token
            from app.services.month_integrity import lock_months
            from datetime import date
            password=native_pin_hash("4826",1)
            with Session(engine) as db:
                for uid, role in [(1,"admin"),(2,"manager"),(3,"manager"),(6,"manager")]:
                    db.add(User(id=uid,name=f"PG{uid}",role=role,department_id=1,is_active=True,auth_source="native",pin_hash=password))
                db.commit()
                token=create_access_token(db.get(User,2))
            headers={"Authorization":"Bearer "+token}
            client=TestClient(app)
            event=client.post("/events",headers=headers,json={"client_name":"PG", "title":"PG", "event_date":"2026-10-15",
                "department_id":1,"manager_id":2,"client_calc_type":"cash","status":"draft"})
            assert event.status_code==200,event.text
            eid=event.json()["id"]
            row=client.post(f"/events/{eid}/items",headers=headers,json={"external_name":"PG expense","external_price":100000,
                "amount_fact":50000,"payment_method":"cash","client_create_token":"pg-row"})
            assert row.status_code==200,row.text
            iid=row.json()["id"]
            payment={"amount_requested":1000,"payment_method":"cash","client_request_token":"pg-retry"}
            def pay():return client.post(f"/event-items/{iid}/payment-requests",headers=headers,json=payment)
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                responses=list(pool.map(lambda _:pay(),range(4)))
            assert all(r.status_code==200 for r in responses),[r.text for r in responses]
            assert len({r.json()["id"] for r in responses})==1
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                responses=list(pool.map(lambda uid:client.post(f"/events/{eid}/coauthor",headers=headers,json={"manager_id":uid}),[3,6]))
            assert all(r.status_code==200 for r in responses),[r.text for r in responses]
            with Session(engine) as db:
                shares=db.execute(select(EventShare).where(EventShare.event_id==eid)).scalars().all()
                assert len(shares)==3 and sum(s.share_percent for s in shares)==100
            with Session(engine) as db:
                item_revision=db.get(EventItem,iid).updated_at.isoformat()
            body={"external_name":"Concurrent", "external_price":100000,"amount_fact":50000,"payment_method":"cash", "expected_updated_at":item_revision}
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                responses=list(pool.map(lambda _:client.patch(f"/event-items/{iid}",headers=headers,json=body),range(2)))
            assert sorted(r.status_code for r in responses)==[200,409],[r.text for r in responses]
            # A write waiting for a concurrent close must observe the closed month.
            month=date(2026,10,1)
            with Session(engine) as closing_db:
                lock_months(closing_db,{month})
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    blocked=pool.submit(client.patch,f"/event-items/{iid}",headers=headers,json={k:v for k,v in body.items() if k!="expected_updated_at"})
                    time.sleep(0.15)
                    closing_db.add(MonthlyClosing(month=month,status="closed"));closing_db.commit()
                    response=blocked.result(timeout=10)
                    assert response.status_code==409,response.text
            client.close()
            print("PostgreSQL: upgrade 0021 -> 0023, repeat upgrade, preserved users, concurrent payment retry, three participants, stale PATCH, close/write race: PASS")
        finally:
            engine.dispose()


if __name__=="__main__":run()
