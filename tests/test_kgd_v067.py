"""Offline KGD response contract and concurrency regressions."""
from types import SimpleNamespace
from unittest.mock import patch
from threading import Barrier
import pytest
from app.services.kgd import client as kgd

BIN = '770100000001'
SETTINGS = SimpleNamespace(KGD_API_KEY='isolated-token', KGD_BASE_URL='https://isolated.invalid')

def response(body=None, ok=True):
    return dict(ok=ok, body=body, status_code=200 if ok else 503, label='KGD test', error=None if ok else 'unavailable',elapsed_sec=0.01)

def live(snr, vat, primary=None):
    def fetch(label, url, headers, **kwargs):
        if 'get-sur-data' in url: return primary if primary is not None else response({})
        return snr if 'snr-search' in url else vat
    with patch.object(kgd,'get_settings',return_value=SETTINGS), patch.object(kgd,'_fetch_json',side_effect=fetch):
        return kgd.check_taxpayer_live(BIN)

@pytest.mark.parametrize('bad',[
    response(ok=False), response({'error':'database unavailable'}),
    response({'success':False,'message':'error'}), response({'message':'Unauthorized'}),
    response({'status':'error','data':None}), response({'foo':'bar'}),
])
def test_snr_failure_never_becomes_not_found_or_valid_regime(bad):
    with pytest.raises(kgd.KgdServiceError): live(bad,response([]))

def test_vat_failure_never_becomes_our_without_vat():
    with pytest.raises(kgd.KgdServiceError): live(response({'type':'SNR_GENERAL_ORDER'}),response(ok=False))

def test_known_simplified_does_not_require_vat_lookup_success():
    result=live(response({'type':'SNR_SIMPLIFIED'}),response(ok=False))
    assert result.tax_status=='simplified'
    assert result.vat_credit_allowed is False

@pytest.mark.parametrize('empty',[[],{},None])
def test_successful_empty_snr_is_explicit_not_found(empty):
    result=live(response(empty),response([]))
    assert result.tax_status=='not_found'
    assert 'не нашёл' in result.message

def test_fallback_can_succeed_if_primary_is_temporarily_unavailable():
    result=live(response({'type':'SNR_GENERAL_ORDER','taxpayerName':'Test'}),response({'registrationDate':'2025-01-01'}),response(ok=False))
    assert result.tax_status=='our_vat'
    assert result.contractor_name=='Test'

def test_wrapped_result_is_unwrapped_before_classification():
    result=live(response({'success':True,'data':{'type':'SNR_GENERAL_ORDER'}}),response({'data':[]}))
    assert result.tax_status=='our_no_vat'

@pytest.mark.parametrize('body',[
    {'error':'unavailable','taxMode':{'ru':'ОУР'},'vatInfo':{'ru':'Без НДС'}},
    {'success':False,'taxMode':{'ru':'Упрощенка'}},
])
def test_primary_error_is_not_trusted_even_with_tax_fields(body):
    assert kgd._detect_open_data_result(body,BIN) is None

def test_unified_success_avoids_all_fallback_requests():
    with patch.object(kgd,'get_settings',return_value=SETTINGS),patch.object(kgd,'_fetch_json',return_value=response({'xin':BIN,'name':{'ru':'Test'},'taxMode':{'ru':'ОУР'},'vatInfo':{'ru':'Без НДС'}})) as fetch:
        result=kgd.check_taxpayer_live(BIN)
    assert result.tax_status=='our_no_vat'
    assert fetch.call_count==1

def test_fallback_reads_really_run_concurrently():
    barrier=Barrier(2,timeout=2)
    def fetch(label,url,headers,**kwargs):
        if 'get-sur-data' in url: return response({})
        barrier.wait()
        return response({'type':'SNR_GENERAL_ORDER'}) if 'snr-search' in url else response([])
    with patch.object(kgd,'get_settings',return_value=SETTINGS),patch.object(kgd,'_fetch_json',side_effect=fetch):
        assert kgd.check_taxpayer_live(BIN).tax_status=='our_no_vat'


def test_wrapped_primary_success_does_not_fall_back():
    body={'success':True,'data':{'xin':BIN,'taxMode':{'ru':'ОУР'},'vatInfo':{'ru':'Без НДС'}}}
    with patch.object(kgd,'get_settings',return_value=SETTINGS),patch.object(kgd,'_fetch_json',return_value=response(body)) as fetch:
        assert kgd.check_taxpayer_live(BIN).tax_status=='our_no_vat'
    assert fetch.call_count==1


def test_http_200_numeric_error_is_not_a_regime():
    with pytest.raises(kgd.KgdServiceError): live(response({'code':503,'message':'unavailable'}),response([]))


def test_response_for_another_taxpayer_is_rejected():
    with pytest.raises(kgd.KgdServiceError): live(response({'xin':'770100000002','type':'SNR_GENERAL_ORDER'}),response([]))
