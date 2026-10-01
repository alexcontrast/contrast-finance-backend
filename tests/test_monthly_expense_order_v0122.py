import unittest

from app.api.routes import monthly_expenses


class _EmptyResult:
    def scalars(self):
        return self

    def all(self):
        return []

    def scalar_one_or_none(self):
        return None


class _RecordingDb:
    def __init__(self):
        self.queries = []

    def execute(self, query):
        self.queries.append(query)
        return _EmptyResult()


class MonthlyExpenseOrderV0122Tests(unittest.TestCase):
    def test_close_month_expenses_are_newest_first_by_creation_time(self):
        db = _RecordingDb()

        monthly_expenses.list_monthly_expenses("2026-09", db)

        sql = " ".join(str(db.queries[0]).split())
        self.assertIn(
            "ORDER BY monthly_expenses.created_at DESC, monthly_expenses.id DESC",
            sql,
        )
        self.assertNotIn("ORDER BY monthly_expenses.month DESC", sql)

    def test_unfiltered_list_keeps_months_grouped_and_sorts_each_month_newest_first(self):
        db = _RecordingDb()

        monthly_expenses.list_monthly_expenses(None, db)

        sql = " ".join(str(db.queries[0]).split())
        self.assertIn(
            "ORDER BY monthly_expenses.month DESC, "
            "monthly_expenses.created_at DESC, monthly_expenses.id DESC",
            sql,
        )


if __name__ == "__main__":
    unittest.main()
