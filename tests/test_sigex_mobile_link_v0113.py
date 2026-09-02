from unittest.mock import patch

import pytest

from app.services.sigex_signing import SigexError, direct_egov_mobile_url


@patch("app.services.sigex_signing._base_url", return_value="https://sigex.kz")
def test_converts_current_egov_web_launcher_to_direct_app_scheme(_base_url):
    source = (
        "https://m.egov.kz/mobileSign/"
        "?link=https://sigex.kz/api/egovQr/egov/AbC123?mgovSign"
    )

    assert direct_egov_mobile_url(source) == (
        "mobileSign:https://sigex.kz/api/egovQr/egov/AbC123"
    )


@patch("app.services.sigex_signing._base_url", return_value="https://sigex.kz")
def test_keeps_valid_direct_app_scheme(_base_url):
    source = "mobileSign:https://sigex.kz/api/egovQr/egov/AbC123"
    assert direct_egov_mobile_url(source) == source


@patch("app.services.sigex_signing._base_url", return_value="https://sigex.kz")
@pytest.mark.parametrize(
    "source",
    [
        "https://apps.apple.com/kz/app/egov-mobile/id1476128386",
        "https://m.egov.kz/mobileSign/?link=https://evil.example/sign",
        "https://m.egov.kz/mobileSign/",
    ],
)
def test_rejects_store_foreign_or_incomplete_launch_links(_base_url, source):
    with pytest.raises(SigexError):
        direct_egov_mobile_url(source)
