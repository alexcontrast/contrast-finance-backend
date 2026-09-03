import inspect
import unittest
from pathlib import Path

from app.api.routes import self_employed_accounting as accounting


class AccountingReceiptOnlyV0116Tests(unittest.TestCase):
    def test_list_is_receipt_only(self):
        source = inspect.getsource(accounting.list_self_employed_accounting)
        self.assertIn("SelfEmployedAccounting.receipt_filename.is_not(None)", source)
        self.assertNotIn("PaymentRequest.payment_method", source)
        self.assertIn("build_row([], record)", source)

    def test_new_import_does_not_auto_match_requests(self):
        source = inspect.getsource(accounting.import_self_employed_receipt)
        self.assertNotIn("_auto_match_receipt", source)
        self.assertIn("create_standalone_record", source)
        self.assertIn('match_status = "unmatched"', source)

    def test_single_receipt_endpoint_exists(self):
        paths = {
            route.path
            for route in __import__("app.main", fromlist=["app"]).app.routes
            if getattr(route, "path", None)
        }
        self.assertIn("/accounting/self-employed/receipts/{accounting_id}", paths)

    def test_frontend_actions_are_in_place(self):
        source = Path("app/web/app.js").read_text(encoding="utf-8")
        start = source.index("async function saveAccountingEditor")
        end = source.index("async function openAccountingReceipt", start)
        self.assertNotIn("loadSelfEmployedAccounting(true)", source[start:end])
        start = source.index("async function importAccountingBatchFiles")
        end = source.index("async function attachAccountingRowToReceipt", start)
        self.assertNotIn('dashboardContent").innerHTML = renderAccountingPanel()', source[start:end])
        self.assertIn("accountingReplaceRow(result.row)", source[start:end])

    def test_status_filters_are_present(self):
        source = Path("app/web/app.js").read_text(encoding="utf-8")
        self.assertIn('value="no_act"', source)
        self.assertIn('value="no_ip_signature"', source)
        self.assertIn('value="no_sz_signature"', source)
        self.assertNotIn('value="unsigned"', source)


if __name__ == "__main__":
    unittest.main()
