import html
import logging
import re
import time
from typing import NamedTuple, Optional

from deep_translator import GoogleTranslator, MyMemoryTranslator
from english_words import get_english_words_set

import cache
from providers import GoogleGtxTranslator, LingvaTranslator

# Inglizcha so'zlar ro'yxati
ENGLISH_WORDS = (
    get_english_words_set(['web2'], lower=True)
    | get_english_words_set(['gcide'], lower=True)
)

DEFAULT_YONALISH = 'en_uz'

YONALISHLAR = {
    'en_uz': {
        'source': 'english',
        'target': 'uzbek',
        'src_flag': '🇬🇧',
        'dst_flag': '🇺🇿',
        'tts_til': 'uz',
        'nom': "🇬🇧 English → 🇺🇿 O'zbekcha",
        'xato': "Siz noto'g'ri so'z kiritdingiz. Iltimos, inglizcha so'z yozing.",
    },
    'uz_en': {
        'source': 'uzbek',
        'target': 'english',
        'src_flag': '🇺🇿',
        'dst_flag': '🇬🇧',
        'tts_til': 'en',
        'nom': "🇺🇿 O'zbekcha → 🇬🇧 English",
        'xato': "Siz noto'g'ri so'z kiritdingiz. Iltimos, o'zbekcha so'z yozing.",
    },
}

XATO_JAVOB = YONALISHLAR['en_uz']['xato']
TARJIMA_XATO = "Tarjima qilishda xatolik yuz berdi. Birozdan keyin qayta urinib ko'ring."

# Tarjimonlar tartibi: biri ishlamasa (limit, tarmoq xatosi) keyingisi sinab ko'riladi
TARJIMONLAR = (GoogleTranslator, GoogleGtxTranslator, LingvaTranslator, MyMemoryTranslator)

KIRILL_LOTIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'ъ': "'", 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'ў': "o'", 'қ': 'q', 'ғ': "g'", 'ҳ': 'h',
}


def kirill_lotin(matn: str) -> str:
    """O'zbekcha kirill yozuvini lotinga o'giradi (tarjimon ba'zan kirillda qaytaradi)."""
    natija = []
    for ch in matn:
        kichik = ch.lower()
        if kichik in KIRILL_LOTIN:
            lotin = KIRILL_LOTIN[kichik]
            natija.append(lotin.capitalize() if ch != kichik else lotin)
        else:
            natija.append(ch)
    return ''.join(natija)


def apostrof_tuzat(matn: str) -> str:
    """o‘, g‘, oʻ kabi turli apostroflarni oddiy ' ga almashtiradi."""
    return matn.translate(str.maketrans({'ʻ': "'", '’': "'", '‘': "'", '`': "'", 'ʼ': "'"}))


def _asoslar(soz: str):
    """So'zning mumkin bo'lgan asosiy shakllari (ko'plik, -ing, -ed va h.k.)."""
    yield soz
    if soz.endswith('ies'):
        yield soz[:-3] + 'y'
    for q in ('s', 'es', 'ed', 'd', 'ing', 'er', 'est', 'ly'):
        if soz.endswith(q) and len(soz) > len(q) + 1:
            t = soz[:-len(q)]
            yield t
            yield t + 'e'
            if len(t) > 2 and t[-1] == t[-2]:
                yield t[:-1]


def inglizcha_mi(soz: str) -> bool:
    """So'z inglizcha ekanini tekshiradi (ko'plik va boshqa shakllari bilan)."""
    return any(asos in ENGLISH_WORDS for asos in _asoslar(soz.lower()))


def matn_inglizcha_mi(matn: str) -> bool:
    soz_lar = matn.replace('-', ' ').split()
    return bool(soz_lar) and all(inglizcha_mi(s) for s in soz_lar)


def matn_togri_mi(matn: str, yonalish: str = DEFAULT_YONALISH) -> bool:
    """Matn faqat lotin harflari, bo'shliq, tire va apostrofdan iboratmi."""
    matn = apostrof_tuzat(matn)
    if not re.fullmatch(r"[A-Za-z' -]+", matn):
        return False
    return any(ch.isalpha() for ch in matn)


# Xato bergan tarjimonni vaqtincha o'tkazib yuborish: {tarjimon: qaysi vaqtgacha}
_bloklangan = {}
LIMIT_BLOK_SONIYA = 10 * 60   # so'rovlar limiti: 10 daqiqa
XATO_BLOK_SONIYA = 30         # boshqa xato (tarmoq va h.k.): 30 soniya


def _tarjima_ol(matn: str, y: dict):
    """Tarjimonlarni ketma-ket sinaydi va birinchi haqiqiy tarjimani qaytaradi.

    Tarjimon so'zni o'zgartirmasdan qaytarsa, bu haqiqiy tarjima hisoblanmaydi:
    keyingi tarjimon sinab ko'riladi. Hech biri o'zgartira olmasa, shu bir xil
    natija qaytariladi (masalan, radio, taxi). Hech biri ishlamasa None.
    """
    zaxira = None
    for dvigatel in TARJIMONLAR:
        if time.monotonic() < _bloklangan.get(dvigatel, 0):
            continue  # yaqinda xato bergan, hozircha o'tkazib yuboramiz

        try:
            natija = dvigatel(source=y['source'], target=y['target']).translate(matn)
        except Exception as xato:
            if type(xato).__name__ == 'TooManyRequests':
                _bloklangan[dvigatel] = time.monotonic() + LIMIT_BLOK_SONIYA
                logging.warning("%s so'rovlar limitiga tushdi, bir muddat o'tkazib yuboriladi",
                                dvigatel.__name__)
            else:
                _bloklangan[dvigatel] = time.monotonic() + XATO_BLOK_SONIYA
                logging.warning("%s tarjima qila olmadi: %s", dvigatel.__name__, xato)
            continue

        if not natija or 'MYMEMORY WARNING' in natija.upper():
            continue
        # Tarjimonlar ba'zan HTML belgilari (&#39; &quot;) va turli apostroflar qaytaradi
        natija = apostrof_tuzat(html.unescape(natija))
        if natija.strip().lower() == matn.lower():
            zaxira = zaxira or natija
            continue
        return natija
    return zaxira


def talaffuz_uchun_tozala(matn: str):
    """Talaffuzga yuboriladigan matnning chetidagi nuqta, vergul, qo'shtirnoq kabilarni olib tashlaydi."""
    toza = re.sub(r"^[^\w]+|[^\w]+$", "", (matn or "").strip())
    return toza or None


class Natija(NamedTuple):
    """Tarjima natijasi."""
    ok: bool
    javob: str
    talaffuz_soz: Optional[str] = None    # tarjima qilingan so'z
    talaffuz_tili: Optional[str] = None   # 'uz' yoki 'en'


def tarjima_qil(matn, yonalish: str = DEFAULT_YONALISH):
    """Tarjima qiladi va Natija qaytaradi.

    talaffuz_soz — tarjima qilingan so'z, talaffuz_tili — 'uz' yoki 'en'.
    Xato bo'lsa faqat ok=False va javob to'ldiriladi.
    """
    if yonalish not in YONALISHLAR:
        yonalish = DEFAULT_YONALISH
    y = YONALISHLAR[yonalish]

    matn = apostrof_tuzat((matn or "").strip())

    if not matn_togri_mi(matn, yonalish):
        return Natija(False, y['xato'])

    kalit = matn.lower()
    natija = cache.ol(yonalish, kalit)
    yangi = natija is None
    if yangi:
        natija = _tarjima_ol(kalit, y)
        if natija is None:
            return Natija(False, TARJIMA_XATO)
        if y['target'] == 'uzbek':
            natija = kirill_lotin(natija)
        natija = natija.strip()

    bir_xil = natija.lower() == matn.lower()
    # Tarjima so'zning o'ziga teng bo'lsa: ma'lum inglizcha so'z bo'lsa (radio, taxi) to'g'ri,
    # aks holda so'z noto'g'ri deb hisoblanadi
    if bir_xil and not (yonalish == 'en_uz' and matn_inglizcha_mi(matn)):
        return Natija(False, y['xato'])

    if yangi:
        cache.saqla(yonalish, kalit, natija)  # faqat to'g'ri tarjimalar saqlanadi

    javob = f"{y['src_flag']} {matn} → {y['dst_flag']} {natija}"
    return Natija(True, javob, talaffuz_uchun_tozala(natija), y['tts_til'])


def javob_tayyorla(matn, yonalish: str = DEFAULT_YONALISH) -> str:
    """Faqat javob matnini qaytaradi."""
    return tarjima_qil(matn, yonalish).javob
