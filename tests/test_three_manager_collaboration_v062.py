import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - register every relationship before create_all
from app.api.routes.events import EventManagerActionPayload, add_event_coauthor
from app.api.routes.manager_dashboard import coauthor_info, event_share_percent_for_manager
from app.db.base import Base
from app.models.department import Department
from app.models.event import Event
from app.models.event_share import EventShare
from app.models.user import User
from app.services.event_collaboration import (
    equal_event_share_allocations,
    ordered_event_participant_ids,
)


def share(user_id: int, percent: str, share_id: int):
    return SimpleNamespace(
        id=share_id,
        user_id=user_id,
        share_percent=Decimal(percent),
    )


class ThreeManagerCollaborationV062Tests(unittest.TestCase):
    def test_three_managers_split_exactly_one_hundred_percent(self):
        allocations = equal_event_share_allocations([10, 20, 30])

        self.assertEqual(
            allocations,
            [
                (10, Decimal("33.34")),
                (20, Decimal("33.33")),
                (30, Decimal("33.33")),
            ],
        )
        self.assertEqual(sum((value for _, value in allocations), Decimal("0.00")), Decimal("100.00"))

    def test_two_manager_behavior_remains_fifty_fifty(self):
        self.assertEqual(
            equal_event_share_allocations([10, 20]),
            [(10, Decimal("50.00")), (20, Decimal("50.00"))],
        )

    def test_owner_is_first_and_duplicate_share_rows_are_ignored(self):
        event = SimpleNamespace(
            manager_id=10,
            shares=[
                share(20, "33.33", 3),
                share(10, "33.34", 2),
                share(20, "33.33", 4),
                share(30, "33.33", 5),
            ],
        )

        self.assertEqual(ordered_event_participant_ids(event), [10, 20, 30])

    def test_each_manager_receives_own_third_in_plan(self):
        event = SimpleNamespace(
            manager_id=10,
            shares=[
                share(10, "33.34", 1),
                share(20, "33.33", 2),
                share(30, "33.33", 3),
            ],
        )

        self.assertEqual(event_share_percent_for_manager(event, SimpleNamespace(id=10)), Decimal("33.34"))
        self.assertEqual(event_share_percent_for_manager(event, SimpleNamespace(id=20)), Decimal("33.33"))
        self.assertEqual(event_share_percent_for_manager(event, SimpleNamespace(id=30)), Decimal("33.33"))

    def test_dashboard_returns_both_other_managers(self):
        event = SimpleNamespace(
            manager_id=10,
            shares=[
                share(10, "33.34", 1),
                share(20, "33.33", 2),
                share(30, "33.33", 3),
            ],
        )
        users = {
            10: SimpleNamespace(id=10, name="Анна"),
            20: SimpleNamespace(id=20, name="Борис"),
            30: SimpleNamespace(id=30, name="Вера"),
        }

        info = coauthor_info(event, users[20], users)

        self.assertTrue(info["is_coauthored"])
        self.assertEqual(info["participant_user_ids"], [10, 20, 30])
        self.assertEqual(info["coauthor_user_ids"], [10, 30])
        self.assertEqual(info["coauthor_names"], ["Анна", "Вера"])

    def test_fourth_manager_is_rejected_by_allocation_helper(self):
        with self.assertRaises(ValueError):
            equal_event_share_allocations([10, 20, 30, 40])

    def test_route_persists_third_manager_after_existing_shares_were_loaded(self):
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                department = Department(name="Тестовый отдел")
                db.add(department)
                db.flush()
                managers = [
                    User(
                        department_id=department.id,
                        name=name,
                        role="manager",
                        is_active=True,
                    )
                    for name in ("Анна", "Борис", "Вера")
                ]
                db.add_all(managers)
                db.flush()
                event = Event(
                    client_name="Заказчик",
                    title="Мероприятие",
                    event_date=date(2026, 10, 7),
                    department_id=department.id,
                    manager_id=managers[0].id,
                    status="draft",
                    money_status="waiting_money",
                    client_calc_type="cash",
                    manager_percent=Decimal("21.00"),
                    agency_commission_amount=Decimal("0.00"),
                    customer_paid_amount=Decimal("0.00"),
                    agency_commission_spread_enabled="false",
                )
                db.add(event)
                db.flush()
                db.add_all(
                    [
                        EventShare(event_id=event.id, user_id=managers[0].id, share_percent=Decimal("50.00")),
                        EventShare(event_id=event.id, user_id=managers[1].id, share_percent=Decimal("50.00")),
                    ]
                )
                db.commit()

                add_event_coauthor(
                    event.id,
                    EventManagerActionPayload(manager_id=managers[2].id),
                    db,
                    managers[0],
                )

                persisted = db.execute(
                    select(EventShare)
                    .where(EventShare.event_id == event.id)
                    .order_by(EventShare.user_id)
                ).scalars().all()
                self.assertEqual(
                    [(row.user_id, row.share_percent) for row in persisted],
                    [
                        (managers[0].id, Decimal("33.34")),
                        (managers[1].id, Decimal("33.33")),
                        (managers[2].id, Decimal("33.33")),
                    ],
                )
        finally:
            engine.dispose()

    def test_browser_keeps_add_and_remove_actions_separate(self):
        source = (Path(__file__).parents[1] / "app" / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn('participantCount < MAX_EVENT_PARTICIPANTS', source)
        self.assertIn('>+ Соавтор</button>', source)
        self.assertIn('>Убрать соавторов</button>', source)
        self.assertIn('!participantIds.includes(Number(manager.id))', source)
        self.assertIn('names.length > 1 ? "Соавторы" : "Соавтор"', source)
        self.assertIn('Соавтор добавлен, доли пересчитаны', source)


if __name__ == "__main__":
    unittest.main()
