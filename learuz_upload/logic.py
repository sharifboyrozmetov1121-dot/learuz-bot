import html
import logging
import re
import requests
from typing import NamedTuple, Optional

import cache

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

TARJIMA_XATO = "Tarjima qilishda xatolik yuz berdi. Birozdan keyin qayta urinib ko'ring."

KIRILL_LOTIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'ъ': "'", 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'ў': "o'", 'қ': 'q', 'ғ': "g'", 'ҳ': 'h',
}

def kirill_lotin(matn: str) -> str:
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
    return matn.translate(str.maketrans({'ʻ': "'", '’': "'", '‘': "'", '`': "'", 'ʼ': "'"}))

def matn_togri_mi(matn: str, yonalish: str = DEFAULT_YONALISH) -> bool:
    matn = apostrof_tuzat(matn)
    if not re.fullmatch(r"[A-Za-z' -]+", matn):
        return False
    return any(ch.isalpha() for ch in matn)

def _tarjima_ol(matn: str, y: dict):
    """To'g'ridan-to'g'ri Google API orqali xatosiz tarjima qiladi."""
    sl = 'en' if y['source'] == 'english' else 'uz'
    tl = 'uz' if y['target'] == 'uzbek' else 'en'
    
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        r = requests.get(
            url,
            params={'client': 'gtx', 'sl': sl, 'tl': tl, 'dt': 't', 'q': matn},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5,
        )
        if r.status_code == 200:
            qismlar = [p[0] for p in r.json()[0] if p and p[0]]
            natija = ''.join(qismlar).strip()
            if natija:
                if tl == 'uz':
                    natija = kirill_lotin(natija)
                return natija
    except Exception as e:
        logging.warning("Tarjima xatosi: %s", e)
    
    return None

def talaffuz_uchun_tozala(matn: str):
    toza = re.sub(r"^[^\w]+|[^\w]+$", "", (matn or "").strip())
    return toza or None

class Natija(NamedTuple):
    ok: bool
    javob: str
    talaffuz_soz: Optional[str] = None
    talaffuz_tili: Optional[str] = None

def tarjima_qil(matn, yonalish: str = DEFAULT_YONALISH):
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

    if yangi:
        cache.saqla(yonalish, kalit, natija)

    javob = f"{y['src_flag']} {matn} → {y['dst_flag']} {natija}"
    return Natija(True, javob, talaffuz_uchun_tozala(natija), y['tts_til'])

def javob_tayyorla(matn, yonalish: str = DEFAULT_YONALISH) -> str:
    return tarjima_qil(matn, yonalish).javob
