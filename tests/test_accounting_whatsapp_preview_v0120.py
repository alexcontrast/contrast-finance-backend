import unittest
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.api.routes import act_signing


class AccountingWhatsappPreviewV0121Tests(unittest.TestCase):
    def _record(self, **overrides):
        values = {
            "contractor_full_name": "СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ",
            "receipt_amount": Decimal("150000.00"),
            "act_date": date(2026, 9, 3),
            "receipt_datetime": datetime(2026, 9, 3, 14, 20),
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_share_preview_title_uses_surname_first_name_amount_and_date(self):
        self.assertEqual(
            act_signing._share_preview_title(self._record()),
            "АВР Contrast-Серікбай Бекзат на сумму 150 000 ₸ от 03.09.2026",
        )

    def test_share_preview_title_keeps_fractional_tenge(self):
        self.assertEqual(
            act_signing._share_preview_title(self._record(receipt_amount=Decimal("150000.50"))),
            "АВР Contrast-Серікбай Бекзат на сумму 150 000,50 ₸ от 03.09.2026",
        )

    def test_public_page_exposes_dynamic_title_and_open_graph(self):
        token = "A" * 32
        record = self._record(contractor_full_name='ИВАНОВ ИВАН ИВАНОВИЧ')
        with patch.object(act_signing, "_record_by_token", return_value=record):
            response = act_signing.act_signing_page(token, db=object())
        html = response.body.decode("utf-8")
        expected = "АВР Contrast-Иванов Иван на сумму 150 000 ₸ от 03.09.2026"
        self.assertIn(f"<title>{expected}</title>", html)
        self.assertIn(f'<meta property="og:title" content="{expected}" />', html)
        self.assertNotIn("{{AVR_SHARE_TITLE}}", html)
        self.assertNotIn("Подписание АВР · Contrast", html)
        self.assertNotIn("Иванович", html)


if __name__ == "__main__":
    unittest.main()
