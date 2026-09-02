import json
import unittest
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes import payment_requests
from app.api.routes import self_employed_accounting as accounting


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeDb:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def execute(self, _query):
        return _RowsResult(self.rows)

    def add(self, _value):
        return None


class AccountingReceiptV0108Tests(unittest.TestCase):
    def test_receipt_dates_include_kazakh_and_date_only(self):
        self.assertEqual(accounting._parse_report_datetime("28 тамыз 2026 ж."), datetime(2026, 8, 28))
        self.assertEqual(accounting._parse_report_datetime("2026 жылғы 28 тамыз, 13:36"), datetime(2026, 8, 28, 13, 36))
        self.assertEqual(accounting._parse_report_datetime("01.09.2026 12:52"), datetime(2026, 9, 1, 12, 52))

    def test_visual_header_date_repairs_ocr_confusables(self):
        self.assertEqual(
            accounting._parse_report_datetime("Чек №000000000011\nот 4 мая 2O26 г., 12.08"),
            datetime(2026, 5, 4, 12, 8),
        )
        self.assertEqual(
            accounting._parse_report_datetime("Дата и время по Астане O1.O9.2O26 12:52"),
            datetime(2026, 9, 1, 12, 52),
        )

    def test_import_metadata_recovers_date_from_visual_ocr(self):
        record = SimpleNamespace()
        accounting._apply_import_metadata(
            record,
            contractor_full_name=None,
            iin=None,
            receipt_number=None,
            receipt_datetime=None,
            service_name=None,
            receipt_amount=None,
            qr_payload=None,
            ocr_text="[DATE_HEADER] Чек №000000000011 от 4 мая 2O26 г., 12.08",
            parse_confidence="80",
        )
        self.assertEqual(record.receipt_datetime, datetime(2026, 5, 4, 12, 8))

    def test_undated_receipt_does_not_match_event_month(self):
        row = SimpleNamespace(has_receipt=True, receipt_datetime=None, event_date=date(2026, 9, 1))
        self.assertFalse(accounting._row_matches_accounting_month(row, (date(2026, 9, 1), date(2026, 10, 1))))

    def test_kazakh_name_and_strict_receipt_number(self):
        self.assertEqual(
            accounting.prefer_full_person_name(
                "БЕКБАУ БОТАГ ЖАНАТКЫЗЫ",
                "БЕКБАУ БОТАГӨЗ ЖАНАТҚЫЗЫ",
            ),
            "БЕКБАУ БОТАГӨЗ ЖАНАТҚЫЗЫ",
        )
        self.assertEqual(accounting.clean_receipt_number("2000000000033"), "000000000033")
        self.assertIsNone(accounting.clean_receipt_number("12345"))

    def test_russian_json_keys_are_legal_fields(self):
        parsed = accounting._parse_esalyq_json({
            "ИИН самозанятого": "030919651322",
            "ФИО самозанятого": "АРХАРОВА АЛЁНА СЕРГЕЕВНА",
            "Номер чека": "2000000000033",
            "receipt": {"date": "2026-08-28"},
            "responseCreatedAt": "2026-09-01T15:00:00",
        })
        self.assertEqual(parsed["iin"], "030919651322")
        self.assertEqual(parsed["contractor_full_name"], "АРХАРОВА АЛЁНА СЕРГЕЕВНА")
        self.assertEqual(parsed["receipt_number"], "000000000033")
        self.assertEqual(parsed["receipt_datetime"], datetime(2026, 8, 28))

    def test_kaspi_structured_receipt(self):
        values = [
            {"header": 15, "amount": 1, "cartItems": 2, "payParameters": 3},
            "200 000 ₸", [4], [6, 9, 12],
            {"item_name": 5}, "Деятельность художников, работающих индивидуально",
            {"name": 7, "value": 8}, "№ чека", "100034654911",
            {"name": 10, "value": 11}, "Дата и время по Астане", "01.09.2026 12:52",
            {"name": 13, "value": 14}, "ИИН самозанятого", "871030450396",
            "Чек самозанятого",
        ]
        source = '<script id="__NUXT_DATA__" type="application/json">' + json.dumps(values, ensure_ascii=False) + "</script>"
        parsed = accounting._parse_kaspi_receipt_html(source)
        self.assertEqual(parsed["iin"], "871030450396")
        self.assertEqual(parsed["receipt_number"], "100034654911")
        self.assertEqual(parsed["receipt_datetime"], datetime(2026, 9, 1, 12, 52))
        self.assertEqual(parsed["receipt_amount"], Decimal("200000.00"))

    def test_identity_recovery_is_unambiguous(self):
        record = SimpleNamespace(id=99, iin=None, contractor_full_name="АРХАРОВА АЛЁНА СЕРГЕЕВНА")
        with patch.object(accounting, "_saved_contact", return_value=None):
            accounting._restore_receipt_identity(
                _FakeDb([(1, "030919651322", "АРХАРОВА АЛЁНА СЕРГЕЕВНА")]),
                record,
            )
        self.assertEqual(record.iin, "030919651322")

    def test_special_payment_has_no_position_method_or_deductions(self):
        payload = SimpleNamespace(card_number=None, self_employed_surname="Архарова", comment=None)
        payment_requests.validate_manager_salary_payment_rules("self_employed", payload)
        with self.assertRaises(HTTPException):
            payment_requests.validate_manager_salary_payment_rules(
                "self_employed",
                SimpleNamespace(card_number=None, self_employed_surname="", comment=None),
            )
        item = SimpleNamespace(
            item_type="coordinator",
            payment_method="self_employed",
            iin_bin="123",
            iin_bin_locked=True,
            tax_check_status="self_employed",
            vat_amount=Decimal("50.00"),
            deduction_amount=Decimal("100.00"),
            updated_at=None,
        )
        payment_requests.apply_payment_context_to_item(_FakeDb(), item, "self_employed", payload)
        self.assertIsNone(item.payment_method)
        self.assertEqual(item.vat_amount, Decimal("0.00"))
        self.assertEqual(item.deduction_amount, Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()
