import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.api.routes import payment_requests, tax
from app.services.event_calculator import item_deduction


class _FakeDb:
    def add(self, _value):
        return None


def self_employed_item(fact, *, external=Decimal("100000.00"), stored=Decimal("10000.00")):
    return SimpleNamespace(
        item_type="regular",
        payment_method="self_employed",
        amount_fact=fact,
        external_amount=external,
        deduction_amount=stored,
        iin_bin=None,
        iin_bin_locked=False,
        tax_check_status="self_employed",
        vat_amount=Decimal("0.00"),
        internal_note=None,
        updated_at=None,
    )


class SelfEmployedDeductionV061Tests(unittest.TestCase):
    def test_zero_fact_never_falls_back_to_external_estimate(self):
        item = self_employed_item(Decimal("0.00"))

        self.assertEqual(item_deduction(item), Decimal("0.00"))
        self.assertEqual(tax.get_amount_base(item, "self_employed"), Decimal("0.00"))

        payload = SimpleNamespace(self_employed_surname="Иванов", comment=None)
        with patch.object(payment_requests, "validate_payment_method_lock", return_value=None):
            payment_requests.apply_payment_context_to_item(_FakeDb(), item, "self_employed", payload)
        self.assertEqual(item.deduction_amount, Decimal("0.00"))

    def test_missing_fact_has_zero_deduction(self):
        item = self_employed_item(None)
        self.assertEqual(item_deduction(item), Decimal("0.00"))
        self.assertEqual(tax.get_amount_base(item, "self_employed"), Decimal("0.00"))

    def test_partial_and_full_fact_use_exactly_ten_percent(self):
        partial = self_employed_item(Decimal("40000.00"), stored=Decimal("99999.00"))
        full = self_employed_item(Decimal("100000.00"), stored=Decimal("1.00"))

        self.assertEqual(item_deduction(partial), Decimal("4000.00"))
        self.assertEqual(item_deduction(full), Decimal("10000.00"))

    def test_browser_uses_fact_only_for_self_employed_deduction(self):
        source = (Path(__file__).parents[1] / "app" / "web" / "app.js").read_text(encoding="utf-8")
        start = source.index("function selfEmployedDeductionBase(item)")
        end = source.index("\n}\n", start) + 2
        helper = source[start:end]

        self.assertIn("return fact > 0 ? fact : 0;", helper)
        self.assertNotIn("externalRowAmount", helper)
        self.assertNotIn("external_amount", helper)

    def test_telegram_self_employed_path_does_not_fall_back_to_estimate(self):
        source = (Path(__file__).parents[1] / "app" / "telegram_bot" / "main.py").read_text(encoding="utf-8")
        marker = 'elif method == "self_employed":'
        start = source.rindex(marker)
        end = source.index('elif method in {"card", "cash"}:', start)
        branch = source[start:end]

        self.assertIn('else Decimal("0.00")', branch)
        self.assertNotIn("else item.external_amount", branch)


if __name__ == "__main__":
    unittest.main()
