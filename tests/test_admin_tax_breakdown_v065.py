import unittest
from decimal import Decimal
from pathlib import Path

from app.api.routes.admin_dashboard import finalize_monthly_tax_totals


class AdminTaxBreakdownV065Tests(unittest.TestCase):
    def test_breakdown_keeps_accrued_and_deductions_when_payable_is_zero(self):
        result = finalize_monthly_tax_totals(
            {
                "turnover": Decimal("1000000"),
                "client_vat": Decimal("120000"),
                "contractor_vat_credit": Decimal("150000"),
                "ip_contrast_tax": Decimal("50000"),
                "tax_deductions": Decimal("80000"),
            }
        )

        self.assertEqual(result["vat_accrued"], Decimal("120000.00"))
        self.assertEqual(result["vat_deductions"], Decimal("150000.00"))
        self.assertEqual(result["vat_to_pay"], Decimal("0.00"))
        self.assertEqual(result["tax_accrued"], Decimal("50000.00"))
        self.assertEqual(result["tax_deductions"], Decimal("80000.00"))
        self.assertEqual(result["tax_to_pay"], Decimal("0.00"))

    def test_positive_remainder_is_preserved(self):
        result = finalize_monthly_tax_totals(
            {
                "client_vat": Decimal("200000"),
                "contractor_vat_credit": Decimal("50000"),
                "ip_contrast_tax": Decimal("70000"),
                "tax_deductions": Decimal("10000"),
            }
        )

        self.assertEqual(result["vat_to_pay"], Decimal("150000.00"))
        self.assertEqual(result["tax_to_pay"], Decimal("60000.00"))

    def test_overview_exposes_hover_and_tap_breakdown(self):
        source = (Path(__file__).parents[1] / "app" / "web" / "app.js").read_text(encoding="utf-8")
        styles = (Path(__file__).parents[1] / "app" / "web" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("function overviewTaxBreakdownRow", source)
        self.assertIn('tabindex="0"', source)
        self.assertIn("company_vat_accrued_amount", source)
        self.assertIn("company_tax_deductions_amount", source)
        self.assertIn(".overview-finance-breakdown:hover .overview-tax-tooltip", styles)
        self.assertIn(".overview-finance-breakdown:focus .overview-tax-tooltip", styles)


if __name__ == "__main__":
    unittest.main()
