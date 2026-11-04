import html
import logging
import re
import time
from typing import NamedTuple, Optional
import requests

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

# Tarjimonlar tartibi
TARJIMONLAR = (GoogleTranslator, GoogleGtxTranslator, LingvaTranslator, MyMemoryTranslator)

KIRILL_LOTIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'ъ': "'", 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'ў': "o'", 'қ': 'q', 'ғ': "g'", 'ҳ': 'h',
}


def kirill_lotin(matn: str) -> str:
    """O'zbekcha kirill yozuvini lotinga o'giradi."""
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
    """Turli apostroflarni oddiy ' ga almashtiradi."""
    return matn.translate(str.maketrans({'ʻ': "'", '’': "'", '‘': "'", '`': "'", 'ʼ': "'"}))


def _asoslar(soz: str):
    """So'zning mumkin bo'lgan asosiy shakllari."""
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
    """So'z inglizcha ekanini tekshiradi."""
    return any(asos in ENGLISH_WORDS for asos in _asoslar(soz.lower()))


def matn_inglizcha_mi(matn: str) -> bool:
    soz_lar = matn.replace('-', ' ').split()
    return bool(soz_lar) and all(inglizcha_mi(s) for s in soz_lar)


def matn_togri_mi(matn: str, yonalish: str = DEFAULT_YONALISH) -> bool:
    """Matn to'g'ri tuzilganligini tekshiradi."""
    matn = apostrof_tuzat(matn)
    if not re.fullmatch(r"[A-Za-z' -]+", matn):
        return False
    return any(ch.isalpha() for ch in matn)


def _tarjima_ol(matn: str, y: dict):
    """To'g'ridan-to'g'ri Google GTX va boshqa zaxiralar orqali tarjima qiladi."""
    url = "https://translate.googleapis.com/translate_a/single"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 1. Asosiy Google GTX so'rovi
    try:
        r = requests.get(
            url,
            params={'client': 'gtx', 'sl': y['source'][:2], 'tl': y['target'][:2], 'dt': 't', 'q': matn},
            headers=headers,
            timeout=5,
        )
        if r.status_code == 200:
            qismlar = [p[0] for p in r.json()[0] if p and p[0]]
            natija = ''.join(qismlar).strip()
            if natija:
                if y['target'] == 'uzbek':
                    natija = kirill_lotin(natija)
                return natija
    except Exception as e:
        logging.warning("Google GTX xatosi: %s", e)

    # 2. Zaxira tarjimonlar
    for dvigatel in TARJIMONLAR:
        try:
            res = dvigatel(source=y['source'], target=y['target']).translate(matn)
            if res:
                natija = apostrof_tuzat(html.unescape(res))
                if y['target'] == 'uzbek':
                    natija = kirill_lotin(natija)
                if natija.strip():
                    return natija.strip()
        except Exception:
            continue

    return None


def talaffuz_uchun_tozala(matn: str):
    """Talaffuz uchun matnni tozalaydi."""
    toza = re.sub(r"^[^\w]+|[^\w]+$", "", (matn or "").strip())
    return toza or None


class Natija(NamedTuple):
    ok: bool
    javob: str
    talaffuz_soz: Optional[str] = None
    talaffuz_tili: Optional[str] = None


def tarjima_qil(matn, yonalish: str = DEFAULT_YONALISH):
    """Tarjima qilish jarayonini boshqaradi."""
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
        natija = natija.strip()

    bir_xil = natija.lower() == matn.lower()
    if bir_xil and yonalish == 'en_uz' and not matn_inglizcha_mi(matn):
        return Natija(False, y['xato'])

    if yangi:
        cache.saqla(yonalish, kalit, natija)

    javob = f"{y['src_flag']} {matn} → {y['dst_flag']} {natija}"
    return Natija(True, javob, talaffuz_uchun_tozala(natija), y['tts_til'])


def javob_tayyorla(matn, yonalish: str = DEFAULT_YONALISH) -> str:
    return tarjima_qil(matn, yonalish).javob
