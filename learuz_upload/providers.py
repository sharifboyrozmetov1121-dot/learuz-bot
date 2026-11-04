from urllib.parse import quote
import requests
from deep_translator import GoogleTranslator

KODLAR = {'english': 'en', 'uzbek': 'uz'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
TIMEOUT = 5


class TooManyRequests(Exception):
    """Server so'rovlar limitiga tushganda."""


class SafeTranslator:
    """Barcha tarjimonlarni birlashtiruvchi va xatoliklarni oldini oluvchi sinf."""

    def __init__(self, source: str = 'english', target: str = 'uzbek'):
        self.source = source
        self.target = target
        self.src_code = KODLAR.get(source, source)
        self.dst_code = KODLAR.get(target, target)

    def translate(self, matn: str) -> str:
        # 1-urinish: deep-translator (GoogleTranslator)
        try:
            res = GoogleTranslator(source=self.src_code, target=self.dst_code).translate(matn)
            if res:
                return res
        except Exception:
            pass

        # 2-urinish: GoogleGtxTranslator
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            r = requests.get(
                url,
                params={'client': 'gtx', 'sl': self.src_code, 'tl': self.dst_code, 'dt': 't', 'q': matn},
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if r.status_code == 200:
                qismlar = [p[0] for p in r.json()[0] if p and p[0]]
                natija = ''.join(qismlar).strip()
                if natija:
                    return natija
        except Exception:
            pass

        # 3-urinish: LingvaTranslator serverlari
        serverlar = ("https://lingva.ml", "https://lingva.garudalinux.org")
        for server in serverlar:
            try:
                r = requests.get(
                    f"{server}/api/v1/{self.src_code}/{self.dst_code}/{quote(matn, safe='')}",
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )
                if r.status_code == 200:
                    natija = (r.json().get('translation') or '').strip()
                    if natija:
                        return natija
            except Exception:
                continue

        # Agar hamma tarjima xizmatlari ishlamasa, asl matnni qaytaradi (bot qotib qolmaydi)
        return matn
