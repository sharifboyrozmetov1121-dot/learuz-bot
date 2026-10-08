from unittest.mock import MagicMock, patch

import pytest

from providers import GoogleGtxTranslator, LingvaTranslator, TooManyRequests


def javob(status=200, data=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = data
    r.raise_for_status.side_effect = None if status < 400 else Exception(f"HTTP {status}")
    return r


@patch("providers.requests.get")
def test_gtx_tarjima_oqiladi(mock_get):
    mock_get.return_value = javob(data=[[["olma", "apple", None, None, 10]], None, "en"])
    assert GoogleGtxTranslator("english", "uzbek").translate("apple") == "olma"
    params = mock_get.call_args.kwargs["params"]
    assert (params["sl"], params["tl"], params["q"]) == ("en", "uz", "apple")


@patch("providers.requests.get")
def test_gtx_bir_necha_qism_birlashadi(mock_get):
    mock_get.return_value = javob(data=[[["Xayrli ", "Good ", 0], ["tong", "morning", 0]]])
    assert GoogleGtxTranslator("english", "uzbek").translate("Good morning") == "Xayrli tong"


@patch("providers.requests.get")
def test_gtx_limit(mock_get):
    mock_get.return_value = javob(status=429)
    with pytest.raises(TooManyRequests):
        GoogleGtxTranslator("english", "uzbek").translate("apple")


@patch("providers.requests.get")
def test_lingva_birinchi_server_ishlamasa_ikkinchisi(mock_get):
    mock_get.side_effect = [Exception("ulanib bo'lmadi"), javob(data={"translation": "olma"})]
    assert LingvaTranslator("english", "uzbek").translate("apple") == "olma"
    assert mock_get.call_count == 2


@patch("providers.requests.get")
def test_lingva_hamma_server_ishlamasa_xato(mock_get):
    mock_get.side_effect = Exception("ulanib bo'lmadi")
    with pytest.raises(Exception):
        LingvaTranslator("english", "uzbek").translate("apple")
