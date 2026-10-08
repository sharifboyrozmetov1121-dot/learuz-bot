from unittest.mock import patch

import pytest

from audio import talaffuz_yarat, uzbek_matnini_turkchaga
from keyboards import natija_klaviaturasi


def _tugmalar(kb):
    return [b.callback_data for row in kb.inline_keyboard for b in row]


def test_talaffuz_tugmasi_inglizcha():
    assert "tts:en:apple" in _tugmalar(natija_klaviaturasi("apple", "en"))


def test_ozbekcha_natijada_talaffuz_tugmasi_yoq():
    data = _tugmalar(natija_klaviaturasi("kitob", "uz"))
    assert not any(d.startswith("tts:") for d in data)
    assert "dir:toggle" in data


def test_talaffuz_tugmasi_yoq_soz_bolmasa():
    data = _tugmalar(natija_klaviaturasi(None))
    assert not any(d.startswith("tts:") for d in data)
    assert "dir:toggle" in data


def test_uzun_matnda_talaffuz_tugmasi_qoyilmaydi():
    assert not any(d.startswith("tts:") for d in _tugmalar(natija_klaviaturasi("a" * 80, "en")))


@pytest.mark.parametrize("uz, turk", [
    ("kitob", "kitob"),
    ("yaxshi", "yahşi"),
    ("o'quvchi", "okuvçi"),
    ("O‘quvchi", "okuvçi"),
    ("g'alaba", "ğalaba"),
    ("jo'ja", "coca"),
])
def test_ozbekcha_turkchaga_moslashtirish(uz, turk):
    assert uzbek_matnini_turkchaga(uz) == turk


@patch("audio.gTTS")
def test_inglizcha_talaffuz(mock_gtts):
    mock_gtts.return_value.write_to_fp.side_effect = lambda fp: fp.write(b"mp3data")
    buf = talaffuz_yarat("apple")
    mock_gtts.assert_called_with(text="apple", lang="en")
    assert buf.read() == b"mp3data"


@patch("audio.gTTS")
def test_ozbekcha_talaffuz_turkcha_ovozda(mock_gtts):
    mock_gtts.return_value.write_to_fp.side_effect = lambda fp: fp.write(b"mp3data")
    talaffuz_yarat("yaxshi", "uz")
    mock_gtts.assert_called_with(text="yahşi", lang="tr")


def test_talaffuz_va_yonalish_tugmalari():
    data = _tugmalar(natija_klaviaturasi("apple", "en"))
    assert data == ["tts:en:apple", "dir:toggle"]
