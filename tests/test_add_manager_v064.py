import unittest
from pathlib import Path

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - register all model relationships
from app.api.routes.users_manage import NativeUserCreate, create_native_user
from app.db.base import Base
from app.models.department import Department
from app.models.user import User
from app.services.auth import verify_pin


class _NoopDb:
    pass


class AddManagerV064Tests(unittest.TestCase):
    def test_valid_form_creates_active_manager_with_native_pin(self):
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                department = Department(name="Санжар")
                db.add(department)
                db.commit()

                created = create_native_user(
                    NativeUserCreate(
                        name="Новый менеджер",
                        phone="+7 (701) 123 45 67",
                        department_id=department.id,
                        pin="4826",
                        role="manager",
                        is_active=True,
                    ),
                    db,
                    object(),
                )

                stored = db.get(User, created.id)
                self.assertEqual(stored.role, "manager")
                self.assertTrue(stored.is_active)
                self.assertEqual(stored.phone, "77011234567")
                self.assertEqual(stored.department_id, department.id)
                self.assertEqual(stored.auth_source, "native")
                self.assertTrue(verify_pin(stored, "4826"))
        finally:
            engine.dispose()

    def test_create_endpoint_rejects_non_numeric_pin(self):
        with self.assertRaises(HTTPException) as raised:
            create_native_user(NativeUserCreate(name="Новый менеджер",phone="+7 701 123 45 67",
                department_id=None,pin="12ab"),_NoopDb(),object())
        self.assertEqual(raised.exception.status_code,400)
        self.assertIn("от 4 до 12 цифр",raised.exception.detail)

    def test_long_pin_is_rejected_before_reaching_database(self):
        with self.assertRaises(ValidationError) as raised:
            NativeUserCreate(name="Новый менеджер",pin="1234567890123")
        self.assertEqual(raised.exception.errors()[0]["loc"],("pin",))

    def test_admin_ui_has_single_add_manager_action_and_fixed_role(self):
        root = Path(__file__).parents[1]
        html = (root / "app" / "web" / "index.html").read_text(encoding="utf-8")
        source = (root / "app" / "web" / "app.js").read_text(encoding="utf-8")

        self.assertEqual(html.count('id="addManagerOpenBtn"'), 1)
        self.assertIn(">+ Менеджер</button>", html)
        self.assertIn("function openAddManagerModal()", source)
        self.assertIn('role: "manager"', source)
        self.assertIn("is_active: true", source)
        self.assertNotIn('id="newManagerRoleInput"', source)


if __name__ == "__main__":
    unittest.main()
