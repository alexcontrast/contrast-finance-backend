"""Execute the two new migrations on a populated baseline schema.

PostgreSQL-specific full-history/concurrency checks live in verify_postgres.py.
"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import MetaData, Table, create_engine, inspect, select
import app.models
from app.db.base import Base


class MigrationTests(unittest.TestCase):
    def test_new_migrations_preserve_data_and_can_be_reversed(self):
        engine=create_engine("sqlite://")
        baseline=MetaData()
        excluded_tables={"auth_attempts","background_states","pending_act_signatures"}
        excluded_columns={"users":{"token_version"},"payment_requests":{"operation_key","operation_hash"}}
        for table in Base.metadata.sorted_tables:
            if table.name in excluded_tables:continue
            Table(table.name,baseline,*(column._copy() for column in table.columns
                if column.name not in excluded_columns.get(table.name,set())))
        baseline.create_all(engine)
        modules=[]
        for name in ("0022_finance_hardening","0023_durable_signing"):
            file=Path(__file__).parents[1]/"alembic"/"versions"/(name+".py")
            spec=importlib.util.spec_from_file_location(name,file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            modules.append(module)
        with engine.begin() as connection:
            connection.execute(baseline.tables["departments"].insert().values(id=1,name="Test"))
            connection.execute(baseline.tables["users"].insert().values(id=7,name="Preserved",role="manager",department_id=1))
            with Operations.context(MigrationContext.configure(connection)):
                with patch.object(modules[0].context,"is_offline_mode",return_value=False):
                    modules[0].upgrade()
                modules[1].upgrade()
            self.assertIn("auth_attempts",inspect(connection).get_table_names())
            self.assertIn("pending_act_signatures",inspect(connection).get_table_names())
            from app.models.user import User
            self.assertEqual(connection.execute(select(User.name,User.token_version).where(User.id==7)).one(),("Preserved",0))
            self.assertTrue(any(i["name"]=="uq_event_shares_event_user" and i["unique"] for i in inspect(connection).get_indexes("event_shares")))
            with Operations.context(MigrationContext.configure(connection)):
                modules[1].downgrade();modules[0].downgrade()
            self.assertNotIn("auth_attempts",inspect(connection).get_table_names())
            self.assertEqual(connection.execute(select(baseline.tables["users"].c.name).where(baseline.tables["users"].c.id==7)).scalar_one(),"Preserved")
        engine.dispose()
