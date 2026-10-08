from unittest.mock import patch

import cache
from logic import TARJIMA_XATO, XATO_JAVOB, javob_tayyorla
from test_logic import tarjimonlar  # noqa: F401  (fixture)


# ---------- cache.py ----------
def test_saqla_va_ol():
    cache.saqla('en_uz', 'book', 'kitob')
    assert cache.ol('en_uz', 'book') == 'kitob'
    assert cache.soni() == 1


def test_yoq_bolsa_none():
    assert cache.ol('en_uz', 'yoq') is None


def test_yonalishlar_alohida():
    cache.saqla('en_uz', 'book', 'kitob')
    assert cache.ol('uz_en', 'book') is None


def test_qayta_saqlash_yangilaydi():
    cache.saqla('en_uz', 'book', 'eski')
    cache.saqla('en_uz', 'book', 'yangi')
    assert cache.ol('en_uz', 'book') == 'yangi'
    assert cache.soni() == 1


def test_fayldagi_baza_qayta_ochilganda_saqlanadi(tmp_path):
    yol = str(tmp_path / "kesh.db")
    cache.ochish(yol)
    cache.saqla('en_uz', 'book', 'kitob')
    cache.yopish()
    cache.ochish(yol)
    assert cache.ol('en_uz', 'book') == 'kitob'


def test_baza_xatosi_botni_yiqitmaydi():
    with patch("cache._baza", side_effect=Exception("disk xatosi")):
        assert cache.ol('en_uz', 'book') is None
        cache.saqla('en_uz', 'book', 'kitob')  # istisno ko'tarilmaydi
        assert cache.soni() == 0


# ---------- logic bilan birgalikda ----------
def test_ikkinchi_marta_tarjimonlar_chaqirilmaydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "kitob"

    assert javob_tayyorla("book") == "🇬🇧 book → 🇺🇿 kitob"
    assert javob_tayyorla("book") == "🇬🇧 book → 🇺🇿 kitob"

    assert g.return_value.translate.call_count == 1


def test_katta_kichik_harf_bir_xil_kesh(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "kitob"
    javob_tayyorla("book")
    assert javob_tayyorla("BOOK") == "🇬🇧 BOOK → 🇺🇿 kitob"
    assert g.return_value.translate.call_count == 1


def test_tarjimonlar_ishlamasa_ham_keshdan_javob(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "kitob"
    javob_tayyorla("book")

    g.return_value.translate.side_effect = Exception("internet yo'q")
    m.return_value.translate.side_effect = Exception("internet yo'q")
    assert javob_tayyorla("book") == "🇬🇧 book → 🇺🇿 kitob"


def test_xato_tarjima_keshlanmaydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.side_effect = Exception("xato")
    m.return_value.translate.side_effect = Exception("xato")
    assert javob_tayyorla("book") == TARJIMA_XATO
    assert cache.soni() == 0


def test_notogri_soz_keshlanmaydi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "salom"
    m.return_value.translate.return_value = "salom"
    assert javob_tayyorla("salom") == XATO_JAVOB
    assert cache.soni() == 0


def test_yonalish_boyicha_alohida_keshlanadi(tarjimonlar):
    g, m = tarjimonlar
    g.return_value.translate.return_value = "kitob"
    javob_tayyorla("book", 'en_uz')
    g.return_value.translate.return_value = "book"
    assert javob_tayyorla("kitob", 'uz_en') == "🇺🇿 kitob → 🇬🇧 book"


def test_birinchi_chaqiruvda_baza_ochilishi_osilib_qolmaydi(tmp_path, monkeypatch):
    """Haqiqiy botda baza birinchi so'rovda ochiladi; bu paytda kesh osilib qolmasligi kerak."""
    import threading

    cache.yopish()
    monkeypatch.setattr(cache, "DB_YOLI", str(tmp_path / "yangi.db"))
    natija = {}

    def ish():
        natija['ol'] = cache.ol('en_uz', 'book')
        cache.saqla('en_uz', 'book', 'kitob')
        natija['soni'] = cache.soni()

    oqim = threading.Thread(target=ish, daemon=True)
    oqim.start()
    oqim.join(timeout=5)
    assert not oqim.is_alive(), "kesh osilib qoldi (deadlock)"
    assert natija == {'ol': None, 'soni': 1}
