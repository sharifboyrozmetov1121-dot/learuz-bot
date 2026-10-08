from unittest.mock import patch

import pytest

from logic import (
    TARJIMA_XATO,
    XATO_JAVOB,
    YONALISHLAR,
    inglizcha_mi,
    javob_tayyorla,
    kirill_lotin,
    matn_togri_mi,
    tarjima_qil,
)

XATO_UZ = YONALISHLAR['uz_en']['xato']


@pytest.fixture
def tarjimonlar():
    """Google va MyMemory soxtalashtiriladi (internet kerak emas)."""
    with patch("logic.TARJIMONLAR", ()), \
         patch("logic.GoogleTranslator") as g, patch("logic.MyMemoryTranslator") as m:
        import logic
        logic.TARJIMONLAR = (g, m)
        g.__name__ = "GoogleTranslator"
        m.__name__ = "MyMemoryTranslator"
        logic._bloklangan.clear()
        yield g, m
        logic._bloklangan.clear()


# ---------- inglizcha_mi ----------
@pytest.mark.parametrize("soz", [
    "apple", "Apple", "APPLE", "book", "happy", "apples", "played",
    "running", "stopped", "babies", "making",
])
def test_inglizcha_soz_taniladi(soz):
    assert inglizcha_mi(soz) is True


@pytest.mark.parametrize("soz", ["olma", "salom", "kitob", "asdfgh"])
def test_notogri_soz_taniladi(soz):
    assert inglizcha_mi(soz) is False


# ---------- matn_togri_mi ----------
@pytest.mark.parametrize("matn", [
    "apple", "good morning", "well-known", "olma", "o'quvchi", "o‘quvchi",
])
def test_togri_matn(matn):
    assert matn_togri_mi(matn) is True


@pytest.mark.parametrize("matn", ["", " ", "123", "apple1", "apple!", "яблоко", "😀", "'", "-"])
def test_notogri_matn(matn):
    assert matn_togri_mi(matn) is False


# ---------- kirill_lotin ----------
@pytest.mark.parametrize("kirill, lotin", [
    ("олма", "olma"),
    ("ўқитувчи", "o'qituvchi"),
    ("Ғалаба", "G'alaba"),
    ("яхши", "yaxshi"),
    ("hello", "hello"),
])
def test_kirill_lotin(kirill, lotin):
    assert kirill_lotin(kirill) == lotin


# ---------- tarjima ----------
def test_chiroyli_format(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "olma"
    assert javob_tayyorla("apple") == "🇬🇧 apple → 🇺🇿 olma"


def test_bosh_joylar_olib_tashlanadi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "olma"
    assert javob_tayyorla("  apple  ") == "🇬🇧 apple → 🇺🇿 olma"
    g.return_value.translate.assert_called_with("apple")


def test_avval_google_ishlatiladi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "olma"
    javob_tayyorla("apple")
    g.assert_called_with(source='english', target='uzbek')
    m.assert_not_called()


def test_google_ishlamasa_mymemory(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.side_effect = Exception("TooManyRequests")
    m.return_value.translate.return_value = "olma"
    assert javob_tayyorla("apple") == "🇬🇧 apple → 🇺🇿 olma"
    m.assert_called_with(source='english', target='uzbek')


def test_ikkalasi_ishlamasa_xabar(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.side_effect = Exception("xato")
    m.return_value.translate.side_effect = Exception("xato")
    assert javob_tayyorla("apple") == TARJIMA_XATO


def test_mymemory_limit_ogohlantirishi_tarjima_emas(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.side_effect = Exception("xato")
    m.return_value.translate.return_value = "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS"
    assert javob_tayyorla("apple") == TARJIMA_XATO


def test_google_bosh_qaytarsa_mymemory(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = None
    m.return_value.translate.return_value = "olma"
    assert javob_tayyorla("apple") == "🇬🇧 apple → 🇺🇿 olma"


def test_kirillcha_natija_lotinga_ogiriladi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "олма"
    assert javob_tayyorla("apple") == "🇬🇧 apple → 🇺🇿 olma"


def test_uz_en_yonalishi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "apple"
    assert javob_tayyorla("olma", 'uz_en') == "🇺🇿 olma → 🇬🇧 apple"
    g.assert_called_with(source='uzbek', target='english')


def test_nomalum_yonalish_standartga_qaytadi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "olma"
    assert javob_tayyorla("apple", 'xx_yy') == "🇬🇧 apple → 🇺🇿 olma"


def test_ozbekcha_soz_en_uz_da_xato(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "olma"  # tarjimonlar so'zni o'zgartirmadi
    m.return_value.translate.return_value = "olma"
    assert javob_tayyorla("olma") == XATO_JAVOB


def test_tanish_inglizcha_soz_bir_xil_tarjima_togri(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "radio"
    m.return_value.translate.return_value = "radio"
    assert javob_tayyorla("radio") == "🇬🇧 radio → 🇺🇿 radio"


@pytest.mark.parametrize("matn", [None, "", "   ", "12345", "яблоко", "apple!"])
def test_notogri_kirish_tarjimonni_chaqirmaydi(tarjimonlar, matn):
    g, m = tarjimonlar
    assert javob_tayyorla(matn) == XATO_JAVOB
    assert javob_tayyorla(matn, 'uz_en') == XATO_UZ
    g.assert_not_called()
    m.assert_not_called()


def test_uz_en_tarjima_bir_xil_bolsa_xato(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "asdfg"
    m.return_value.translate.return_value = "asdfg"
    assert javob_tayyorla("asdfg", 'uz_en') == XATO_UZ


# ---------- tarjima_qil (talaffuz tarjima qilingan so'zni o'qiydi) ----------
def test_en_uz_talaffuz_ozbekcha_tarjimani_oqiydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "kitob"
    n = tarjima_qil("book", 'en_uz')
    assert (n.ok, n.talaffuz_soz, n.talaffuz_tili) == (True, "kitob", "uz")


def test_uz_en_talaffuz_inglizcha_tarjimani_oqiydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "book"
    n = tarjima_qil("kitob", 'uz_en')
    assert (n.ok, n.talaffuz_soz, n.talaffuz_tili) == (True, "book", "en")


def test_tarjima_qil_xatoda_qoshimcha_malumot_yoq(tarjimonlar):
    assert tarjima_qil("123", 'en_uz') == (False, XATO_JAVOB, None, None)


# ---------- talaffuz uchun matnni tozalash ----------
from logic import talaffuz_uchun_tozala  # noqa: E402


@pytest.mark.parametrize("kirish, kutilgan", [
    ("apple", "apple"),
    ("Apple.", "Apple"),
    ('"hello!"', "hello"),
    ("  good morning, ", "good morning"),
    ("...", None),
    ("", None),
    (None, None),
])
def test_talaffuz_uchun_tozala(kirish, kutilgan):
    assert talaffuz_uchun_tozala(kirish) == kutilgan


def test_uz_en_natijadagi_nuqta_talaffuzga_otmaydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "Apple."
    n = tarjima_qil("olma", 'uz_en')
    assert n.ok is True
    assert n.talaffuz_soz == "Apple"


# ---------- limitga tushgan tarjimonni vaqtincha o'tkazib yuborish ----------
class TooManyRequests(Exception):
    pass


def test_limitga_tushgan_google_keyingi_safar_chaqirilmaydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.side_effect = TooManyRequests()
    m.return_value.translate.return_value = "olma"

    assert javob_tayyorla("apple") == "🇬🇧 apple → 🇺🇿 olma"
    assert javob_tayyorla("book") == "🇬🇧 book → 🇺🇿 olma"  # boshqa so'z: keshdan emas

    assert g.return_value.translate.call_count == 1  # ikkinchi marta Google chaqirilmadi
    assert m.return_value.translate.call_count == 2


def test_oddiy_xato_qisqa_muddatga_bloklaydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.side_effect = Exception("tarmoq xatosi")
    m.return_value.translate.return_value = "olma"

    javob_tayyorla("apple")
    javob_tayyorla("book")
    assert g.return_value.translate.call_count == 1  # 30 soniya ichida qayta urinilmaydi


def test_blok_vaqti_otgach_google_qayta_ishlatiladi(tarjimonlar):
    import logic
    g, m = tarjimonlar
    g.return_value.translate.side_effect = TooManyRequests()
    m.return_value.translate.return_value = "olma"
    javob_tayyorla("apple")

    with patch("logic.time.monotonic", return_value=logic.time.monotonic() + 11 * 60):
        g.return_value.translate.side_effect = None
        g.return_value.translate.return_value = "olma"
        javob_tayyorla("book")  # boshqa so'z: keshdan emas

    assert g.return_value.translate.call_count == 2


# ---------- tarjimon so'zni o'zgartirmasa keyingisi sinab ko'riladi ----------
def test_bir_xil_javob_bersa_keyingi_tarjimon_sinaladi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "apple"   # tarjima qilmadi
    m.return_value.translate.return_value = "olma"
    assert javob_tayyorla("apple") == "🇬🇧 apple → 🇺🇿 olma"


def test_hamma_bir_xil_qaytarsa_notanish_soz_xato(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "salom"
    m.return_value.translate.return_value = "salom"
    assert javob_tayyorla("salom") == XATO_JAVOB


# ---------- tarjimondan kelgan HTML belgilari va apostroflar ----------
def test_html_belgilari_tozalanadi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "noto&#39;g&#39;ri &quot;yo&#39;l&quot;"
    assert javob_tayyorla("wrong") == "🇬🇧 wrong → 🇺🇿 noto'g'ri \"yo'l\""


def test_burama_apostrof_oddiyga_almashtiriladi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "o‘quvchi"
    assert javob_tayyorla("student") == "🇬🇧 student → 🇺🇿 o'quvchi"
