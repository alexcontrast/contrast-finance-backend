"""Behavioural regressions. All data/services are isolated from production."""
import base64
import hashlib
import io
import json
import unittest
import zipfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import app.models
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models import Department, User, Event, EventItem, EventShare, PaymentRequest, MonthlyClosing, SelfEmployedAccounting, SelfEmployedActSignature
from app.models.pending_act_signature import PendingActSignature
from app.services.auth import create_access_token, native_pin_hash, verify_pin
from app.services.job_leases import acquire_lease, release_lease, persistent_watermark, renew_lease
from app.services.act_archive import signed_archive_response
from app.services.sigex_signing import cms_signer_identity
from app.api.routes import self_employed_accounting as accounting
from app.api.routes import act_signing


class HardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin_hash = native_pin_hash("4826", 1)

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)
        with self.factory() as db:
            db.add_all([Department(id=1, name="Санжар"), Department(id=2, name="Рауфаль")])
            db.flush()
            for uid, role, dept in [(1,"admin",1),(2,"manager",1),(3,"manager",2),(4,"department_head",1),(5,"accountant",1)]:
                db.add(User(id=uid, name=f"Test{uid}", role=role, department_id=dept, phone=f"7701000000{uid}",
                            is_active=True, pin_hash=self.pin_hash, auth_source="native", telegram_id=str(uid)))
            db.commit()
        def isolated_db():
            with self.factory() as db:
                yield db
        app.dependency_overrides[get_db] = isolated_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def auth(self, uid=2):
        with self.factory() as db:
            return {"Authorization": "Bearer " + create_access_token(db.get(User, uid))}

    def event_body(self, **values):
        return dict(client_name="Клиент", title="Тест", event_date="2026-10-14", department_id=1,
                    manager_id=2, client_calc_type="cash", manager_percent=21, status="draft", **values)

    def event(self):
        r = self.client.post("/events", json=self.event_body(), headers=self.auth())
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()["id"]

    def item_body(self, **values):
        data = dict(external_name="Фотограф", external_price="100000", external_quantity=1, external_days=1,
                    amount_fact="50000", payment_method="cash", client_create_token="row-1")
        data.update(values)
        return data

    def item(self, eid, **values):
        r = self.client.post(f"/events/{eid}/items", json=self.item_body(**values), headers=self.auth())
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_anonymous_financial_routes_and_mutations_are_closed(self):
        calls = [("get", "/monthly-expenses?month=2026-10", None),
            ("get", "/monthly-closings", None), ("get", "/monthly-dashboard?month=2026-10", None),
            ("get", "/db/tables", None), ("post", "/departments", {"name":"Injected"}),
            ("post", "/departments/seed", None),
            ("post", "/monthly-expenses", {"month":"2026-10-01","title":"x","amount":10,"allocation_type":"sanzhar_only"})]
        for method, path, body in calls:
            with self.subTest(path=path):
                response = self.client.request(method, path, json=body)
                self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(self.client.get("/monthly-expenses", headers=self.auth()).status_code, 403)

    def test_expense_creator_is_authenticated_admin(self):
        r = self.client.post("/monthly-expenses", headers=self.auth(1), json={"month":"2026-10-01",
            "title":"Расход","amount":100,"allocation_type":"sanzhar_only","created_by_user_id":3})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()["created_by_user_id"],1)

    def test_manager_cannot_accept_or_set_initial_salary_rate(self):
        body = self.event_body(); body.update(status="accepted", manager_percent=100)
        self.assertEqual(self.client.post("/events",json=body,headers=self.auth()).status_code,403)
        body["status"] = "draft"
        r = self.client.post("/events",json=body,headers=self.auth())
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(Decimal(r.json()["manager_percent"]),Decimal(21))
        body["status"] = "accepted"
        self.assertEqual(self.client.patch(f'/events/{r.json()["id"]}',json=body,headers=self.auth()).status_code,403)

    def test_head_cannot_move_own_department(self):
        response = self.client.patch("/auth/me/profile", headers=self.auth(4),
            json={"name":"Test4","department_id":2})
        self.assertEqual(response.status_code,403,response.text)

    def test_pin_reset_revokes_old_tokens_and_upgrades_hash(self):
        before = self.auth()
        r = self.client.patch("/auth/change-pin", headers=before, json={"old_pin":"4826","new_pin":"926183"})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.client.get("/auth/me",headers=before).status_code,401)
        self.assertEqual(self.client.get("/auth/me",headers={"Authorization":"Bearer "+r.json()["access_token"]}).status_code,200)
        with self.factory() as db:
            user=db.get(User,2)
            self.assertTrue(user.pin_hash.startswith("pbkdf2_sha256$"))
            self.assertTrue(verify_pin(user,"926183"))
            self.assertFalse(verify_pin(user,"4826"))

    def test_login_limit_is_shared_by_sessions(self):
        statuses=[self.client.post("/auth/login",json={"name":"missing","pin":"1111","auth_mode":"manager"}).status_code for _ in range(13)]
        self.assertEqual(statuses[:12],[401]*12)
        self.assertEqual(statuses[-1],429)

    def test_accountant_can_log_in(self):
        r=self.client.post("/auth/login",json={"name":"Test5","pin":"4826","auth_mode":"accountant"})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()["user"]["role"],"accountant")

    def test_client_cannot_forge_kgd_or_paid_amount(self):
        row=self.item(self.event(),payment_method="invoice",iin_bin="770100000001",iin_bin_locked=True,
            tax_check_status="our_vat",vat_amount=90000,deduction_amount=80000,paid_amount=99999)
        self.assertFalse(row["iin_bin_locked"])
        self.assertIsNone(row["tax_check_status"])
        self.assertEqual(Decimal(row["vat_amount"]),0)
        self.assertEqual(Decimal(row["paid_amount"]),0)

    def test_bin_can_be_explicitly_reset_without_active_request(self):
        eid=self.event(); row=self.item(eid,payment_method="invoice",iin_bin="770100000001")
        with self.factory() as db:
            item=db.get(EventItem,row["id"]);item.iin_bin_locked=True;item.tax_check_status="our_vat";db.commit()
        body=self.item_body(payment_method="invoice",iin_bin="770100000002",reset_tax_context=True)
        r=self.client.patch(f'/event-items/{row["id"]}',headers=self.auth(),json=body)
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()["iin_bin"],"770100000002")
        self.assertFalse(r.json()["iin_bin_locked"])

    def test_idempotent_row_post_never_replays_old_values(self):
        eid=self.event();row=self.item(eid)
        body=self.item_body(external_name="Исправленная строка")
        self.assertEqual(self.client.patch(f'/event-items/{row["id"]}',headers=self.auth(),json=body).status_code,200)
        repeated=self.client.post(f"/events/{eid}/items",headers=self.auth(),json=self.item_body())
        self.assertEqual(repeated.json()["external_name"],"Исправленная строка")

    def test_payment_retry_is_idempotent_and_body_bound(self):
        row=self.item(self.event()); endpoint=f'/event-items/{row["id"]}/payment-requests'
        body={"amount_requested":10000,"payment_method":"cash","client_request_token":"operation-1"}
        a=self.client.post(endpoint,headers=self.auth(),json=body)
        b=self.client.post(endpoint,headers=self.auth(),json=body)
        self.assertEqual(a.status_code,200,a.text);self.assertEqual(b.status_code,200,b.text)
        self.assertEqual(a.json()["id"],b.json()["id"])
        body["amount_requested"]=20000
        self.assertEqual(self.client.post(endpoint,headers=self.auth(),json=body).status_code,409)

    def test_deleted_position_and_cancelled_event_reject_payments(self):
        eid=self.event();row=self.item(eid)
        self.assertEqual(self.client.delete(f'/event-items/{row["id"]}',headers=self.auth()).status_code,200)
        r=self.client.post(f'/event-items/{row["id"]}/payment-requests',headers=self.auth(),json={"amount_requested":100,"payment_method":"cash"})
        self.assertEqual(r.status_code,404,r.text)

    def test_coauthor_cannot_take_ownership_by_removing_others(self):
        eid=self.event()
        self.assertEqual(self.client.post(f"/events/{eid}/coauthor",headers=self.auth(),json={"manager_id":3}).status_code,200)
        r=self.client.post(f"/events/{eid}/coauthor/remove",headers=self.auth(3))
        self.assertEqual(r.status_code,403,r.text)
        with self.factory() as db:self.assertEqual(db.get(Event,eid).manager_id,2)

    def test_closed_month_blocks_changes_until_reopened(self):
        eid=self.event(); row=self.item(eid)
        with self.factory() as db:db.add(MonthlyClosing(month=date(2026,10,1),status="closed"));db.commit()
        endpoint=f'/event-items/{row["id"]}'
        self.assertEqual(self.client.patch(endpoint,headers=self.auth(),json=self.item_body(external_name="Новая")).status_code,409)
        self.assertEqual(self.client.post("/monthly-closings/reopen?month=2026-10",headers=self.auth(1)).status_code,200)
        self.assertEqual(self.client.patch(endpoint,headers=self.auth(),json=self.item_body(external_name="Новая")).status_code,200)

    def test_invalid_item_types_and_zero_quantity_rejected(self):
        eid=self.event()
        for values in [{"item_type":"admin"},{"external_quantity":0},{"external_days":1.5},{"payment_method":"hacked"}]:
            with self.subTest(values=values):
                self.assertEqual(self.client.post(f"/events/{eid}/items",headers=self.auth(),json=self.item_body(**values)).status_code,422)

    def test_receipt_timezone_and_kazakh_spelling(self):
        self.assertEqual(accounting.clean_datetime("2026-08-31T23:30:00Z"),datetime(2026,9,1,4,30))
        self.assertEqual(accounting.clean_datetime("2026-08-31T23:30:00"),datetime(2026,8,31,23,30))
        self.assertEqual(accounting.prefer_full_person_name("СЕРИКБАЙ БЕКЗАТ НУРЕИСАУЛЫ","СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ"),"СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ")
        self.assertEqual(accounting.prefer_full_person_name("ИВАНОВ ИВАН", "ПЕТРОВ ИВАН ПЕТРОВИЧ"),"ИВАНОВ ИВАН")

    def test_signing_freezes_document_and_queue_retains_both_cms(self):
        with self.factory() as db:
            record=SelfEmployedAccounting(act_status="generated",act_sha256="a"*64,act_session_status="signing")
            db.add(record);db.commit()
            with self.assertRaises(Exception):accounting._assert_act_mutable(record)
            first, second = b"first"*32, b"second"*32
            for data in [first, second]:
                act_signing._stage_pending_signature(db,record,base64.b64encode(data).decode());db.commit()
            self.assertEqual(bytes(record.act_pending_signature_data),first)
            queued=db.execute(select(PendingActSignature).order_by(PendingActSignature.id)).scalars().all()
            self.assertEqual([bytes(q.signature_data) for q in queued],[first,second])
            self.assertTrue(act_signing._advance_pending_signature(db,record,hashlib.sha256(first).hexdigest()))
            self.assertEqual(bytes(record.act_pending_signature_data),second)

    def test_portable_archive_preserves_source_and_two_cms(self):
        pdf=b"%PDF-1.4 isolated test source"
        with self.factory() as db:
            record=SelfEmployedAccounting(act_status="signed",act_data=pdf,act_sha256=hashlib.sha256(pdf).hexdigest())
            db.add(record);db.flush()
            for role in ("customer","contractor"):
                cms=role.encode()
                db.add(SelfEmployedActSignature(accounting_id=record.id,signer_role=role,expected_iin="770100000001",phone="",
                    token=role,token_expires_at=datetime(2030,1,1),status="signed",signature_data=cms,signature_sha256=hashlib.sha256(cms).hexdigest()))
            db.commit()
            response=signed_archive_response(db,record)
            self.assertEqual(response.media_type,"application/zip")
            with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
                self.assertEqual(archive.read("AVR_original.pdf"),pdf)
                self.assertEqual(archive.read("signature_customer.cms"),b"customer")
                manifest=json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["sha256"]["AVR_original.pdf"],record.act_sha256)

    def test_job_lease_and_restart_watermark(self):
        first=acquire_lease("test-job",factory=self.factory)
        self.assertTrue(first)
        self.assertIsNone(acquire_lease("test-job",factory=self.factory))
        release_lease("test-job",first,factory=self.factory)
        self.assertTrue(acquire_lease("test-job",factory=self.factory))
        with self.factory() as db:
            a=persistent_watermark(db,"bot-cutover",datetime(2026,10,1))
        with self.factory() as db:
            b=persistent_watermark(db,"bot-cutover",datetime(2026,10,15))
        self.assertEqual(a,b)

    def test_cms_uses_signerinfo_not_extra_expected_certificate(self):
        def cert(iin,serial):
            key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
            name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,"Test"),x509.NameAttribute(NameOID.SERIAL_NUMBER,"IIN"+iin)])
            certificate=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(serial).not_valid_before(datetime(2026,1,1)).not_valid_after(datetime(2027,1,1)).sign(key,hashes.SHA256())
            return key,certificate
        key,foreign=cert("770100000001",11); _,expected=cert("770100000002",12)
        cms=pkcs7.PKCS7SignatureBuilder().set_data(b"document").add_signer(foreign,key,hashes.SHA256()).add_certificate(expected).sign(serialization.Encoding.DER,[pkcs7.PKCS7Options.DetachedSignature])
        self.assertEqual(cms_signer_identity(base64.b64encode(cms).decode(),["770100000002"])[0],"770100000001")

    def test_security_headers_and_request_limit(self):
        r=self.client.get("/")
        self.assertIn("'strict-dynamic'",r.headers["Content-Security-Policy"])
        self.assertIn('nonce="',r.text)
        r=self.client.post("/auth/login",headers={"content-length":str(30*1024*1024)},content=b"{}")
        self.assertEqual(r.status_code,413)

    def test_both_signatures_finalize_and_subscription_error_stops_automatic_retry(self):
        first,second=b"first"*32,b"second"*32
        pdf=b"%PDF-1.4 isolated source"
        with self.factory() as db:
            record=SelfEmployedAccounting(act_status="generated",iin="770100000002",contractor_full_name="Test contractor",
                act_filename="AVR.pdf",act_data=pdf,act_sha256=hashlib.sha256(pdf).hexdigest(),act_session_status="finalizing")
            db.add(record);db.commit();rid=record.id
            for raw in (first,second):act_signing._stage_pending_signature(db,record,base64.b64encode(raw).decode());db.commit()
        def role(_record,signature):
            customer=base64.b64decode(signature)==first
            return ("customer" if customer else "contractor","881118350706" if customer else "770100000002","Test")
        with patch.object(act_signing,"SessionLocal",self.factory), patch.object(act_signing,"_signer_role",side_effect=role), \
             patch.object(act_signing,"register_document_signature",return_value=("doc-test",1)) as register, \
             patch.object(act_signing,"add_document_signature",return_value=2) as add, \
             patch.object(act_signing,"finalize_document_data") as finalize, patch.object(act_signing,"_start_ddc_worker"):
            act_signing._finalize_pending_signature(rid)
            self.assertEqual(register.call_count,1);self.assertEqual(add.call_count,1)
            finalize.assert_called_once_with("doc-test",pdf)
        with self.factory() as db:
            record=db.get(SelfEmployedAccounting,rid)
            self.assertEqual(record.act_status,"signed")
            self.assertIsNone(record.act_pending_signature_sha256)
            signatures=db.execute(select(SelfEmployedActSignature).where(SelfEmployedActSignature.accounting_id==rid)).scalars().all()
            self.assertEqual({s.status for s in signatures},{"signed"})
            self.assertEqual({bytes(s.signature_data) for s in signatures},{first,second})
        from app.services.sigex_signing import SigexError
        with patch.object(act_signing,"SessionLocal",self.factory), patch.object(act_signing,"build_document_card",
            side_effect=SigexError("Feature is not available on current subscription level")) as builder:
            act_signing._build_signed_ddc(rid);act_signing._build_signed_ddc(rid)
            self.assertEqual(builder.call_count,1)
        with self.factory() as db:self.assertEqual(db.get(SelfEmployedAccounting,rid).act_ddc_status,"unavailable")

    def test_signed_identity_does_not_change_when_phone_is_edited(self):
        with self.factory() as db:
            record=SelfEmployedAccounting(contractor_full_name="СЕРИКБАЙ БЕКЗАТ НУРЕИСАУЛЫ",iin="060819550845",
                act_status="signed",receipt_filename="old.png",service_name="Фото",receipt_amount=100000)
            db.add(record);db.commit();rid=record.id
            db.add(SelfEmployedAccounting(contractor_full_name="СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ",iin="060819550845"));db.commit()
        response=self.client.patch(f"/accounting/self-employed/receipts/{rid}",headers=self.auth(1),json={"contractor_phone":"87021123403"})
        self.assertEqual(response.status_code,200,response.text)
        with self.factory() as db:self.assertEqual(db.get(SelfEmployedAccounting,rid).contractor_full_name,"СЕРИКБАЙ БЕКЗАТ НУРЕИСАУЛЫ")

    def test_partial_receipt_number_update_checks_existing_iin(self):
        with self.factory() as db:
            db.add(SelfEmployedAccounting(iin="030919651322",receipt_number="000000000042",receipt_filename="one.png"))
            second=SelfEmployedAccounting(iin="030919651322",receipt_number="000000000043",receipt_filename="two.png")
            db.add(second);db.commit();rid=second.id
        response=self.client.patch(f"/accounting/self-employed/receipts/{rid}",headers=self.auth(1),json={"receipt_number":"000000000042"})
        self.assertEqual(response.status_code,409,response.text)

    def test_combined_kgd_runs_once_before_creating_the_row(self):
        from app.api.routes import tax
        from app.services.kgd.client import KgdTaxpayerResult
        eid=self.event();created=[]
        original=tax.create_event_item
        def create(*args,**kwargs):created.append(True);return original(*args,**kwargs)
        def kgd(_):
            self.assertFalse(created,"Network KGD must run before the row lock/create path")
            return KgdTaxpayerResult(iin_bin="770100000001",tax_status="our_vat",message="OK",source="kgd",contractor_name="Test")
        with patch.object(tax,"create_event_item",side_effect=create),patch.object(tax,"check_taxpayer",side_effect=kgd) as remote:
            r=self.client.post(f"/events/{eid}/items/tax/check",headers=self.auth(),json={"item":self.item_body(),"iin_bin":"770100000001"})
        self.assertEqual(r.status_code,200,r.text);self.assertEqual(remote.call_count,1)
        self.assertEqual(r.json()["item"]["tax_check_status"],"our_vat")

    def test_status_batch_requires_access_and_returns_requested_records(self):
        with self.factory() as db:
            row=SelfEmployedAccounting(receipt_filename="r.png",contractor_full_name="Test",act_status="generated")
            db.add(row);db.commit();rid=row.id
        endpoint=f"/accounting/self-employed/acts/status-batch?ids={rid}"
        self.assertEqual(self.client.get(endpoint,headers=self.auth()).status_code,403)
        r=self.client.get(endpoint,headers=self.auth(5))
        self.assertEqual(r.status_code,200,r.text);self.assertEqual([x["accounting_id"] for x in r.json()],[rid])

    def test_case_insensitive_name_and_old_phone_format_login(self):
        with self.factory() as db:
            user=db.get(User,2);user.name="АЛЕКСЕЙ";user.phone="8 701 000 0002";db.commit()
        for body in [{"name":"алексей"},{"phone":"+7 (701) 000-00-02"}]:
            r=self.client.post("/auth/login",json={**body,"pin":"4826","auth_mode":"manager"})
            self.assertEqual(r.status_code,200,r.text)
        r=self.client.patch("/auth/me/profile",headers=self.auth(3),json={"name":"алексей","department_id":2})
        self.assertEqual(r.status_code,409,r.text)

    def test_expired_cms_does_not_strand_the_other_received_signature(self):
        first,second=b"expired"*32,b"fresh"*32
        with self.factory() as db:
            record=SelfEmployedAccounting(act_status="generated",act_sha256="a"*64,act_session_status="finalizing")
            db.add(record);db.commit();rid=record.id
            for raw in (first,second):
                act_signing._stage_pending_signature(db,record,base64.b64encode(raw).decode());db.commit()
        with patch.object(act_signing,"SessionLocal",self.factory),patch.object(act_signing,"_signer_role",return_value=("customer","881118350706","Test")):
            act_signing._mark_signature_error(rid,RuntimeError("Time stamp in OCSP significantly differs from time stamp in TSP"))
        with self.factory() as db:
            record=db.get(SelfEmployedAccounting,rid)
            self.assertEqual(bytes(record.act_pending_signature_data),second)
            self.assertEqual(record.act_session_status,"finalizing")
            self.assertIsNone(record.act_signing_error)
            queued=db.execute(select(PendingActSignature).order_by(PendingActSignature.id)).scalars().all()
            self.assertEqual([q.status for q in queued],["stale","queued"])
            self.assertEqual([bytes(q.signature_data) for q in queued],[first,second])

    def test_lease_cleanup_cannot_release_a_new_owners_lock(self):
        first=acquire_lease("lease-owner",factory=self.factory)
        self.assertTrue(renew_lease("lease-owner",first,90,factory=self.factory))
        release_lease("lease-owner",first,factory=self.factory)
        second=acquire_lease("lease-owner",factory=self.factory)
        self.assertNotEqual(first,second)
        release_lease("lease-owner",first,factory=self.factory)
        self.assertFalse(renew_lease("lease-owner",first,90,factory=self.factory))
        self.assertIsNone(acquire_lease("lease-owner",factory=self.factory))

    def test_failed_database_lease_always_clears_local_worker_flags(self):
        rid=123456
        with patch.object(act_signing,"SessionLocal",self.factory),patch.object(act_signing,"job_lease",side_effect=RuntimeError("DB unavailable")),patch.object(act_signing,"_mark_signature_error"):
            act_signing._active_workers.add(rid)
            act_signing._process_signature(rid)
            self.assertNotIn(rid,act_signing._active_workers)
            act_signing._active_ddc_workers.add(rid)
            with self.assertRaisesRegex(RuntimeError,"DB unavailable"):
                act_signing._ddc_worker(rid,False)
            self.assertNotIn(rid,act_signing._active_ddc_workers)

    def test_egov_wait_releases_database_connection(self):
        from sqlalchemy import event as sql_event
        checked_out=[0]
        sql_event.listen(self.engine,"checkout",lambda *_:checked_out.__setitem__(0,checked_out[0]+1))
        sql_event.listen(self.engine,"checkin",lambda *_:checked_out.__setitem__(0,checked_out[0]-1))
        with self.factory() as db:
            record=SelfEmployedAccounting(act_status="generated",act_session_status="signing",act_data=b"%PDF",
                act_session_expires_at=datetime.utcnow()+timedelta(minutes=5))
            db.add(record);db.commit();rid=record.id
        def wait(**_):
            self.assertEqual(checked_out[0],0,"The eGov network wait holds a SQL connection")
            raise RuntimeError("isolated network interruption")
        with patch.object(act_signing,"SessionLocal",self.factory),patch.object(act_signing,"wait_for_egov_signature",side_effect=wait) as remote:
            act_signing._process_signature(rid)
            self.assertEqual(remote.call_count,1)
        self.assertEqual(checked_out[0],0)

    def test_telegram_pin_binding_has_shared_attempt_limit(self):
        from types import SimpleNamespace
        from app.telegram_bot import main as bot
        from fastapi import HTTPException
        sender=SimpleNamespace(id=9999,username="test")
        with self.factory() as db,patch.object(bot,"verify_pin",return_value=False) as verify:
            for _ in range(12):
                with self.assertRaisesRegex(RuntimeError,"Неверный телефон"):
                    bot.bind_user_by_phone_pin(db,sender,"77010000002","0000")
            with self.assertRaises(HTTPException) as caught:
                bot.bind_user_by_phone_pin(db,sender,"77010000002","0000")
            self.assertEqual(caught.exception.status_code,429)
            self.assertEqual(verify.call_count,12)

    def test_site_and_bot_share_payment_fixation_rules(self):
        from app.telegram_bot import main as bot
        from app.services.payment_method_rules import allowed_payment_methods
        from fastapi import HTTPException
        eid=self.event();row=self.item(eid)
        with self.factory() as db:
            item=db.get(EventItem,row['id']);item.payment_method="invoice";item.iin_bin="770100000001"
            item.iin_bin_locked=True;item.tax_check_status="our_vat";db.commit()
        # A KGD check alone does not fix the method; an actual request does.
        r=self.client.post(f'/event-items/{row["id"]}/payment-requests',headers=self.auth(),json={
            "amount_requested":1000,"payment_method":"cash","client_request_token":"site-cash"})
        self.assertEqual(r.status_code,200,r.text)
        with self.factory() as db:
            item=db.get(EventItem,row['id'])
            self.assertEqual(allowed_payment_methods(db,item),["cash","card"])
            self.assertIsNone(bot.fixed_payment_method_for_item(db,item))
        payload={"event_id":eid,"item_id":row['id'],"amount":1000,"payment_method":"card",
                 "card_number":"4400430012345678","client_request_token":"bot-card"}
        with patch.object(bot,"SessionLocal",self.factory):
            request=bot.create_payment_request_from_bot("2",payload)
            self.assertEqual(request.payment_method,"card")
            with self.assertRaises(HTTPException) as raised:
                bot.create_payment_request_from_bot("2",{**payload,"payment_method":"self_employed",
                    "comment":"Иванов","client_request_token":"bot-invalid"})
            self.assertEqual(raised.exception.status_code,409)

    def test_unrelated_signature_cannot_block_a_valid_signature_in_the_queue(self):
        from app.services.sigex_signing import SigexError
        first,second=b"unrelated"*32,b"contractor"*32
        with self.factory() as db:
            record=SelfEmployedAccounting(act_status="generated",act_sha256="a"*64,act_data=b"%PDF",
                iin="770100000002",act_session_status="finalizing")
            db.add(record);db.commit();rid=record.id
            for raw in (first,second):
                act_signing._stage_pending_signature(db,record,base64.b64encode(raw).decode());db.commit()
        def role(record,signature):
            if base64.b64decode(signature)==first:raise SigexError("ИИН в ЭЦП не совпадает ни с ИП, ни с самозанятым в АВР")
            return "contractor","770100000002","Test"
        with patch.object(act_signing,"SessionLocal",self.factory),patch.object(act_signing,"_signer_role",side_effect=role), \
             patch.object(act_signing,"register_document_signature",return_value=("valid-document",1)),patch.object(act_signing,"finalize_document_data"):
            act_signing._finalize_pending_signature(rid)
        with self.factory() as db:
            record=db.get(SelfEmployedAccounting,rid)
            self.assertEqual(record.act_status,"partially_signed")
            self.assertIsNone(record.act_pending_signature_sha256)
            rows=db.execute(select(PendingActSignature).order_by(PendingActSignature.id)).scalars().all()
            self.assertEqual([r.status for r in rows],["rejected","completed"])
            self.assertEqual([bytes(r.signature_data) for r in rows],[first,second])

    def test_regular_kgd_wait_does_not_hold_a_database_connection(self):
        from sqlalchemy import event as sql_event
        from app.api.routes import tax
        from app.services.kgd.client import KgdTaxpayerResult
        eid=self.event();row=self.item(eid);headers=self.auth()
        checked_out=[0]
        sql_event.listen(self.engine,"checkout",lambda *_:checked_out.__setitem__(0,checked_out[0]+1))
        sql_event.listen(self.engine,"checkin",lambda *_:checked_out.__setitem__(0,checked_out[0]-1))
        def kgd(_):
            self.assertEqual(checked_out[0],0,"KGD HTTP holds the editor's database connection")
            return KgdTaxpayerResult(iin_bin="770100000001",tax_status="our_vat",message="OK",source="kgd",contractor_name="Test")
        with patch.object(tax,"check_taxpayer",side_effect=kgd) as remote:
            r=self.client.post(f'/event-items/{row["id"]}/tax/check',headers=headers,json={"iin_bin":"770100000001"})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(remote.call_count,1)
        self.assertEqual(checked_out[0],0)

    def test_combined_kgd_releases_connection_and_reports_name(self):
        from sqlalchemy import event as sql_event
        from app.api.routes import tax
        from app.services.kgd.client import KgdTaxpayerResult
        eid=self.event();headers=self.auth();checked_out=[0]
        sql_event.listen(self.engine,"checkout",lambda *_:checked_out.__setitem__(0,checked_out[0]+1))
        sql_event.listen(self.engine,"checkin",lambda *_:checked_out.__setitem__(0,checked_out[0]-1))
        def kgd(_):
            self.assertEqual(checked_out[0],0)
            return KgdTaxpayerResult(iin_bin="770100000001",tax_status="our_vat",message="Test / ОУР",source="kgd",contractor_name="Test")
        with patch.object(tax,"check_taxpayer",side_effect=kgd):
            response=self.client.post(f"/events/{eid}/items/tax/check",headers=headers,json={"item":self.item_body(),"iin_bin":"770100000001"})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()["tax"]["contractor_name"],"Test")

    def test_not_found_response_does_not_lock_or_grant_deductions(self):
        from app.api.routes import tax
        from app.services.kgd.client import KgdTaxpayerResult
        eid=self.event();row=self.item(eid)
        result=KgdTaxpayerResult(iin_bin="770100000001",tax_status="not_found",message="КГД не нашёл БИН/ИИН",source="kgd")
        with patch.object(tax,"check_taxpayer",return_value=result):
            response=self.client.post(f'/event-items/{row["id"]}/tax/check',headers=self.auth(),json={"iin_bin":"770100000001"})
        self.assertEqual(response.status_code,200,response.text)
        body=response.json();self.assertFalse(body["iin_bin_locked"])
        self.assertEqual(body["tax_check_status"],"not_found")
        self.assertIn("не нашёл",body["message"])
        self.assertEqual(Decimal(body["deduction_amount"]),0)

    def test_technical_kgd_failure_is_503_and_does_not_modify_item(self):
        from app.api.routes import tax
        from app.services.kgd.client import KgdServiceError
        eid=self.event();row=self.item(eid)
        with patch.object(tax,"check_taxpayer",side_effect=KgdServiceError("КГД временно недоступен")):
            response=self.client.post(f'/event-items/{row["id"]}/tax/check',headers=self.auth(),json={"iin_bin":"770100000001"})
        self.assertEqual(response.status_code,503,response.text)
        with self.factory() as db:
            item=db.get(EventItem,row["id"])
            self.assertFalse(item.iin_bin_locked)
            self.assertIsNone(item.tax_check_status)

    def test_payment_combined_retry_reuses_the_same_created_item(self):
        from app.api.routes import tax
        from app.services.kgd.client import KgdTaxpayerResult
        eid=self.event();body={"item":self.item_body(client_create_token="payment-bin-retry-token"),"iin_bin":"770100000001","payment_context":True}
        result=KgdTaxpayerResult(iin_bin="770100000001",tax_status="our_vat",message="Test",source="kgd")
        with patch.object(tax,"check_taxpayer",return_value=result):
            first=self.client.post(f"/events/{eid}/items/tax/check",headers=self.auth(),json=body)
            second=self.client.post(f"/events/{eid}/items/tax/check",headers=self.auth(),json=body)
        self.assertEqual(first.status_code,200,first.text)
        self.assertEqual(second.status_code,200,second.text)
        self.assertEqual(first.json()["item"]["id"],second.json()["item"]["id"])


if __name__ == "__main__":
    unittest.main()
