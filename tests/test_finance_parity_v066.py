"""Run the actual JS preview against the Decimal server calculator."""
import json
from pathlib import Path
import random
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from decimal import Decimal
from app.models.event import Event
from app.models.event_item import EventItem
from app.services import event_calculator as calculator


class PreviewParityTests(unittest.TestCase):
    def test_preview_matches_server_for_payment_modes_rates_and_rounding(self):
        root=Path(__file__).parents[1]
        rng=random.Random(6615)
        cases=[];expected=[]
        for index in range(120):
            rates={"vat_rate":Decimal("0.16"),"contrast_internal_tax_rate":Decimal("0.12"),
                "simplified_tax_rate":Decimal("0.05"),"contractor_deduction_rate":Decimal("0.10")}
            if index>=80:
                rates.update(vat_rate=Decimal("0.18"),contrast_internal_tax_rate=Decimal("0.11"),
                    simplified_tax_rate=Decimal("0.06"),contractor_deduction_rate=Decimal("0.09"))
            event=dict(client_calc_type=["cash","ip_contrast_event","our_no_vat","simplified"][index%4],
                manager_percent=[0,21,33.33,100][index%4],agency_commission_amount=[0,5,7.5][index%3],
                simplified_bank_tax_percent=[0,3.5,5][index%3])
            rows=[]
            for n in range(4):
                price=Decimal(rng.randrange(10000,100000000))/100
                quantity=1+n%2;days=1
                external=(price*quantity*days).quantize(Decimal('.01'))
                method=["cash","card","self_employed","invoice"][n]
                fact=[None,Decimal('0'),Decimal('12345.50'),external/2][(index+n)%4]
                rows.append(dict(item_type="regular",external_name="Test",external_price=price,
                    external_quantity=quantity,external_days=days,external_amount=external,
                    amount_fact=fact,paid_amount=0,payment_method=method,
                    vat_amount=Decimal('1111.50') if method=='invoice' else 0,
                    deduction_amount=Decimal('2222.50') if method=='invoice' else 0))
            rows.append(dict(item_type="coordinator",external_name="Координатор",external_price=100001,
                external_quantity=1,external_days=1,external_amount=100001,amount_fact=50000,
                paid_amount=0,payment_method=None,vat_amount=0,deduction_amount=0))
            settings=SimpleNamespace(**{key.upper():value for key,value in rates.items()})
            with patch.object(calculator,"get_settings",return_value=settings):
                expected.append(calculator.calculate_event_summary_values(Event(**event),[EventItem(**row) for row in rows]))
            cases.append(dict(event=event,items=rows,economics=rates))
        actual=json.loads(subprocess.check_output(['node',str(root/'tests/finance-preview.cjs'),str(root)],
            input=json.dumps(cases,default=str).encode(),cwd=root))
        fields=('external_total','turnover_with_vat','agency_commission_amount','client_vat_amount',
            'contractor_vat_credit','deductions_total','taxes_total','taxes_net','tax_base_amount',
            'vat_to_pay','vat_net','regular_positions_commission','total_commission_amount',
            'manager_percent','manager_salary','coordinator_company_share','final_company_income',
            'tax_rate_percent','simplified_bank_tax_amount')
        for i,(server,preview) in enumerate(zip(expected,actual)):
            for field in fields:
                with self.subTest(case=i,field=field):
                    self.assertEqual(Decimal(str(preview[field])).quantize(Decimal('.01')),server[field])
