import unittest
from pathlib import Path


class AccountingSignaturePollV0117Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("app/web/app.js").read_text(encoding="utf-8")

    def test_filters_are_split_by_party(self):
        self.assertIn('value="no_ip_signature"', self.source)
        self.assertIn('>Не подписано ИП</option>', self.source)
        self.assertIn('value="no_sz_signature"', self.source)
        self.assertIn('>Не подписано СЗ</option>', self.source)
        self.assertNotIn('value="unsigned"', self.source)

    def test_polling_does_not_require_local_sent_state(self):
        start = self.source.index("async function pollAccountingSignatureChanges")
        end = self.source.index("async function pollLiveEventChanges", start)
        block = self.source[start:end]
        self.assertIn('Boolean(row?.has_act)', block)
        self.assertIn('String(row.customer_signature?.status || "") !== "signed"', block)
        self.assertIn('String(row.contractor_signature?.status || "") !== "signed"', block)
        self.assertNotIn('["sent", "signing"].includes(String(row.customer_signature', block)
        self.assertIn('await refreshAccountingRow(row.accounting_id)', block)

    def test_signed_badge_still_uses_row_scoped_refresh(self):
        self.assertIn('const statusClass = status === "signed"', self.source)
        self.assertIn('? "is-signed"', self.source)
        self.assertIn('existingEl.replaceWith(node)', self.source)


if __name__ == "__main__":
    unittest.main()
