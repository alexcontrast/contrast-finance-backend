import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.api.routes import self_employed_accounting as accounting
from app.services import self_employed_identity_lookup as lookup


class _RowsResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return self._rows


class _FakeDb:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def execute(self, _query):
        return _RowsResult(self.rows)

    def add(self, _value):
        return None


class AccountingIdentityLookupV0118Tests(unittest.TestCase):
    def test_business_analyst_text_extracts_full_name(self):
        text = (
            "ИП БЕРНИК Н.А. ИИН:890913450337 Общая информация "
            "Руководитель компании БЕРНИК НИНА АНДРЕЕВНА "
            "Проверено: Национальное бюро статистики"
        )
        self.assertEqual(
            lookup._extract_name(text, "890913450337"),
            "БЕРНИК НИНА АНДРЕЕВНА",
        )

    def test_adata_text_extracts_kazakh_full_name(self):
        text = (
            "БИН: 030218651232 Руководитель СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ "
            "Дата назначения руководителя 01.01.2026"
        )
        self.assertEqual(
            lookup._extract_name(text, "030218651232"),
            "СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ",
        )

    def test_local_history_wins_without_external_request(self):
        record = SimpleNamespace(
            id=99,
            iin="030919651322",
            contractor_full_name=None,
            ocr_text=None,
        )
        with patch.object(accounting, "_saved_contact", return_value=None), patch.object(
            accounting, "lookup_full_name_by_iin"
        ) as external:
            accounting._restore_receipt_identity(
                _FakeDb([(1, "030919651322", "АРХАРОВА АЛЁНА СЕРГЕЕВНА")]),
                record,
                allow_external=True,
            )
        self.assertEqual(record.contractor_full_name, "АРХАРОВА АЛЁНА СЕРГЕЕВНА")
        external.assert_not_called()

    def test_external_lookup_fills_missing_name_and_seeds_receipt_history(self):
        record = SimpleNamespace(
            id=99,
            iin="030218651232",
            contractor_full_name=None,
            ocr_text="[KASPI_QR] structured receipt",
        )
        result = lookup.ExternalIdentityResult(
            full_name="СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ",
            source="ba.prg.kz",
        )
        with patch.object(accounting, "_saved_contact", return_value=None), patch.object(
            accounting, "lookup_full_name_by_iin", return_value=result
        ) as external:
            accounting._restore_receipt_identity(
                _FakeDb([]),
                record,
                allow_external=True,
            )
        external.assert_called_once_with("030218651232")
        self.assertEqual(record.contractor_full_name, "СЕРІКБАЙ БЕКЗАТ НҰРЕИСАҰЛЫ")
        self.assertIn("[IIN_FIO_LOOKUP:ba.prg.kz]", record.ocr_text)


if __name__ == "__main__":
    unittest.main()
